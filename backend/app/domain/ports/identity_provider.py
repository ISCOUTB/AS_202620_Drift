from abc import ABC, abstractmethod

from app.domain.model.account import GoogleIdentity


class IdentityRejected(Exception):
    """El proveedor no confirmó la identidad (código inválido, datos que no cuadran)."""


class IdentityProviderUnavailable(Exception):
    """El proveedor de identidad no respondió."""


class IdentityProvider(ABC):
    """Quien confirma quién es la persona. DRIFT no guarda contraseñas."""

    @abstractmethod
    def authorization_url(self, state: str, nonce: str) -> str:
        """Dirección a la que se envía a la persona para que inicie sesión."""

    @abstractmethod
    def identify(self, code: str, nonce: str) -> GoogleIdentity:
        """Cambia el código que devolvió el proveedor por la identidad."""
