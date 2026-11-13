from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from app.domain.model.account import Device, Favorite, GoogleIdentity, User


class AccountRepository(ABC):
    """
    Cuentas, sesiones, dispositivos (ADR-0017) y favoritos (ADR-0020).

    Son datos propios de DRIFT: ninguna tienda puede reponerlos. Por eso, a
    diferencia de la copia de respaldo de las fuentes, un fallo de este
    almacén sí se propaga: es peor fingir que algo se guardó.

    De una sesión solo se guarda la huella (hash) de su identificador.
    """

    @abstractmethod
    def save_user(self, identity: GoogleIdentity) -> User:
        """Crea la cuenta o actualiza su correo, nombre y foto."""

    @abstractmethod
    def delete_user(self, user_id: str) -> None:
        """Borra la cuenta con sus sesiones, dispositivos y favoritos."""

    @abstractmethod
    def create_session(
        self,
        token_hash: str,
        user_id: str,
        expires_at: datetime,
    ) -> None:
        pass

    @abstractmethod
    def find_user_by_session(
        self,
        token_hash: str,
        now: datetime,
    ) -> Optional[User]:
        """`None` si la sesión no existe o ya venció."""

    @abstractmethod
    def delete_session(self, token_hash: str) -> None:
        pass

    @abstractmethod
    def list_devices(self, user_id: str) -> List[Device]:
        pass

    @abstractmethod
    def save_device(self, device: Device) -> None:
        """Crea el dispositivo o reemplaza el que tiene ese `id` y dueño."""

    @abstractmethod
    def delete_device(self, user_id: str, device_id: str) -> bool:
        """`False` si ese usuario no tiene un dispositivo con ese `id`."""

    @abstractmethod
    def list_favorites(self, user_id: str) -> List[Favorite]:
        """Del más reciente al más antiguo."""

    @abstractmethod
    def save_favorite(self, favorite: Favorite) -> None:
        """Guarda el favorito o reemplaza el de ese usuario y ese juego."""

    @abstractmethod
    def delete_favorite(self, user_id: str, game_id: str) -> bool:
        """`False` si ese usuario no tenía ese juego en favoritos."""
