from typing import Optional

from app.domain.model.game_requirements import GameRequirements
from app.domain.ports.game_requirements_repository import (
    GameRequirementsRepository,
)


class InMemoryGameRequirementsRepository(GameRequirementsRepository):
    """
    Catálogo controlado para demostrar la estimación de compatibilidad.

    Escala de GPU usada en esta etapa:
    1 = básica
    2 = media
    3 = alta
    """

    def __init__(self):
        self.requirements = {
            620: GameRequirements(
                game_id=620,
                minimum_ram_gb=2,
                recommended_ram_gb=4,
                minimum_gpu_score=1,
                recommended_gpu_score=2,
            ),
        }

    def get_by_game_id(self, game_id: int) -> Optional[GameRequirements]:
        return self.requirements.get(game_id)