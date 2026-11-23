from dataclasses import dataclass, field
from typing import Optional, Tuple


@dataclass(frozen=True)
class Trailer:
    """
    Tráiler de un juego. La tienda lo entrega como transmisión adaptable:
    `hls` (lista .m3u8) y, si existe, `dash` (manifiesto .mpd). El navegador
    lo descarga directamente de la tienda, no a través de DRIFT.
    """

    name: str
    thumbnail: str
    hls: str
    dash: Optional[str] = None


@dataclass(frozen=True)
class Screenshot:
    thumbnail: str
    full: str


@dataclass(frozen=True)
class GameDetails:
    """Ficha de un juego para su página: lo que se ve antes de los precios."""

    game_id: str
    name: str
    description: Optional[str]
    header_image: Optional[str]
    background_image: Optional[str]
    release_date: Optional[str]
    coming_soon: bool
    developers: Tuple[str, ...] = field(default_factory=tuple)
    publishers: Tuple[str, ...] = field(default_factory=tuple)
    genres: Tuple[str, ...] = field(default_factory=tuple)
    trailers: Tuple[Trailer, ...] = field(default_factory=tuple)
    screenshots: Tuple[Screenshot, ...] = field(default_factory=tuple)
    website: Optional[str] = None
    source: str = "Steam"
