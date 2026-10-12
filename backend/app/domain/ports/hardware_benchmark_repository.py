from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.model.hardware_benchmark import HardwareBenchmark


class HardwareBenchmarkRepository(ABC):
    """Catálogo de puntajes de un tipo de componente (gráficas o procesadores)."""

    @abstractmethod
    def list_all(self) -> List[HardwareBenchmark]:
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[HardwareBenchmark]:
        """Componente cuyo nombre coincide exactamente con el del catálogo."""

    @abstractmethod
    def find_in_text(self, text: str) -> List[HardwareBenchmark]:
        """Componentes del catálogo mencionados en un texto libre de requisitos."""

    @abstractmethod
    def describe_source(self) -> dict:
        """Origen de los puntajes: fuente, benchmark y fecha de consulta."""
