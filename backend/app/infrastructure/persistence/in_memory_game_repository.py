from typing import List
from app.domain.model.game import Game
from app.domain.ports.game_repository import GameRepository


class InMemoryGameRepository(GameRepository):

    def __init__(self):
        # Precios en pesos colombianos, como las demás fuentes.
        self.games = [
            Game(
                1,
                "Minecraft",
                {
                    "Steam": 119900.0,
                    "PlayStation": 119900.0,
                    "Xbox": 79900.0
                }
            ),
            Game(
                2,
                "Cyberpunk 2077",
                {
                    "Steam": 239900.0,
                    "PlayStation": 199900.0,
                    "Xbox": 199900.0
                }
            ),
            Game(
                3,
                "Elden Ring",
                {
                    "Steam": 239900.0,
                    "PlayStation": 239900.0,
                    "Xbox": 239900.0
                }
            ),
            Game(
                4,
                "Red Dead Redemption 2",
                {
                    "Steam": 239900.0,
                    "PlayStation": 159900.0,
                    "Xbox": 179900.0
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