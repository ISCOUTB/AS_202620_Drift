import time
from threading import Lock
from typing import List, Optional

import httpx

from app.domain.model.game import Game
from app.domain.ports.exchange_rate_provider import ExchangeRateProvider
from app.domain.ports.game_repository import GameRepository


class CheapSharkGameRepository(GameRepository):
    """Adaptador de CheapShark: precios de tiendas de juegos de PC."""

    _base_url = "https://www.cheapshark.com/api/1.0"

    # CheapShark rechaza peticiones sin un User-Agent descriptivo.
    _headers = {
        "User-Agent": "DRIFT/1.0 (proyecto academico AS_202620 UTB)",
        "Accept": "application/json",
    }

    # Steam ya se consulta directamente y en pesos colombianos.
    _excluded_store_ids = {"1"}

    def __init__(self, exchange_rates: ExchangeRateProvider):
        self._exchange_rates = exchange_rates
        self._cache = {}
        self._cache_duration_seconds = 60
        self._stores = {}
        self._stores_loaded_at = None
        self._stores_duration_seconds = 24 * 60 * 60
        self._lock = Lock()

    def search(self, query: str) -> List[Game]:
        cache_key = query.strip().lower()

        if not cache_key:
            return []

        with self._lock:
            cached_result = self._cache.get(cache_key)

            if cached_result and time.monotonic() - cached_result["created_at"] < self._cache_duration_seconds:
                return self._copy(cached_result["games"])

            games = self._search_cheapshark(query.strip())

            self._cache[cache_key] = {
                "created_at": time.monotonic(),
                "games": games,
            }

            return self._copy(games)

    @staticmethod
    def _copy(games: List[Game]) -> List[Game]:
        # Los repositorios que combinan tiendas modifican `prices`;
        # se entregan copias para no alterar lo guardado en caché.
        return [
            Game(
                id=game.id,
                name=game.name,
                prices=dict(game.prices),
                image=game.image,
            )
            for game in games
        ]

    def _search_cheapshark(self, query: str) -> List[Game]:
        response = httpx.get(
            f"{self._base_url}/deals",
            params={
                "title": query,
                "pageSize": 60,
            },
            headers=self._headers,
            timeout=5.0,
        )

        response.raise_for_status()
        deals = response.json()

        if not isinstance(deals, list) or not deals:
            return []

        stores = self._get_stores()

        # CheapShark entrega precios en USD; Steam los entrega en COP.
        # Se convierte a COP para que la comparación de precios sea válida.
        usd_to_cop = self._exchange_rates.usd_to_cop()

        games_by_id = {}

        for deal in deals:
            store_id = str(deal.get("storeID"))

            if store_id in self._excluded_store_ids:
                continue

            store_name = stores.get(store_id)
            price = self._price_in_cop(deal, usd_to_cop)

            if not store_name or not deal.get("title") or price is None:
                continue

            # El steamAppID permite unir el juego con el resultado de Steam.
            game_id = deal.get("steamAppID") or f"cheapshark-{deal.get('gameID')}"

            game = games_by_id.get(game_id)

            if game is None:
                game = Game(
                    id=game_id,
                    name=deal["title"],
                    prices={},
                    image=deal.get("thumb"),
                )
                games_by_id[game_id] = game

            current_price = game.prices.get(store_name)

            if current_price is None or price < current_price:
                game.prices[store_name] = price

        return list(games_by_id.values())

    @staticmethod
    def _price_in_cop(deal: dict, usd_to_cop: float) -> Optional[float]:
        try:
            return round(float(deal["salePrice"]) * usd_to_cop, 2)
        except (KeyError, TypeError, ValueError):
            return None

    def _get_stores(self) -> dict:
        if self._stores and time.monotonic() - self._stores_loaded_at < self._stores_duration_seconds:
            return self._stores

        response = httpx.get(
            f"{self._base_url}/stores",
            headers=self._headers,
            timeout=5.0,
        )

        response.raise_for_status()
        stores = response.json()

        if not isinstance(stores, list):
            return {}

        self._stores = {
            str(store["storeID"]): store["storeName"]
            for store in stores
            if store.get("isActive")
        }
        self._stores_loaded_at = time.monotonic()

        return self._stores
