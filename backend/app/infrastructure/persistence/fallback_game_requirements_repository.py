from typing import List, Optional

from app.domain.model.game_requirements import GameRequirements
from app.domain.ports.game_requirements_repository import (
    GameRequirementsRepository,
)


class FallbackGameRequirementsRepository(GameRequirementsRepository):
    """Consulta varios repositorios en orden y devuelve el primer resultado."""

    def __init__(self, repositories: List[GameRequirementsRepository]):
        self.repositories = repositories

    def get_by_game_id(self, game_id: int) -> Optional[GameRequirements]:
        for repository in self.repositories:
            requirements = repository.get_by_game_id(game_id)

            if requirements is not None:
                return requirements

        return None
