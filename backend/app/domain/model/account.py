import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

PC = "pc"
PLAYSTATION = "playstation"
XBOX = "xbox"

DEVICE_KINDS = (PC, PLAYSTATION, XBOX)

MAX_DEVICES_PER_USER = 10
MAX_NAME_LENGTH = 40
MAX_COMPONENT_LENGTH = 120


MAX_FAVORITES_PER_USER = 100
MAX_GAME_NAME_LENGTH = 200
MAX_IMAGE_LENGTH = 500

_GAME_ID = re.compile(r"^[A-Za-z0-9_-]{1,80}$")
# Dirección https sin espacios ni caracteres que puedan cerrar un atributo
# o una regla de estilo donde la página la use.
_IMAGE_URL = re.compile(r"^https://[^\s\"'()<>\\]+$")


class InvalidFavorite(ValueError):
    """El favorito no cumple las reglas; el mensaje se le muestra al usuario."""


class InvalidDevice(ValueError):
    """El dispositivo no cumple las reglas; el mensaje se le muestra al usuario."""


@dataclass(frozen=True)
class GoogleIdentity:
    """Lo único que DRIFT toma de la cuenta de Google de una persona."""

    subject: str
    email: str
    name: str
    picture: Optional[str] = None


@dataclass(frozen=True)
class User:
    id: str
    google_subject: str
    email: str
    name: str
    picture: Optional[str] = None


@dataclass(frozen=True)
class PcSpecs:
    """Equipo de un PC, con los mismos datos que usa la compatibilidad."""

    ram_gb: int
    gpu_score: int
    gpu_name: Optional[str] = None
    cpu_name: Optional[str] = None
    cpu_score: Optional[int] = None
    storage_gb: Optional[int] = None

    def __post_init__(self):
        _positive(self.ram_gb, "la memoria RAM", maximum=1024)
        _positive(self.gpu_score, "la tarjeta gráfica")

        if self.cpu_score is not None:
            _positive(self.cpu_score, "el procesador")

        if self.storage_gb is not None:
            _positive(self.storage_gb, "el espacio libre", maximum=100_000)

        for text in (self.gpu_name, self.cpu_name):
            if text is not None and (
                not isinstance(text, str) or len(text) > MAX_COMPONENT_LENGTH
            ):
                raise InvalidDevice("El nombre de un componente es demasiado largo.")


@dataclass(frozen=True)
class Device:
    """
    Un dispositivo del usuario (ficha del problema: «registrar los
    dispositivos del usuario»). Un PC lleva su equipo; una consola no
    necesita más que su nombre.
    """

    id: str
    user_id: str
    name: str
    kind: str
    specs: Optional[PcSpecs] = None
    created_at: Optional[datetime] = field(default=None, compare=False)

    def __post_init__(self):
        if self.kind not in DEVICE_KINDS:
            raise InvalidDevice("El tipo de dispositivo no es válido.")

        if (
            not isinstance(self.name, str)
            or not self.name.strip()
            or len(self.name) > MAX_NAME_LENGTH
        ):
            raise InvalidDevice(
                f"El nombre debe tener entre 1 y {MAX_NAME_LENGTH} caracteres."
            )

        if self.kind == PC and self.specs is None:
            raise InvalidDevice("Un PC necesita su memoria RAM y su tarjeta gráfica.")

        if self.kind != PC and self.specs is not None:
            raise InvalidDevice("Una consola no lleva componentes de PC.")


MAX_STORE_LENGTH = 60
MAX_AMOUNT = 1_000_000_000


def _valid_amount(value, allow_zero: bool) -> bool:
    """Un precio en pesos: número (no booleano), hasta mil millones."""

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False

    lowest_ok = value >= 0 if allow_zero else value > 0

    return lowest_ok and value <= MAX_AMOUNT


def _valid_text(value, max_length: int) -> bool:
    return isinstance(value, str) and bool(value.strip()) and len(value) <= max_length


def _valid_image(value) -> bool:
    return (
        isinstance(value, str)
        and len(value) <= MAX_IMAGE_LENGTH
        and bool(_IMAGE_URL.match(value))
    )


def _positive(value, label: str, maximum: Optional[int] = None) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise InvalidDevice(f"Ingresa un valor válido para {label}.")

    if maximum is not None and value > maximum:
        raise InvalidDevice(f"El valor de {label} es demasiado grande.")


@dataclass(frozen=True)
class Favorite:
    """
    Un juego que el usuario guardó para seguirle el precio.

    `price` y `store` son el mejor precio que la persona tenía en pantalla
    al guardarlo: sirven para decirle después si subió o bajó. `None` si el
    juego no tenía precio en ese momento.

    `target_price` es el precio al que la persona quiere que le avisen
    (ADR-0021); `None` si no puso uno.
    """

    user_id: str
    game_id: str
    name: str
    image: Optional[str] = None
    price: Optional[float] = None
    store: Optional[str] = None
    saved_at: Optional[datetime] = field(default=None, compare=False)
    target_price: Optional[float] = None

    def __post_init__(self):
        if not isinstance(self.game_id, str) or not _GAME_ID.match(self.game_id):
            raise InvalidFavorite("El juego no es válido.")

        if self.target_price is not None and not _valid_amount(
            self.target_price, allow_zero=False
        ):
            raise InvalidFavorite("Ingresa un precio objetivo mayor que cero.")

        if not _valid_text(self.name, MAX_GAME_NAME_LENGTH):
            raise InvalidFavorite("El nombre del juego no es válido.")

        if self.image is not None and not _valid_image(self.image):
            raise InvalidFavorite("La imagen del juego no es válida.")

        if (self.price is None) != (self.store is None):
            raise InvalidFavorite("El precio necesita su tienda.")

        if self.price is not None and not _valid_amount(self.price, allow_zero=True):
            raise InvalidFavorite("El precio no es válido.")

        if self.store is not None and not _valid_text(self.store, MAX_STORE_LENGTH):
            raise InvalidFavorite("La tienda no es válida.")
