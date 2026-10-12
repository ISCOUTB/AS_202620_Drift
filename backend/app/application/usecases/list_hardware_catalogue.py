from typing import Callable, Optional

from app.domain.ports.hardware_benchmark_repository import (
    HardwareBenchmarkRepository,
)


class ListHardwareCatalogue:
    """
    Componentes de un tipo (gráficas o procesadores) para el buscador de «Mi PC».

    Entrega nombres y nivel aproximado, no los puntajes: estos solo aparecen
    en el resultado de una comparación concreta.
    """

    def __init__(
        self,
        benchmarks: HardwareBenchmarkRepository,
        classify: Callable[[Optional[str]], Optional[int]],
        level_from_score: Callable[[int], int],
    ):
        self.benchmarks = benchmarks
        self.classify = classify
        self.level_from_score = level_from_score

    def execute(self) -> dict:
        return {
            **self.benchmarks.describe_source(),
            "items": [
                {
                    "name": item.name,
                    "laptop": item.laptop,
                    # Nivel por familia de modelo o, si es nuevo, por su puntaje.
                    "level": (
                        self.classify(item.name)
                        or self.level_from_score(item.score)
                    ),
                }
                for item in self.benchmarks.list_all()
            ],
        }
