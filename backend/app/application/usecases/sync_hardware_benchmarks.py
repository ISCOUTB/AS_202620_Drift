from datetime import datetime, timezone
from typing import Callable, Dict, Optional

from app.domain.ports.hardware_benchmark_store import HardwareBenchmarkStore


class BenchmarkSyncRejected(Exception):
    """
    La copia de puntajes llegó vacía o con otra forma.

    Aceptarla borraría los puntajes guardados, así que se rechaza y se
    conserva lo que ya había (mismo criterio que el catálogo de PlayStation).
    """

    def __init__(self, kind: str):
        super().__init__(kind)
        self.kind = kind


class SyncHardwareBenchmarks:
    """
    Carga en el almacén los puntajes de gráficas y procesadores.

    `sources` entrega, por tipo, la copia más reciente (archivo o dirección
    privada). `on_loaded` avisa a los catálogos para que vuelvan a leer.
    Sin almacén (no hay base de datos) solo se recargan los catálogos.
    """

    def __init__(
        self,
        sources: Dict[str, Callable[[], dict]],
        store: Optional[HardwareBenchmarkStore],
        on_loaded: Callable[[], None] = lambda: None,
    ):
        self._sources = sources
        self._store = store
        self._on_loaded = on_loaded

    def execute(self) -> dict:
        payloads = {}

        # Primero se validan todas: no se guarda una mitad si la otra falla.
        for kind, source in self._sources.items():
            payload = source()

            if not _has_items(payload):
                raise BenchmarkSyncRejected(kind)

            payloads[kind] = payload

        loaded = {}

        for kind, payload in payloads.items():
            if self._store is not None:
                loaded[kind] = self._store.replace(kind, payload)
            else:
                loaded[kind] = len(payload["items"])

        self._on_loaded()

        return {
            "loaded": loaded,
            "stored_in_database": self._store is not None,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }


def _has_items(payload) -> bool:
    return (
        isinstance(payload, dict)
        and isinstance(payload.get("items"), list)
        and len(payload["items"]) > 0
    )
