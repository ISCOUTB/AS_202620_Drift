from abc import ABC, abstractmethod
from typing import Optional

from app.domain.model.game_details import GameDetails


class GameDetailsSource(ABC):
    """Fuente de la ficha de un juego: sinopsis, tráilers y capturas."""

    @abstractmethod
    def get(self, game_id: str) -> Optional[GameDetails]:
        """
        La ficha del juego, o `None` si la fuente no lo conoce.

        Si la fuente no responde, eleva un error: la ruta lo convierte en
        «no disponible» en lugar de decir que el juego no existe.
        """
