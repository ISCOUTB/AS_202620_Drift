from typing import Iterable, List, Optional

from app.domain.model.game import Game
from app.domain.ports.game_repository import GameRepository


class SearchGames:

    def __init__(self, repository: GameRepository):
        self.repository = repository

    def execute(
        self,
        query: str,
        platforms: Optional[Iterable[str]] = None,
    ) -> List[Game]:
        """
        Busca un juego en todas las tiendas.

        Con `platforms`, cada juego conserva solo las tiendas de esas
        plataformas y se omiten los juegos que no se venden en ninguna.
        """

        games = self.repository.search(query)

        wanted = set(platforms or ())

        if not wanted:
            return games

        return [
            restricted
            for restricted in (game.restricted_to(wanted) for game in games)
            if restricted.prices
        ]
