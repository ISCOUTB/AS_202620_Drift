from dataclasses import dataclass
from datetime import datetime
from typing import List

from app.domain.model.game import Game


@dataclass(frozen=True)
class SourceSnapshot:
    """
    Copia de lo que una fuente respondió a una búsqueda (ADR-0015).

    `captured_at` es el momento, en UTC, en que la fuente entregó el dato.
    Con él se decide si la copia todavía es reciente, si solo sirve de
    respaldo o si ya es demasiado vieja para mostrarse.
    """

    games: List[Game]
    captured_at: datetime
