from typing import Optional

from app.domain.model.game_details import GameDetails
from app.domain.ports.game_details_source import GameDetailsSource


class GetGameDetails:
    """
    Ficha de un juego para su página: sinopsis, tráilers, capturas y datos.

    Solo los juegos de Steam tienen ficha. Los que solo se venden en otra
    tienda no la tienen y la página muestra únicamente sus precios.
    """

    def __init__(self, source: GameDetailsSource):
        self.source = source

    def execute(self, game_id: str) -> Optional[GameDetails]:
        if not game_id.isdecimal():
            return None

        return self.source.get(game_id)
