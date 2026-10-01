from abc import ABC, abstractmethod
from typing import List

from app.domain.model.normalized_game import NormalizedGame


class GameCatalogRepository(ABC):

    @abstractmethod
    def replace(
        self,
        games: List[NormalizedGame],
    ) -> None:
        pass