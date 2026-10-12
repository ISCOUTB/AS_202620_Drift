from dataclasses import dataclass


@dataclass(frozen=True)
class HardwareBenchmark:
    """Puntaje de un componente (gráfica o procesador) en un benchmark publicado."""

    name: str
    score: int
    laptop: bool = False
