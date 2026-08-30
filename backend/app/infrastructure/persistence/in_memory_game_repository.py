from typing import List
from app.domain.model.game import Game
from app.domain.ports.game_repository import GameRepository


class InMemoryGameRepository(GameRepository):

    def __init__(self):
        self.games = [
            Game(
                1,
                "Minecraft",
                {
                    "Steam": 29.99,
                    "PlayStation": 29.99,
                    "Xbox": 19.99
                }
            ),
            Game(
                2,
                "Cyberpunk 2077",
                {
                    "Steam": 59.99,
                    "PlayStation": 49.99,
                    "Xbox": 49.99
                }
            ),
            Game(
                3,
                "Elden Ring",
                {
                    "Steam": 59.99,
                    "PlayStation": 59.99,
                    "Xbox": 59.99
                }
            ),
            Game(
                4,
                "Red Dead Redemption 2",
                {
                    "Steam": 59.99,
                    "PlayStation": 39.99,
                    "Xbox": 44.99
                }
            )
        ]

    def search(self, query: str) -> List[Game]:
        query = query.lower().strip()

        return [
            game
            for game in self.games
            if query in game.name.lower()
        ]