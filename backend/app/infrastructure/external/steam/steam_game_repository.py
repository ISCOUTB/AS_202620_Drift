import time
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, List, Optional

import httpx  # noqa: F401

from app.domain.model.game import Game
from app.domain.ports.game_repository import GameRepository
from app.infrastructure.external.resilient_http import (
    ExternalSourceError,
    RetryPolicy,
    TimeBudget,
    get_json,
)
from app.infrastructure.external.single_flight_cache import SingleFlightCache
from app.infrastructure.game_copy import copy_games

SOURCE_NAME = "Steam"
DEFAULT_TOTAL_DEADLINE_SECONDS = 5.0

class SteamGameRepository(GameRepository):
    def __init__(
        self,
        policy: Optional[RetryPolicy] = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ):
        self._policy = policy or RetryPolicy.from_env(
        "DRIFT_STEAM",
        default_total_deadline_seconds=DEFAULT_TOTAL_DEADLINE_SECONDS,
        )
        self._sleep = sleep
        self._clock = clock
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

    def _get_json(
        self,
        url: str,
        params: dict,
        budget: Optional[TimeBudget] = None,
    ):
        return get_json(
            url,
            params,
            source=SOURCE_NAME,
            policy=self._policy,
            sleep=self._sleep,
            budget=budget,
        )


    def _search_steam(self, query: str) -> List[Game]:
        budget = TimeBudget.from_policy(self._policy, self._clock)

        data = self._get_json(
            "https://store.steampowered.com/api/storesearch/",
            {
                "term": query,
                "cc": "co",
                "l": "spanish",
            },
            budget=budget,
        )

        if not isinstance(data, dict) or not isinstance(
            data.get("items", []), list
        ):
            raise ExternalSourceError(SOURCE_NAME, "invalid_response")

        raw_items = data.get("items", [])[:5]
        items = [item for item in raw_items if self._is_valid_item(item)]

        if not items:
            if raw_items:
                raise ExternalSourceError(SOURCE_NAME, "invalid_response")
            return []

        with ThreadPoolExecutor(max_workers=min(5, len(items))) as executor:
            games = list(
                executor.map(
                    lambda item: self._get_game_details(item, budget),
                    items,
                )
            )

        return games


    @staticmethod
    def _is_valid_item(item) -> bool:
        return (
            isinstance(item, dict)
            and isinstance(item.get("id"), int)
            and not isinstance(item.get("id"), bool)
            and isinstance(item.get("name"), str)
        )

    def _get_game_details(
        self,
        item: dict,
        budget: Optional[TimeBudget] = None,
    ) -> Game:
        app_id = item["id"]

        details_data = self._get_json(
            "https://store.steampowered.com/api/appdetails",
            {
                "appids": app_id,
                "cc": "co",
                "l": "spanish",
            },
            budget=budget,
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
