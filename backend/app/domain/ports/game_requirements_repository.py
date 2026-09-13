from abc import ABC, abstractmethod
from typing import Optional

from app.domain.model.game_requirements import GameRequirements


class GameRequirementsRepository(ABC):
    @abstractmethod
    def get_by_game_id(self, game_id: int) -> Optional[GameRequirements]:
        pass