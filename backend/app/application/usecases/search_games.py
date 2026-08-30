from typing import List
from app.domain.model.game import Game
from app.domain.ports.game_repository import GameRepository


class SearchGames:

    def __init__(self, repository: GameRepository):
        self.repository = repository

    def execute(self, query: str) -> List[Game]:
        return self.repository.search(query)