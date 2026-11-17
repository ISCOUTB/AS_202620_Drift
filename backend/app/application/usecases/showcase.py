from typing import List, Optional

from app.domain.ports.showcase import (
    EXPLORE_GENRES,
    EXPLORE_PRICES,
    EXPLORE_SORTS,
    EXPLORE_TAGS,
    FEATURED_CATEGORIES,
    MAX_EXPLORE_PAGE,
    ExplorePage,
    ExploreQuery,
    FeaturedGame,
    FeaturedGamesSource,
    GameExplorer,
    PcStoreDirectory,
)
from app.domain.services.platforms import PC, PLAYSTATION, XBOX

# Tiendas que DRIFT consulta directamente, sin intermediarios.
DIRECT_STORES = (
    {"name": "Steam", "platform": PC, "source": "Steam"},
    {"name": "PlayStation", "platform": PLAYSTATION, "source": "PlayStation"},
    {"name": "Xbox", "platform": XBOX, "source": "Xbox"},
    {"name": "Microsoft Store", "platform": PC, "source": "Xbox"},
)


class ListFeaturedGames:
    """Juegos del momento para la portada; cambian con las ventas de la tienda."""

    def __init__(self, source: FeaturedGamesSource):
        self.source = source

    def execute(self, category: Optional[str] = None) -> List[FeaturedGame]:
        if category is not None and category not in FEATURED_CATEGORIES:
            raise ValueError("categoría desconocida")

        return self.source.list(category)


class ListStores:
    """Todas las tiendas cuyos precios compara DRIFT."""

    def __init__(self, directory: PcStoreDirectory, directory_source: str):
        self.directory = directory
        self.directory_source = directory_source

    def execute(self) -> dict:
        stores = [dict(store) for store in DIRECT_STORES]
        known = {store["name"] for store in stores}
        complete = True

        try:
            names = self.directory.pc_stores()
        except Exception:  # noqa: BLE001  la lista nunca tumba la portada
            names = []
            complete = False

        for name in sorted(set(names), key=str.casefold):
            if name not in known:
                stores.append(
                    {"name": name, "platform": PC, "source": self.directory_source}
                )

        # `complete` en falso: la fuente de las tiendas de PC no respondió y
        # solo se listan las que DRIFT consulta directamente.
        return {"complete": complete, "items": stores}


class ExploreGames:
    """Una página del catálogo para la página «Explorar»."""

    def __init__(self, explorer: GameExplorer):
        self.explorer = explorer

    def execute(self, query: ExploreQuery) -> ExplorePage:
        if query.genre is not None and query.genre not in EXPLORE_GENRES:
            raise ValueError("género desconocido")

        if any(tag not in EXPLORE_TAGS for tag in query.tags):
            raise ValueError("etiqueta desconocida")

        if query.sort not in EXPLORE_SORTS or query.price not in EXPLORE_PRICES:
            raise ValueError("orden o precio desconocido")

        if not 1 <= query.page <= MAX_EXPLORE_PAGE:
            raise ValueError("página fuera de rango")

        # Sin etiquetas repetidas: la misma página no se pide dos veces.
        tags = tuple(dict.fromkeys(query.tags))

        return self.explorer.explore(
            ExploreQuery(
                genre=query.genre,
                tags=tags,
                sort=query.sort,
                price=query.price,
                page=query.page,
            )
        )
