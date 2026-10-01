from threading import Lock
from typing import List

from app.domain.model.game import Game
from app.domain.model.normalized_game import NormalizedGame
from app.domain.ports.game_repository import GameRepository
from app.domain.ports.game_catalog_repository import (
    GameCatalogRepository,
)


class InMemoryPlayStationCatalog(
    GameRepository,
    GameCatalogRepository,
):
    """
    Catálogo local de PlayStation.

    Mantiene una copia sincronizada del catálogo general,
    pero también permite realizar búsquedas directas en
    PlayStation cuando el juego no está almacenado localmente.
    """

    def __init__(self, search_source=None):
        self._games: list[NormalizedGame] = []
        self._lock = Lock()
        self._search_source = search_source

    def replace(
        self,
        games: List[NormalizedGame],
    ) -> None:

        with self._lock:
            self._games = list(games)

    def search(
        self,
        query: str,
    ) -> List[Game]:

        normalized_query = query.lower().strip()

        if not normalized_query:
            return []

        with self._lock:
            local_matches = [
                game
                for game in self._games
                if normalized_query in game.name.lower()
            ]

        if local_matches:
            return [
                self._to_game(game)
                for game in local_matches
            ]

        if self._search_source is None:
            return []

        remote_matches = self._search_source.search_catalog(
            query
        )

        return [
            self._to_game(game)
            for game in remote_matches
        ]

    @staticmethod
    def _to_game(
        game: NormalizedGame,
    ) -> Game:

        return Game(
            id=game.id,
            name=game.name,
            prices={
                "PlayStation": game.price,
            },
        )