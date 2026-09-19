from typing import List

from app.domain.model.game import Game
from app.domain.ports.game_repository import GameRepository


class CombinedGameRepository(GameRepository):
    """Combina los resultados existentes con el catálogo local de PlayStation."""

    def __init__(self, primary_repository: GameRepository, secondary_repository: GameRepository):
        self.primary_repository = primary_repository
        self.secondary_repository = secondary_repository

    def search(self, query: str) -> List[Game]:
        games = self.primary_repository.search(query)
        games_by_name = {game.name.casefold(): game for game in games}

        for game in self.secondary_repository.search(query):
            existing_game = games_by_name.get(game.name.casefold())
            if existing_game:
                existing_game.prices.update(game.prices)
                continue

            games.append(game)
            games_by_name[game.name.casefold()] = game

        return games
