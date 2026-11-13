import logging
import os

from app.domain.ports.account_repository import AccountRepository
from app.infrastructure.observability import log_event
from app.infrastructure.persistence.in_memory_account_repository import (
    InMemoryAccountRepository,
)

logger = logging.getLogger("drift")


def build_account_repository() -> AccountRepository:
    """
    Elige dónde viven las cuentas y los dispositivos (ADR-0017).

    Con `DRIFT_DATABASE_URL`: PostgreSQL. Sin ella: memoria, que se borra al
    reiniciar y solo sirve para desarrollo y pruebas.

    A diferencia de la copia de respaldo de las fuentes, aquí no hay un
    segundo almacén en memoria: si PostgreSQL falla, las cuentas responden
    «no disponible». Guardar un dispositivo en memoria y perderlo después
    sería peor que avisar.
    """

    database_url = os.getenv("DRIFT_DATABASE_URL", "").strip()

    if not database_url:
        log_event(logger, "account_store_configured", backend="memory")
        return InMemoryAccountRepository()

    from app.infrastructure.persistence.postgres_account_repository import (
        PostgresAccountRepository,
    )
    from app.infrastructure.persistence.postgres_database import (
        shared_database,
    )

    log_event(logger, "account_store_configured", backend="postgres")

    return PostgresAccountRepository(shared_database(database_url))
