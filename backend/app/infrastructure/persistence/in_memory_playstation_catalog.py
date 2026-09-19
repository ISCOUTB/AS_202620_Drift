from threading import Lock
from typing import List

from app.domain.model.game import Game
from app.domain.model.normalized_game import NormalizedGame
from app.domain.ports.game_repository import GameRepository


class InMemoryPlayStationCatalog(GameRepository):
    """Caché local reemplazada sólo después de una captura exitosa."""

    def __init__(self):
        self._games: list[NormalizedGame] = []
        self._lock = Lock()

    def replace(self, games: List[NormalizedGame]) -> None:
        with self._lock:
            self._games = list(games)

    def search(self, query: str) -> List[Game]:
        normalized_query = query.lower().strip()
        with self._lock:
            matches = [
                game
                for game in self._games
                if normalized_query in game.name.lower()
            ]

        return [
            Game(
                id=game.id,
                name=game.name,
                prices={"PlayStation": game.price},
            )
            for game in matches
        ]
