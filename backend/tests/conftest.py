"""Configuración común de las pruebas del backend."""

import pytest

from tests.admin_auth import ADMIN_TOKEN


@pytest.fixture(autouse=True)
def security_defaults(monkeypatch):
    """Token administrativo conocido y sin límite de tasa.

    Las pruebas que verifican esos controles (test_s13_seguridad_api.py) los
    cambian de forma explícita.
    """

    from app import main

    monkeypatch.setenv("DRIFT_ADMIN_TOKEN", ADMIN_TOKEN)
    monkeypatch.setattr(main.rate_limiter, "limit", 0)


@pytest.fixture(autouse=True)
def empty_snapshot_store():
    """Cada prueba empieza sin copias de respaldo de otras pruebas (ADR-0015)."""

    from app import main

    # Con DRIFT_DATABASE_URL el almacén es PostgreSQL y no se vacía aquí.
    clear = getattr(main.snapshot_store, "clear", None)

    if clear is not None:
        clear()
