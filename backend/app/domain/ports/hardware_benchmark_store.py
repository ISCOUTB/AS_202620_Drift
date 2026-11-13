from abc import ABC, abstractmethod

GPU = "gpu"
CPU = "cpu"

KINDS = (GPU, CPU)


class HardwareBenchmarkStore(ABC):
    """
    Dónde se guardan los puntajes de gráficas y procesadores.

    Una lista de puntajes tiene esta forma, la misma de las copias JSON:

        {"source": ..., "benchmark": ..., "retrieved_at": ...,
         "items": [{"name": ..., "score": ..., "laptop": ...}]}
    """

    @abstractmethod
    def load(self, kind: str) -> dict:
        """La lista guardada de ese tipo; `{}` si todavía no hay ninguna."""

    @abstractmethod
    def replace(self, kind: str, payload: dict) -> int:
        """Reemplaza la lista completa de ese tipo. Devuelve cuántos guardó."""
