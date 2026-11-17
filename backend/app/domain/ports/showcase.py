"""
Puertos de lo que la portada de DRIFT muestra además de la búsqueda: los
juegos del momento y las tiendas conectadas.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Tuple

# Categorías que la portada ofrece para explorar.
FEATURED_CATEGORIES = (
    "Acción",
    "Aventura",
    "Carreras",
    "Deportes",
    "RPG",
    "Estrategia",
)


@dataclass(frozen=True)
class FeaturedGame:
    """Un juego destacado: lo justo para mostrarlo y poder buscarlo."""

    id: str
    name: str
    image: str
    hero: str
    header: str


class FeaturedGamesSource(ABC):

    @abstractmethod
    def list(self, category: Optional[str]) -> List[FeaturedGame]:
        """
        Los juegos más vendidos del momento, de una categoría o de todas.

        Nunca lanza errores: la portada no puede fallar por esta lista. Si
        la fuente no responde entrega la última que obtuvo, o una vacía.
        """


# --- Explorar ------------------------------------------------------------------

# Géneros de la página «Explorar»: identificador de la URL -> nombre visible.
EXPLORE_GENRES = {
    "accion": "Acción",
    "aventura": "Aventura",
    "rol": "Rol",
    "estrategia": "Estrategia",
    "simulacion": "Simulación",
    "deportes": "Deportes",
    "carreras": "Carreras",
    "terror": "Terror",
    "casuales": "Casuales",
}

# Etiquetas con las que se afina un género.
EXPLORE_TAGS = {
    "un-jugador": "Un jugador",
    "multijugador": "Multijugador",
    "cooperativo": "Cooperativo",
    "mundo-abierto": "Mundo abierto",
    "buena-trama": "Buena trama",
    "indie": "Indie",
    "anime": "Anime",
    "pixelados": "Pixelados",
    "fantasia": "Fantasía",
    "ciencia-ficcion": "Ciencia ficción",
    "supervivencia": "Supervivencia",
    "por-turnos": "Estrategia por turnos",
}

# Orden de la lista y filtro de precio.
EXPLORE_SORTS = ("populares", "valorados", "precio-asc", "precio-desc")
EXPLORE_PRICES = ("todos", "gratis", "hasta-40000", "hasta-100000", "ofertas")

# Steam no pagina más allá de un número razonable de páginas.
MAX_EXPLORE_PAGE = 20


@dataclass(frozen=True)
class ExploreQuery:
    genre: Optional[str] = None
    tags: Tuple[str, ...] = ()
    sort: str = "populares"
    price: str = "todos"
    page: int = 1


@dataclass(frozen=True)
class ExploreGame:
    """Ficha de un juego para recorrer el catálogo, antes de comparar precios."""

    id: str
    name: str
    image: Optional[str] = None      # carátula vertical
    hero: Optional[str] = None       # panorámica
    header: Optional[str] = None     # horizontal pequeña
    capsule: Optional[str] = None    # horizontal grande
    description: Optional[str] = None
    tags: Tuple[str, ...] = ()
    release_date: Optional[date] = None
    developers: Tuple[str, ...] = ()
    review: Optional[str] = None
    review_percent: Optional[int] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    discount: int = 0
    is_free: bool = False


@dataclass(frozen=True)
class ExplorePage:
    items: List[ExploreGame] = field(default_factory=list)
    has_more: bool = False


class GameExplorer(ABC):

    @abstractmethod
    def explore(self, query: ExploreQuery) -> ExplorePage:
        """
        Una página del catálogo según el género, las etiquetas, el orden y
        el precio. Si la fuente no responde, eleva `ExternalSourceError`.
        """


class PcStoreDirectory(ABC):

    @abstractmethod
    def pc_stores(self) -> List[str]:
        """Nombres de las tiendas de PC que la fuente de precios cubre hoy."""
