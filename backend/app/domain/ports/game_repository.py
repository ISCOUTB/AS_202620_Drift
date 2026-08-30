from abc import ABC, abstractmethod
from typing import List
from app.domain.model.game import Game


class GameRepository(ABC):

    @abstractmethod
    def search(self, query: str) -> List[Game]:
        pass