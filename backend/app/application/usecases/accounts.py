"""
Casos de uso de las cuentas: iniciar y cerrar sesión, administrar los
dispositivos del usuario (ADR-0017) y sus juegos favoritos (ADR-0020).
"""

import hashlib
import secrets
import uuid
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Callable, List, Optional, cast

from app.domain.model.account import (
    MAX_DEVICES_PER_USER,
    MAX_FAVORITES_PER_USER,
    PC,
    Device,
    Favorite,
    InvalidDevice,
    InvalidFavorite,
    PcSpecs,
    User,
)
from app.domain.ports.account_repository import AccountRepository
from app.domain.ports.identity_provider import IdentityProvider

SESSION_DAYS = 30


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def hash_token(token: str) -> str:
    """Huella de un identificador de sesión: es lo único que se guarda."""

    return hashlib.sha256(token.encode()).hexdigest()


class DeviceNotFound(Exception):
    pass


class FavoriteNotFound(Exception):
    pass


class Sessions:
    """Inicio y cierre de sesión con un proveedor de identidad."""

    def __init__(
        self,
        accounts: AccountRepository,
        identity_provider: IdentityProvider,
        now: Callable[[], datetime] = _utc_now,
    ):
        self._accounts = accounts
        self._identity_provider = identity_provider
        self._now = now

    def begin(self) -> dict:
        """
        Prepara un inicio de sesión.

        `state` evita que otro sitio complete el inicio de sesión por la
        persona; `nonce` ata la respuesta del proveedor a este intento.
        """

        state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(32)

        return {
            "state": state,
            "nonce": nonce,
            "url": self._identity_provider.authorization_url(state, nonce),
        }

    def complete(self, code: str, nonce: str) -> dict:
        """Confirma la identidad, crea o actualiza la cuenta y abre la sesión."""

        identity = self._identity_provider.identify(code, nonce)
        user = self._accounts.save_user(identity)

        token = secrets.token_urlsafe(32)
        expires_at = self._now() + timedelta(days=SESSION_DAYS)

        self._accounts.create_session(hash_token(token), user.id, expires_at)

        return {"token": token, "expires_at": expires_at, "user": user}

    def current_user(self, token: Optional[str]) -> Optional[User]:
        if not token:
            return None

        return self._accounts.find_user_by_session(hash_token(token), self._now())

    def end(self, token: Optional[str]) -> None:
        if token:
            self._accounts.delete_session(hash_token(token))

    def delete_account(self, user: User) -> None:
        """Borra la cuenta y todo lo que DRIFT guardó de ella."""

        self._accounts.delete_user(user.id)


class Devices:
    """Los dispositivos que registra un usuario."""

    def __init__(
        self,
        accounts: AccountRepository,
        now: Callable[[], datetime] = _utc_now,
    ):
        self._accounts = accounts
        self._now = now

    def list(self, user: User) -> List[Device]:
        return self._accounts.list_devices(user.id)

    def add(self, user: User, name: str, kind: str, specs: Optional[dict]) -> Device:
        if len(self._accounts.list_devices(user.id)) >= MAX_DEVICES_PER_USER:
            raise InvalidDevice(
                f"Puedes registrar hasta {MAX_DEVICES_PER_USER} dispositivos."
            )

        device = self._build(str(uuid.uuid4()), user, name, kind, specs)
        self._accounts.save_device(device)

        return device

    def update(
        self,
        user: User,
        device_id: str,
        name: str,
        kind: str,
        specs: Optional[dict],
    ) -> Device:
        existing = next(
            (
                device
                for device in self._accounts.list_devices(user.id)
                if device.id == device_id
            ),
            None,
        )

        if existing is None:
            raise DeviceNotFound()

        device = self._build(device_id, user, name, kind, specs, existing.created_at)
        self._accounts.save_device(device)

        return device

    def remove(self, user: User, device_id: str) -> None:
        if not self._accounts.delete_device(user.id, device_id):
            raise DeviceNotFound()

    def _build(self, device_id, user, name, kind, specs, created_at=None) -> Device:
        clean_name = name.strip() if isinstance(name, str) else name

        return Device(
            id=device_id,
            user_id=user.id,
            name=clean_name,
            kind=kind,
            specs=_pc_specs(specs) if kind == PC else _no_specs(specs),
            created_at=created_at or self._now(),
        )


def _pc_specs(specs: Optional[dict]) -> Optional[PcSpecs]:
    if not specs:
        return None

    try:
        return PcSpecs(**specs)
    except TypeError as error:
        raise InvalidDevice("Los datos del PC no son válidos.") from error


def _no_specs(specs: Optional[dict]) -> None:
    if specs:
        raise InvalidDevice("Una consola no lleva componentes de PC.")

    return None


class Favorites:
    """Los juegos que un usuario guarda para seguirles el precio."""

    def __init__(
        self,
        accounts: AccountRepository,
        now: Callable[[], datetime] = _utc_now,
    ):
        self._accounts = accounts
        self._now = now

    def list(self, user: User) -> List[Favorite]:
        return self._accounts.list_favorites(user.id)

    def save(
        self,
        user: User,
        game_id: str,
        name: str,
        image: Optional[str] = None,
        price: Optional[float] = None,
        store: Optional[str] = None,
    ) -> Favorite:
        """
        Guarda el juego. Guardarlo de nuevo actualiza el precio de
        referencia y lo deja de primero; el precio objetivo se conserva.
        """

        existing = self._accounts.list_favorites(user.id)
        previous = next(
            (favorite for favorite in existing if favorite.game_id == game_id),
            None,
        )

        if (
            len(existing) >= MAX_FAVORITES_PER_USER
            and all(favorite.game_id != game_id for favorite in existing)
        ):
            raise InvalidFavorite(
                f"Puedes guardar hasta {MAX_FAVORITES_PER_USER} favoritos."
            )

        favorite = Favorite(
            user_id=user.id,
            game_id=game_id,
            name=name.strip() if isinstance(name, str) else name,
            image=image,
            price=price,
            store=store,
            saved_at=self._now(),
            target_price=previous.target_price if previous else None,
        )
        self._accounts.save_favorite(favorite)

        return favorite

    def set_target(
        self,
        user: User,
        game_id: str,
        target_price: Optional[float],
    ) -> Favorite:
        """Pone o quita el precio al que la persona quiere que le avisen."""

        existing = next(
            (
                favorite
                for favorite in self._accounts.list_favorites(user.id)
                if favorite.game_id == game_id
            ),
            None,
        )

        if existing is None:
            raise FavoriteNotFound()

        favorite = cast(Favorite, replace(existing, target_price=target_price))
        self._accounts.save_favorite(favorite)

        return favorite

    def remove(self, user: User, game_id: str) -> None:
        if not self._accounts.delete_favorite(user.id, game_id):
            raise FavoriteNotFound()
