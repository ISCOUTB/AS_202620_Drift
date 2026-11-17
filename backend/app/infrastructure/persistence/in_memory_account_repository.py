import uuid
from datetime import datetime
from threading import Lock
from typing import List, Optional

from app.domain.model.account import Device, Favorite, GoogleIdentity, User
from app.domain.ports.account_repository import AccountRepository


class InMemoryAccountRepository(AccountRepository):
    """
    Cuentas en la memoria del proceso: solo para desarrollo y pruebas.

    Todo se pierde al reiniciar. Se usa cuando no hay `DRIFT_DATABASE_URL`;
    en el laboratorio las cuentas viven en PostgreSQL.
    """

    def __init__(self):
        self._users = {}
        self._sessions = {}
        self._devices = {}
        self._favorites = {}
        self._lock = Lock()

    def save_user(self, identity: GoogleIdentity) -> User:
        with self._lock:
            existing = next(
                (
                    user
                    for user in self._users.values()
                    if user.google_subject == identity.subject
                ),
                None,
            )

            user = User(
                id=existing.id if existing else str(uuid.uuid4()),
                google_subject=identity.subject,
                email=identity.email,
                name=identity.name,
                picture=identity.picture,
            )
            self._users[user.id] = user

            return user

    def delete_user(self, user_id: str) -> None:
        with self._lock:
            self._users.pop(user_id, None)
            self._sessions = {
                token: session
                for token, session in self._sessions.items()
                if session[0] != user_id
            }
            self._devices = {
                key: device
                for key, device in self._devices.items()
                if device.user_id != user_id
            }
            self._favorites = {
                key: favorite
                for key, favorite in self._favorites.items()
                if favorite.user_id != user_id
            }

    def create_session(
        self,
        token_hash: str,
        user_id: str,
        expires_at: datetime,
    ) -> None:
        with self._lock:
            self._sessions[token_hash] = (user_id, expires_at)

    def find_user_by_session(
        self,
        token_hash: str,
        now: datetime,
    ) -> Optional[User]:
        with self._lock:
            session = self._sessions.get(token_hash)

            if session is None:
                return None

            user_id, expires_at = session

            if expires_at <= now:
                del self._sessions[token_hash]
                return None

            return self._users.get(user_id)

    def delete_session(self, token_hash: str) -> None:
        with self._lock:
            self._sessions.pop(token_hash, None)

    def list_devices(self, user_id: str) -> List[Device]:
        with self._lock:
            devices = [
                device
                for device in self._devices.values()
                if device.user_id == user_id
            ]

        return sorted(devices, key=lambda device: (device.created_at, device.id))

    def save_device(self, device: Device) -> None:
        with self._lock:
            self._devices[(device.user_id, device.id)] = device

    def delete_device(self, user_id: str, device_id: str) -> bool:
        with self._lock:
            return self._devices.pop((user_id, device_id), None) is not None

    def list_favorites(self, user_id: str) -> List[Favorite]:
        with self._lock:
            favorites = [
                favorite
                for favorite in self._favorites.values()
                if favorite.user_id == user_id
            ]

        return sorted(
            favorites,
            key=lambda favorite: (favorite.saved_at, favorite.game_id),
            reverse=True,
        )

    def save_favorite(self, favorite: Favorite) -> None:
        with self._lock:
            self._favorites[(favorite.user_id, favorite.game_id)] = favorite

    def delete_favorite(self, user_id: str, game_id: str) -> bool:
        with self._lock:
            return self._favorites.pop((user_id, game_id), None) is not None
