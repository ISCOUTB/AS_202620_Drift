from datetime import datetime, timezone

from app.domain.ports.game_catalog_repository import (
    GameCatalogRepository,
)
from app.domain.ports.game_catalog_source import GameCatalogSource


class CatalogSyncRejected(Exception):
    """
    La fuente respondió, pero sin juegos utilizables.

    Un catálogo de tienda sin un solo juego no es un dato legítimo: es una
    respuesta con otra forma, vacía o degradada. Aceptarla borraría el
    catálogo local, así que la sincronización se rechaza y se conserva lo
    que ya había (S12, arc42 §8.13).
    """

    def __init__(self, reason: str = "empty_catalog"):
        super().__init__(reason)
        self.reason = reason


class SyncPlayStationCatalog:
    def __init__(
        self,
        source: GameCatalogSource,
        catalog: GameCatalogRepository,
    ):
        self.source = source
        self.catalog = catalog

    def execute(self) -> dict:
        games = self.source.fetch_catalog()

        if not games:
            raise CatalogSyncRejected()

        self.catalog.replace(games)

        return {
            "source": "playstation",
            "games_loaded": len(games),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }