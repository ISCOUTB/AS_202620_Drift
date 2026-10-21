import time
from threading import Lock
from typing import Callable, List, Optional

import httpx  # noqa: F401  los tests parchean cheapshark_game_repository.httpx.get

from app.domain.model.game import Game
from app.domain.ports.exchange_rate_provider import ExchangeRateProvider
from app.domain.ports.game_repository import GameRepository
from app.infrastructure.external.resilient_http import (
    ExternalSourceError,
    RetryPolicy,
    TimeBudget,
    get_json,
)
from app.infrastructure.external.single_flight_cache import SingleFlightCache
from app.infrastructure.game_copy import copy_games


SOURCE_NAME = "CheapShark"

# CheapShark limita las llamadas pero no publica la cifra, y su documentación
# advierte de bloqueos ante tráfico automatizado excesivo: un único reintento,
# que respeta `Retry-After` (hasta 2 s). El plazo total coincide con el de la
# fuente secundaria (DRIFT_SOURCE_TIMEOUT_SECONDS) para que el hilo que la
# búsqueda abandona termine junto con su plazo en lugar de seguir ocupado.
DEFAULT_POLICY = dict(timeout_seconds=3.0, max_attempts=2)
DEFAULT_TOTAL_DEADLINE_SECONDS = 3.0


class CheapSharkGameRepository(GameRepository):
    """Adaptador de CheapShark: precios de tiendas de juegos de PC."""

    _base_url = "https://www.cheapshark.com/api/1.0"
    _redirect_url = "https://www.cheapshark.com/redirect"

    # CheapShark rechaza peticiones sin un User-Agent descriptivo.
    _headers = {
        "User-Agent": "DRIFT/1.0 (proyecto academico AS_202620 UTB)",
        "Accept": "application/json",
    }

    # Steam ya se consulta directamente y en pesos colombianos.
    _excluded_store_ids = {"1"}

    def __init__(
        self,
        exchange_rates: ExchangeRateProvider,
        policy: Optional[RetryPolicy] = None,
        sleep: Callable[[float], None] = time.sleep,
    ):
        # Variables DRIFT_CHEAPSHARK_*; ver arc42 §7 y §8.13.
        self._policy = policy or RetryPolicy.from_env(
            "DRIFT_CHEAPSHARK",
            default_total_deadline_seconds=DEFAULT_TOTAL_DEADLINE_SECONDS,
            **DEFAULT_POLICY,
        )
        self._sleep = sleep
        self._exchange_rates = exchange_rates
        self._cache = SingleFlightCache(ttl_seconds=60)
        self._stores = {}
        self._stores_loaded_at = None
        self._stores_duration_seconds = 24 * 60 * 60
        self._lock = Lock()

    def search(self, query: str) -> List[Game]:
        cache_key = query.strip().lower()

        if not cache_key:
            return []

        games = self._cache.get_or_load(
            cache_key,
            lambda: self._search_cheapshark(query.strip()),
        )

        return copy_games(games)

    def _search_cheapshark(self, query: str) -> List[Game]:
        # Un solo plazo para la consulta de ofertas y, si la caché de tiendas
        # está vacía, la lista de tiendas.
        budget = TimeBudget.from_policy(self._policy)

        deals = get_json(
            f"{self._base_url}/deals",
            {
                "title": query,
                "pageSize": 60,
            },
            source=SOURCE_NAME,
            policy=self._policy,
            sleep=self._sleep,
            headers=self._headers,
            budget=budget,
        )

        # Una lista vacía es «sin ofertas» (dato legítimo); cualquier otra
        # forma es una respuesta inválida y no debe cachearse como vacía.
        if not isinstance(deals, list):
            raise ExternalSourceError(SOURCE_NAME, "invalid_response")

        if not deals:
            return []

        stores = self._get_stores(budget)

        # CheapShark entrega precios en USD; Steam los entrega en COP.
        # Se convierte a COP para que la comparación de precios sea válida.
        usd_to_cop = self._exchange_rates.usd_to_cop()

        games_by_id = {}

        for deal in deals:
            if not isinstance(deal, dict):
                continue

            store_id = str(deal.get("storeID"))

            if store_id in self._excluded_store_ids:
                continue

            store_name = stores.get(store_id)
            price = self._price_in_cop(deal, usd_to_cop)

            if not store_name or not deal.get("title") or price is None:
                continue

            self._add_offer(games_by_id, deal, store_name, price)

        return list(games_by_id.values())

    def _add_offer(
        self,
        games_by_id: dict,
        deal: dict,
        store_name: str,
        price: float,
    ) -> None:
        """Registra la oferta en su juego si es la más barata de esa tienda."""

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

        if current_price is not None and price >= current_price:
            return

        game.prices[store_name] = price

        # CheapShark lleva a la oferta en la tienda mediante su enlace de
        # redirección; el dealID ya viene codificado.
        if deal.get("dealID"):
            game.links[store_name] = (
                f"{self._redirect_url}?dealID={deal['dealID']}"
            )

    @staticmethod
    def _price_in_cop(deal: dict, usd_to_cop: float) -> Optional[float]:
        try:
            return round(float(deal["salePrice"]) * usd_to_cop, 2)
        except (KeyError, TypeError, ValueError):
            return None

    def _get_stores(self, budget: Optional[TimeBudget] = None) -> dict:
        # El lock protege solo la lectura y la escritura, no la llamada HTTP.
        with self._lock:
            if self._stores and time.monotonic() - self._stores_loaded_at < self._stores_duration_seconds:
                return self._stores

        try:
            stores = get_json(
                f"{self._base_url}/stores",
                None,
                source=SOURCE_NAME,
                policy=self._policy,
                sleep=self._sleep,
                headers=self._headers,
                budget=budget,
            )

            # Sin lista de tiendas no se puede nombrar ninguna oferta: es un
            # fallo de la fuente, no «ninguna tienda».
            if not isinstance(stores, list):
                raise ExternalSourceError(SOURCE_NAME, "invalid_response")
        except ExternalSourceError:
            # Falló el refresco de una lista vencida: los nombres de tienda
            # casi no cambian, así que la lista anterior sigue siendo útil.
            # Sin lista previa no hay con qué nombrar las ofertas y el fallo
            # se propaga (y no se guarda en la caché de búsquedas).
            with self._lock:
                stale_stores = self._stores

            if stale_stores:
                return stale_stores

            raise

        active_stores = {
            str(store["storeID"]): store["storeName"]
            for store in stores
            if isinstance(store, dict)
            and store.get("isActive")
            and "storeID" in store
            and "storeName" in store
        }

        with self._lock:
            self._stores = active_stores
            self._stores_loaded_at = time.monotonic()

        return active_stores
