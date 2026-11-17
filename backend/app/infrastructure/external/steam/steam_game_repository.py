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
DEFAULT_TOTAL_DEADLINE_SECONDS = 4.0

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
        items = self._unique_by_id(
            item for item in raw_items if self._is_valid_item(item)
        )

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


    def price_in_colombia(self, app_id: str) -> Optional[tuple]:
        """
        (precio normal, precio de hoy, descuento) de un juego en pesos.

        Lo usa el historial de precios para poner a Steam en pesos de
        Colombia. Devuelve `None` si Steam no responde o el juego no tiene
        precio: el historial sigue sin la serie de Steam.
        """

        try:
            details = self._get_json(
                "https://store.steampowered.com/api/appdetails",
                {"appids": app_id, "cc": "co", "filters": "price_overview"},
                budget=TimeBudget.from_policy(self._policy, self._clock),
            )
        except ExternalSourceError:
            return None

        entry = details.get(str(app_id)) if isinstance(details, dict) else None
        data = entry.get("data") if isinstance(entry, dict) else None
        price = data.get("price_overview") if isinstance(data, dict) else None

        if not isinstance(price, dict):
            return None

        initial = price.get("initial")
        final = price.get("final")
        discount = price.get("discount_percent")

        for value in (initial, final):
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or value <= 0
            ):
                return None

        if (
            isinstance(discount, bool)
            or not isinstance(discount, int)
            or not 0 <= discount <= 100
        ):
            discount = 0

        return (initial / 100, final / 100, discount)

    @staticmethod
    def _is_valid_item(item) -> bool:
        return (
            isinstance(item, dict)
            and isinstance(item.get("id"), int)
            and not isinstance(item.get("id"), bool)
            and isinstance(item.get("name"), str)
        )

    @staticmethod
    def _unique_by_id(items) -> List[dict]:
        # Conserva la primera aparición de cada juego.
        unique = {}

        for item in items:
            unique.setdefault(item["id"], item)

        return list(unique.values())

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
        discounts = {}
        price_overview = game_data.get("price_overview")

        # Un juego sin precio (gratuito, no lanzado o no vendido en la
        # región) es un dato válido; un importe no numérico se descarta.
        if isinstance(price_overview, dict) and price_overview:
            final_price = price_overview.get("final", 0)

            if isinstance(final_price, (int, float)) and not isinstance(
                final_price, bool
            ):
                prices["Steam"] = final_price / 100

                discount = price_overview.get("discount_percent")

                if (
                    isinstance(discount, int)
                    and not isinstance(discount, bool)
                    and 0 < discount <= 100
                ):
                    discounts["Steam"] = discount

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
            discounts=discounts,
        )
