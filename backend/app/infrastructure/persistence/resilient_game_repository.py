from typing import List

import httpx

from app.domain.model.game import Game
from app.domain.ports.game_repository import GameRepository


class ResilientGameRepository(GameRepository):
    def __init__(
        self,
        primary_repository: GameRepository,
        fallback_repository: GameRepository,
    ):
        self.primary_repository = primary_repository
        self.fallback_repository = fallback_repository

    def search(self, query: str) -> List[Game]:
        try:
            return self.primary_repository.search(query)
        except httpx.HTTPError:
            fallback_games = self.fallback_repository.search(query)

            for game in fallback_games:
                game.unavailable_sources = ["Steam"]

            return fallback_games