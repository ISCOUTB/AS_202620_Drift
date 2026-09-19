from abc import ABC, abstractmethod
from typing import List

from app.domain.model.normalized_game import NormalizedGame


class GameCatalogSource(ABC):

    @abstractmethod
    def fetch_catalog(self) -> List[NormalizedGame]:
        pass
