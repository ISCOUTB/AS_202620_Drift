from dataclasses import dataclass
from typing import Optional

from app.domain.model.price_history import PriceHistory
from app.domain.ports.price_history_repository import PriceHistoryRepository

NOT_CONFIGURED = "not_configured"
NOT_FOUND = "not_found"


@dataclass(frozen=True)
class PriceHistoryAnswer:
    """
    `history` es `None` cuando no hay historial que mostrar; `reason` dice
    por qué: la fuente no está configurada o no conoce ese juego.
    """

    history: Optional[PriceHistory]
    reason: Optional[str] = None


class GetPriceHistory:
    """Consulta el historial de precios de un juego (ficha del problema)."""

    def __init__(self, repository: Optional[PriceHistoryRepository]):
        # Sin fuente de historial (falta su llave) el caso de uso sigue
        # existiendo y responde que no está disponible.
        self.repository = repository

    def execute(self, game_id: str) -> PriceHistoryAnswer:
        if self.repository is None:
            return PriceHistoryAnswer(None, NOT_CONFIGURED)

        history = self.repository.get(game_id)

        if history is None:
            return PriceHistoryAnswer(None, NOT_FOUND)

        return PriceHistoryAnswer(history)
