from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from app.domain.model.game import Game
from app.domain.model.source_snapshot import SourceSnapshot


class SourceSnapshotStore(ABC):
    """
    Guarda la última respuesta de cada fuente a cada búsqueda (ADR-0015).

    Es un respaldo, no una fuente de verdad: los adaptadores no deben
    lanzar errores hacia quien los usa. Si el almacén no está disponible,
    `get` devuelve `None` y `put` no hace nada.
    """

    @abstractmethod
    def get(self, source: str, key: str) -> Optional[SourceSnapshot]:
        pass

    @abstractmethod
    def put(
        self,
        source: str,
        key: str,
        games: List[Game],
        captured_at: datetime,
    ) -> None:
        pass
