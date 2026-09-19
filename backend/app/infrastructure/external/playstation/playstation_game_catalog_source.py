from datetime import datetime, timezone
from typing import Any, List

import httpx

from app.domain.model.normalized_game import NormalizedGame
from app.domain.ports.game_catalog_source import GameCatalogSource


class PlayStationGameCatalogSource(GameCatalogSource):
    """Adaptador del catálogo documentado por PSN Swagger."""

    _catalog_url = (
        "https://store.playstation.com/"
        "store/api/chihiro/00_09_000/container/co/es/999/"
        "STORE-MSF77008-ALLGAMES"
    )

    def fetch_catalog(self) -> List[NormalizedGame]:
        response = httpx.get(
            self._catalog_url,
            params={
                "size": 100,
                "start": 0,
                "gameContentType": "games",
            },
            headers={"Accept": "application/json"},
            timeout=10.0,
        )
        response.raise_for_status()

        payload = response.json()
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

    @staticmethod
    def _normalize(item: dict, captured_at: datetime) -> NormalizedGame:
        sku = item.get("default_sku") or {}
        price = PlayStationGameCatalogSource._price(sku)

        return NormalizedGame(
            id=str(item["id"]),
            name=item["name"],
            source="playstation",
            platform=item.get("playable_platform") or "PlayStation",
            price=price,
            currency=(
                sku.get("currency")
                or sku.get("currency_code")
                or item.get("currency")
                or "COP"
            ),
            discount=PlayStationGameCatalogSource._discount(sku),
            captured_at=captured_at,
        )

    @staticmethod
    def _price(sku: dict) -> float:
        price = sku.get("price", sku.get("actual_price", 0))
        if isinstance(price, dict):
            price = price.get("value", price.get("amount", 0))
        try:
            # PSN Swagger define default_sku.price en unidades menores.
            return float(price) / 100
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _discount(sku: dict) -> int:
        discount = sku.get("discount", sku.get("discount_percentage", 0))
        try:
            return int(discount)
        except (TypeError, ValueError):
            return 0
