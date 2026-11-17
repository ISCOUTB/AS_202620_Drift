import logging
import re
import time
from threading import Lock
from typing import Callable, List, Optional

import httpx  # noqa: F401  los tests parchean steam_featured_games_source.httpx.get

from app.domain.ports.showcase import FeaturedGame, FeaturedGamesSource
from app.infrastructure.external.resilient_http import (
    ExternalSourceError,
    RetryPolicy,
    TimeBudget,
    get_json,
)
from app.infrastructure.external.single_flight_cache import SingleFlightCache
from app.infrastructure.observability import log_event

logger = logging.getLogger("drift")

SOURCE_NAME = "Steam"

SEARCH_URL = "https://store.steampowered.com/search/results/"
IMAGES = "https://cdn.cloudflare.steamstatic.com/steam/apps"

# Etiquetas de la tienda de Steam para cada categoría de la portada.
CATEGORY_TAGS = {
    "Acción": 19,
    "Aventura": 21,
    "Carreras": 699,
    "Deportes": 701,
    "RPG": 122,
    "Estrategia": 9,
}

MAX_GAMES = 24

# Los más vendidos cambian a lo largo del día, no de un minuto a otro.
CACHE_SECONDS = 60 * 60

_APP_ID = re.compile(r"/apps/(\d+)/")


class SteamFeaturedGamesSource(FeaturedGamesSource):
    """
    Los juegos más vendidos de Steam en Colombia, generales o por etiqueta.

    Es la misma búsqueda pública de la tienda, pedida en JSON. La lista se
    guarda una hora; si Steam no responde se entrega la última obtenida y,
    si nunca hubo una, una lista vacía: la portada tiene su propia lista de
    respaldo.
    """

    def __init__(
        self,
        policy: Optional[RetryPolicy] = None,
        sleep: Callable[[float], None] = time.sleep,
        store_items=None,
    ):
        # `SteamStoreItems`: rutas reales de las imágenes. Sin él, las rutas
        # se arman con el identificador, que fallan en los juegos recientes.
        self._store_items = store_items
        self._policy = policy or RetryPolicy(
            timeout_seconds=3.0,
            max_attempts=2,
            total_deadline_seconds=4.0,
        )
        self._sleep = sleep
        self._cache = SingleFlightCache(ttl_seconds=CACHE_SECONDS)
        self._last_good = {}
        self._lock = Lock()

    def list(self, category: Optional[str]) -> List[FeaturedGame]:
        try:
            games = self._cache.get_or_load(
                category,
                lambda: self._fetch(category),
            )
        except ExternalSourceError as error:
            log_event(
                logger,
                "featured_games_unavailable",
                reason=error.reason,
            )

            with self._lock:
                return list(self._last_good.get(category, []))

        with self._lock:
            self._last_good[category] = games

        return list(games)

    def _fetch(self, category: Optional[str]) -> List[FeaturedGame]:
        params = {
            "json": 1,
            "filter": "topsellers",
            # 998: solo juegos, sin aplicaciones, bandas sonoras ni hardware.
            "category1": 998,
            "cc": "co",
            "l": "spanish",
            "count": 40,
        }

        if category is not None:
            params["tags"] = CATEGORY_TAGS[category]

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

        games = {}

        for item in items:
            game = _featured(item)

            if game is not None:
                games.setdefault(game.id, game)

            if len(games) >= MAX_GAMES:
                break

        # Una lista vacía no reemplaza a la anterior: se trata como fallo.
        if not games:
            raise ExternalSourceError(SOURCE_NAME, "invalid_response")

        return self._with_real_images(list(games.values()))

    def _with_real_images(self, games: List[FeaturedGame]) -> List[FeaturedGame]:
        """Cambia las rutas armadas por las que Steam entrega para cada juego."""

        if self._store_items is None:
            return games

        try:
            details = self._store_items.details(game.id for game in games)
        except ExternalSourceError as error:
            log_event(
                logger,
                "featured_images_unavailable",
                reason=error.reason,
            )
            return games

        return [
            FeaturedGame(
                id=game.id,
                name=game.name,
                image=details[game.id].image or game.image,
                hero=details[game.id].hero or game.hero,
                header=details[game.id].header or game.header,
            )
            if game.id in details
            else game
            for game in games
        ]


def _featured(item) -> Optional[FeaturedGame]:
    if not isinstance(item, dict):
        return None

    name = item.get("name")
    logo = item.get("logo")

    if not isinstance(name, str) or not name.strip() or not isinstance(logo, str):
        return None

    match = _APP_ID.search(logo)

    if match is None:
        return None

    app_id = match.group(1)

    return FeaturedGame(
        id=app_id,
        name=name.strip()[:120],
        image=f"{IMAGES}/{app_id}/library_600x900.jpg",
        hero=f"{IMAGES}/{app_id}/library_hero.jpg",
        header=f"{IMAGES}/{app_id}/header.jpg",
    )
