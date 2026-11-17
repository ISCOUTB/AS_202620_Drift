from abc import ABC, abstractmethod
from typing import Optional

from app.domain.model.price_history import PriceHistory


class PriceHistoryRepository(ABC):

    @abstractmethod
    def get(self, game_id: str) -> Optional[PriceHistory]:
        """`None` cuando la fuente del historial no conoce ese juego."""
