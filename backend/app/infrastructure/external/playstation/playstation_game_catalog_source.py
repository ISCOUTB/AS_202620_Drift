from datetime import datetime, timezone
from typing import Any, List, Optional
from urllib.parse import quote

import httpx  # noqa: F401  los tests parchean playstation_game_catalog_source.httpx.get

from app.domain.model.normalized_game import NormalizedGame
from app.domain.ports.exchange_rate_provider import ExchangeRateProvider
from app.domain.ports.game_catalog_source import GameCatalogSource
from app.infrastructure.external.resilient_http import (
    RetryPolicy,
    TimeBudget,
    get_json,
)

SOURCE_NAME = "PlayStation"

# El catálogo es un endpoint de la tienda sin contrato publicado: no se
# conocen sus límites. Un reintento acotado y plazos propios por operación;
# la búsqueda comparte el plazo de la fuente secundaria (DRIFT_SOURCE_TIMEOUT_SECONDS).
DEFAULT_SYNC_POLICY = dict(timeout_seconds=10.0, max_attempts=2)
DEFAULT_SEARCH_POLICY = dict(timeout_seconds=3.0, max_attempts=2)
DEFAULT_SEARCH_DEADLINE_SECONDS = 3.0


class PlayStationGameCatalogSource(GameCatalogSource):
    """Adaptador del catálogo de PlayStation Store."""

    _catalog_url = (
        "https://store.playstation.com/"
        "store/api/chihiro/00_09_000/container/co/es/999/"
        "STORE-MSF77008-ALLGAMES"
    )

    _search_url = (
        "https://store.playstation.com/"
        "store/api/chihiro/00_09_000/tumbler/co/es/999/"
    )

    def __init__(
        self,
        exchange_rates: ExchangeRateProvider,
        sync_policy: Optional[RetryPolicy] = None,
        search_policy: Optional[RetryPolicy] = None,
    ):
        self._exchange_rates = exchange_rates
        # Variables DRIFT_PLAYSTATION_SYNC_* y DRIFT_PLAYSTATION_SEARCH_*.
        self._sync_policy = sync_policy or RetryPolicy.from_env(
            "DRIFT_PLAYSTATION_SYNC",
            **DEFAULT_SYNC_POLICY,
        )
        self._search_policy = search_policy or RetryPolicy.from_env(
            "DRIFT_PLAYSTATION_SEARCH",
            default_total_deadline_seconds=DEFAULT_SEARCH_DEADLINE_SECONDS,
            **DEFAULT_SEARCH_POLICY,
        )

    def fetch_catalog(self) -> List[NormalizedGame]:
        """
        Obtiene una página del catálogo general de PlayStation.

        Se mantiene para el endpoint de sincronización existente.
        """

        payload = get_json(
            self._catalog_url,
            {
                "size": 100,
                "start": 0,
                "gameContentType": "games",
            },
            source=SOURCE_NAME,
            policy=self._sync_policy,
            headers={
                "Accept": "application/json",
            },
        )

        captured_at = datetime.now(timezone.utc)

        return [
            self._normalize(item, captured_at)
            for item in self._catalog_items(payload)
            if item.get("id") and item.get("name")
        ]

    def search_catalog(
        self,
        query: str,
        size: int = 10,
    ) -> List[NormalizedGame]:
        """
        Busca directamente un videojuego en PlayStation Store.

        Esto evita depender de que el juego se encuentre
        dentro de los primeros elementos del catálogo general.
        """

        normalized_query = query.strip()

        if not normalized_query:
            return []

        encoded_query = quote(
            normalized_query.replace(" ", "_"),
            safe="",
        )

        url = f"{self._search_url}{encoded_query}"

        payload = get_json(
            url,
            {
                "suggested_size": size,
                "mode": "game",
            },
            source=SOURCE_NAME,
            policy=self._search_policy,
            budget=TimeBudget.from_policy(self._search_policy),
        )

        captured_at = datetime.now(timezone.utc)

        return [
            self._normalize(item, captured_at)
            for item in self._catalog_items(payload)
            if item.get("id") and item.get("name")
        ]

    @staticmethod
    def _catalog_items(payload: Any) -> list[dict]:
        if isinstance(payload, list):
            return payload

        if not isinstance(payload, dict):
            return []

        if isinstance(payload.get("links"), list):
            return payload["links"]

        if isinstance(payload.get("items"), list):
            return payload["items"]

        return [payload]

    def _normalize(
        self,
        item: dict,
        captured_at: datetime,
    ) -> NormalizedGame:

        sku = item.get("default_sku") or {}

        price = self._price(sku)
        currency = self._currency(item, sku)

        # La tienda de Colombia publica precios en USD; se convierten a
        # COP para poder compararlos con los de las demás tiendas.
        if price and currency == "USD":
            price = round(
                price * self._exchange_rates.usd_to_cop(),
                2,
            )
            currency = "COP"

        return NormalizedGame(
            id=str(item["id"]),
            name=item["name"],
            source="playstation",
            platform=item.get(
                "playable_platform"
            ) or "PlayStation",
            price=price,
            currency=currency,
            discount=PlayStationGameCatalogSource._discount(
                sku
            ),
            captured_at=captured_at,
        )

    @staticmethod
    def _currency(item: dict, sku: dict) -> str:
        currency = (
            sku.get("currency")
            or sku.get("currency_code")
            or item.get("currency")
        )

        if currency:
            return str(currency).upper()

        if str(sku.get("display_price") or "").startswith("US$"):
            return "USD"

        return "COP"

    @staticmethod
    def _price(sku: dict) -> Optional[float]:
        """Devuelve None cuando PlayStation no publica un precio."""

        price = sku.get(
            "price",
            sku.get("actual_price"),
        )

        if isinstance(price, dict):
            price = price.get(
                "value",
                price.get("amount"),
            )

        try:
            return float(price) / 100
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _discount(sku: dict) -> int:
        discount = sku.get(
            "discount",
            sku.get("discount_percentage", 0),
        )

        try:
            return int(discount)
        except (TypeError, ValueError):
            return 0