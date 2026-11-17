import logging
import os

from app.domain.ports.source_snapshot_store import SourceSnapshotStore
from app.infrastructure.observability import log_event
from app.infrastructure.persistence.in_memory_source_snapshot_store import (
    InMemorySourceSnapshotStore,
)
from app.infrastructure.persistence.resilient_source_snapshot_store import (
    ResilientSourceSnapshotStore,
)
from app.infrastructure.persistence.stale_fallback_game_repository import (
    stale_seconds_from_env,
)

logger = logging.getLogger("drift")


def build_source_snapshot_store() -> SourceSnapshotStore:
    """
    Elige dónde se guardan las copias de respaldo (ADR-0014).

    Con `DRIFT_DATABASE_URL`: PostgreSQL, con la memoria como segundo
    respaldo. Sin ella (desarrollo local, CI): solo memoria.

    El controlador de PostgreSQL se importa solo si hace falta, así los
    entornos sin base de datos no necesitan tenerlo instalado.
    """

    memory = InMemorySourceSnapshotStore()
    database_url = os.getenv("DRIFT_DATABASE_URL", "").strip()

    if not database_url:
        log_event(logger, "snapshot_store_configured", backend="memory")
        return memory

    try:
        from app.infrastructure.persistence.postgres_database import (
            shared_database,
        )
        from app.infrastructure.persistence.postgres_source_snapshot_store import (
            PostgresSourceSnapshotStore,
        )
    except ImportError:
        log_event(
            logger,
            "snapshot_store_configured",
            backend="memory",
            reason="postgres_driver_missing",
        )
        return memory

    try:
        durable = PostgresSourceSnapshotStore(
            shared_database(database_url),
            max_age_seconds=stale_seconds_from_env(),
        )
    except Exception as error:  # noqa: BLE001  una URL mal escrita no tumba la API
        log_event(
            logger,
            "snapshot_store_configured",
            backend="memory",
            reason="postgres_configuration_error",
            error=type(error).__name__,
        )
        return memory

    log_event(logger, "snapshot_store_configured", backend="postgres")

    return ResilientSourceSnapshotStore(primary=durable, fallback=memory)
