"""
Catálogo de Steam para la página «Explorar»: una página de juegos según el
género, las etiquetas, el orden y el precio, con la ficha de cada uno.

Son dos llamadas por página: la búsqueda pública de la tienda (qué juegos y en
qué orden) y `GetItems` (la ficha de todos a la vez). Cada página se guarda 15
minutos: varias personas que recorren el mismo género no repiten llamadas.
"""

import re
import time
from typing import Callable, List, Optional

import httpx  # noqa: F401  los tests parchean steam_game_explorer.httpx.get

from app.domain.ports.showcase import (
    ExploreGame,
    ExplorePage,
    ExploreQuery,
    GameExplorer,
)
from app.infrastructure.external.resilient_http import (
    ExternalSourceError,
    RetryPolicy,
    TimeBudget,
    get_json,
)
from app.infrastructure.external.single_flight_cache import SingleFlightCache
from app.infrastructure.external.steam.steam_store_items import SteamStoreItems

SOURCE_NAME = "Steam"

SEARCH_URL = "https://store.steampowered.com/search/results/"
IMAGES = "https://cdn.cloudflare.steamstatic.com/steam/apps"

# Una página de la búsqueda de Steam en JSON trae 25 juegos.
PAGE_SIZE = 25
CACHE_SECONDS = 15 * 60

# Etiquetas de la tienda de Steam (IStoreService/GetTagList).
GENRE_TAGS = {
    "accion": 19,
    "aventura": 21,
    "rol": 122,
    "estrategia": 9,
    "simulacion": 599,
    "deportes": 701,
    "carreras": 699,
    "terror": 1667,
    "casuales": 597,
}

EXTRA_TAGS = {
    "un-jugador": 4182,
    "multijugador": 3859,
    "cooperativo": 1685,
    "mundo-abierto": 1695,
    "buena-trama": 1742,
    "indie": 492,
    "anime": 4085,
    "pixelados": 3964,
    "fantasia": 1684,
    "ciencia-ficcion": 3942,
    "supervivencia": 1662,
    "por-turnos": 1741,
}

SORTS = {
    "populares": {"filter": "topsellers"},
    "valorados": {"sort_by": "Reviews_DESC"},
    "precio-asc": {"filter": "topsellers", "sort_by": "Price_ASC"},
    "precio-desc": {"filter": "topsellers", "sort_by": "Price_DESC"},
}

# Precios en pesos colombianos (la búsqueda se hace con cc=co).
PRICES = {
    "todos": {},
    "gratis": {"maxprice": "free"},
    "hasta-40000": {"maxprice": 40000},
    "hasta-100000": {"maxprice": 100000},
    "ofertas": {"specials": 1},
}

_APP_ID = re.compile(r"/apps/(\d+)/")


class SteamGameExplorer(GameExplorer):

    def __init__(
        self,
        store_items: SteamStoreItems,
        policy: Optional[RetryPolicy] = None,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self._store_items = store_items
        self._policy = policy or RetryPolicy(
            timeout_seconds=3.0,
            max_attempts=2,
            total_deadline_seconds=4.0,
        )
        self._sleep = sleep
        self._cache = SingleFlightCache(ttl_seconds=CACHE_SECONDS)

    def explore(self, query: ExploreQuery) -> ExplorePage:
        key = (query.genre, tuple(sorted(query.tags)), query.sort, query.price, query.page)

        return self._cache.get_or_load(key, lambda: self._load(query))

    def _load(self, query: ExploreQuery) -> ExplorePage:
        found = self._search(query)

        try:
            details = self._store_items.details(app_id for app_id, _ in found)
        except ExternalSourceError:
            # Sin fichas, la lista sigue: nombre e imágenes armadas con el id.
            details = {}

        items = [details.get(app_id) or _minimal(app_id, name) for app_id, name in found]

        return ExplorePage(items=items, has_more=len(found) >= PAGE_SIZE)

    def _search(self, query: ExploreQuery) -> List[tuple]:
        params = {
            "json": 1,
            # 998: solo juegos, sin aplicaciones, bandas sonoras ni hardware.
            "category1": 998,
            "cc": "co",
            "l": "spanish",
            "page": query.page,
        }

        tags = [GENRE_TAGS[query.genre]] if query.genre else []
        tags += [EXTRA_TAGS[tag] for tag in query.tags]

        if tags:
            params["tags"] = ",".join(str(tag) for tag in tags)

        params.update(SORTS[query.sort])
        params.update(PRICES[query.price])

        answer = get_json(
            SEARCH_URL,
            params,
            source=SOURCE_NAME,
            policy=self._policy,
            sleep=self._sleep,
            budget=TimeBudget.from_policy(self._policy),
        )

        items = answer.get("items") if isinstance(answer, dict) else None

        if not isinstance(items, list):
            raise ExternalSourceError(SOURCE_NAME, "invalid_response")

        found = {}

        for item in items:
            if not isinstance(item, dict):
                continue

            name = item.get("name")
            logo = item.get("logo")
            match = _APP_ID.search(logo) if isinstance(logo, str) else None

            if match and isinstance(name, str) and name.strip():
                found.setdefault(match.group(1), name.strip()[:120])

        return list(found.items())


def _minimal(app_id: str, name: str) -> ExploreGame:
    return ExploreGame(
        id=app_id,
        name=name,
        image=f"{IMAGES}/{app_id}/library_600x900.jpg",
        hero=f"{IMAGES}/{app_id}/library_hero.jpg",
        header=f"{IMAGES}/{app_id}/header.jpg",
    )
