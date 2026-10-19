import time
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, List, Optional

import httpx  # noqa: F401  los tests parchean steam_game_repository.httpx.get

from app.domain.model.game import Game
from app.domain.ports.game_repository import GameRepository
from app.infrastructure.external.resilient_http import (
    ExternalSourceError,
    RetryPolicy,
    get_json,
)
from app.infrastructure.external.single_flight_cache import SingleFlightCache
from app.infrastructure.game_copy import copy_games

SOURCE_NAME = "Steam"


class SteamGameRepository(GameRepository):
    def __init__(
        self,
        policy: Optional[RetryPolicy] = None,
        sleep: Callable[[float], None] = time.sleep,
    ):
        # Variables DRIFT_STEAM_*; ver arc42 §7 y ADR-0009.
        self._policy = policy or RetryPolicy.from_env("DRIFT_STEAM")
        self._sleep = sleep
        self._cache = SingleFlightCache(ttl_seconds=60)

    def search(self, query: str) -> List[Game]:
        cache_key = query.strip().lower()

        # Evita que muchos usuarios simultáneos repitan exactamente las
        # mismas consultas a Steam, sin que búsquedas distintas se esperen.
        games = self._cache.get_or_load(
            cache_key,
            lambda: self._search_steam(query),
        )

        return copy_games(games)

    def _get_json(self, url: str, params: dict):
        return get_json(
            url,
            params,
            source=SOURCE_NAME,
            policy=self._policy,
            sleep=self._sleep,
        )

    def _search_steam(self, query: str) -> List[Game]:
        data = self._get_json(
            "https://store.steampowered.com/api/storesearch/",
            {
                "term": query,
                "cc": "co",
                "l": "spanish",
            },
        )

        if not isinstance(data, dict) or not isinstance(
            data.get("items", []), list
        ):
            raise ExternalSourceError(SOURCE_NAME, "invalid_response")

        # Se limita a cinco resultados: evita pedir decenas de detalles
        # innecesarios a Steam en una sola búsqueda.
        raw_items = data.get("items", [])[:5]
        items = [item for item in raw_items if self._is_valid_item(item)]

        if not items:
            # Sin ítems es una búsqueda sin resultados; ítems presentes pero
            # todos malformados es una respuesta inválida, no «sin resultados».
            if raw_items:
                raise ExternalSourceError(SOURCE_NAME, "invalid_response")

            return []

        # Los detalles se consultan en paralelo, no uno después de otro.
        with ThreadPoolExecutor(max_workers=min(5, len(items))) as executor:
            games = list(executor.map(self._get_game_details, items))

        return games

    @staticmethod
    def _is_valid_item(item) -> bool:
        return (
            isinstance(item, dict)
            and isinstance(item.get("id"), int)
            and not isinstance(item.get("id"), bool)
            and isinstance(item.get("name"), str)
        )

    def _get_game_details(self, item: dict) -> Game:
        app_id = item["id"]

        details_data = self._get_json(
            "https://store.steampowered.com/api/appdetails",
            {
                "appids": app_id,
                "cc": "co",
                "l": "spanish",
            },
        )

        if not isinstance(details_data, dict):
            raise ExternalSourceError(SOURCE_NAME, "invalid_response")

        entry = details_data.get(str(app_id), {})
        game_data = entry.get("data", {}) if isinstance(entry, dict) else {}

        if not isinstance(game_data, dict):
            game_data = {}

        prices = {}
        price_overview = game_data.get("price_overview")

        # Un juego sin precio (gratuito, no lanzado o no vendido en la
        # región) es un dato válido; un importe no numérico se descarta.
        if isinstance(price_overview, dict) and price_overview:
            final_price = price_overview.get("final", 0)

            if isinstance(final_price, (int, float)) and not isinstance(
                final_price, bool
            ):
                prices["Steam"] = final_price / 100

        return Game(
            id=app_id,
            name=item["name"],
            prices=prices,
            image=game_data.get("header_image"),
            links=(
                {"Steam": f"https://store.steampowered.com/app/{app_id}/"}
                if prices
                else {}
            ),
        )