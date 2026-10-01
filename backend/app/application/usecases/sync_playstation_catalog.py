from datetime import datetime, timezone

from app.domain.ports.game_catalog_repository import (
    GameCatalogRepository,
)
from app.domain.ports.game_catalog_source import GameCatalogSource


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
        self.catalog.replace(games)

        return {
            "source": "playstation",
            "games_loaded": len(games),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }