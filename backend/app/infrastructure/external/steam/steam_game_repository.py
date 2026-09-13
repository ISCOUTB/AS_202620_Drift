import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from typing import List

import httpx

from app.domain.model.game import Game
from app.domain.ports.game_repository import GameRepository


class SteamGameRepository(GameRepository):
    def __init__(self):
        self._cache = {}
        self._cache_duration_seconds = 60
        self._cache_lock = Lock()

    def search(self, query: str) -> List[Game]:
        cache_key = query.strip().lower()

        # Evita que muchos usuarios simultáneos repitan exactamente
        # las mismas consultas a Steam.
        with self._cache_lock:
            cached_result = self._cache.get(cache_key)

            if cached_result and time.monotonic() - cached_result["created_at"] < self._cache_duration_seconds:
                return cached_result["games"]

            games = self._search_steam(query)

            self._cache[cache_key] = {
                "created_at": time.monotonic(),
                "games": games,
            }

            return games

    def _search_steam(self, query: str) -> List[Game]:
        response = httpx.get(
            "https://store.steampowered.com/api/storesearch/",
            params={
                "term": query,
                "cc": "co",
                "l": "spanish",
            },
        )

        response.raise_for_status()
        data = response.json()

        # Se limita a cinco resultados: evita pedir decenas de detalles
        # innecesarios a Steam en una sola búsqueda.
        items = data.get("items", [])[:5]

        if not items:
            return []

        # Los detalles se consultan en paralelo, no uno después de otro.
        with ThreadPoolExecutor(max_workers=min(5, len(items))) as executor:
            games = list(executor.map(self._get_game_details, items))

        return games

    def _get_game_details(self, item: dict) -> Game:
        app_id = item["id"]

        details_response = httpx.get(
            "https://store.steampowered.com/api/appdetails",
            params={
                "appids": app_id,
                "cc": "co",
                "l": "spanish",
            },
        )

        details_response.raise_for_status()

        details_data = details_response.json()
        game_data = details_data.get(str(app_id), {}).get("data", {})

        prices = {}
        price_overview = game_data.get("price_overview")

        if price_overview:
            prices["Steam"] = price_overview.get("final", 0) / 100

        return Game(
            id=app_id,
            name=item["name"],
            prices=prices,
        )