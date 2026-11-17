"""
ADR-0018 — Puntajes de gráficas y procesadores en la base de datos.

Las pruebas del adaptador de PostgreSQL solo corren con
`DRIFT_TEST_DATABASE_URL`. Las demás no usan red ni base de datos, y todos
los puntajes son inventados.
"""

import os

import pytest
from fastapi.testclient import TestClient

from app import main
from app.application.usecases.sync_hardware_benchmarks import (
    BenchmarkSyncRejected,
    SyncHardwareBenchmarks,
)
from app.domain.ports.hardware_benchmark_store import HardwareBenchmarkStore
from app.infrastructure.persistence.json_hardware_benchmark_repository import (
    JsonHardwareBenchmarkRepository,
    load_from_store_or_copy,
)
from tests.admin_auth import ADMIN_HEADERS

client = TestClient(main.app)


def copy(*names, source="Copia de prueba"):
    return {
        "source": source,
        "benchmark": "Benchmark de prueba (valores inventados)",
        "retrieved_at": "2026-10-12",
        "items": [
            {"name": name, "score": 1000 + position, "laptop": False}
            for position, name in enumerate(names)
        ],
    }


GPUS = copy("NVIDIA GeForce RTX 3060", "AMD Radeon RX 6600")
CPUS = copy("Intel Core i5-12400F")


class MemoryStore(HardwareBenchmarkStore):
    def __init__(self, saved=None):
        self.saved = dict(saved or {})
        self.broken = False
        self.replaced = []

    def load(self, kind):
        if self.broken:
            raise ConnectionError("base de datos caída")

        return self.saved.get(kind, {})

    def replace(self, kind, payload):
        if self.broken:
            raise ConnectionError("base de datos caída")

        self.saved[kind] = payload
        self.replaced.append(kind)

        return len(payload["items"])


# --- De dónde lee el catálogo -------------------------------------------------


def test_scores_are_read_from_the_database_when_it_has_them():
    store = MemoryStore({"gpu": GPUS})

    def copy_must_not_be_read():
        raise AssertionError("no debía leerse la copia JSON")

    assert load_from_store_or_copy("gpu", store, copy_must_not_be_read) == GPUS


def test_an_empty_database_is_filled_from_the_copy_on_first_use():
    store = MemoryStore()

    loaded = load_from_store_or_copy("gpu", store, lambda: GPUS)

    # La migración ocurre sola: la siguiente lectura ya sale de la base.
    assert loaded == GPUS
    assert store.saved == {"gpu": GPUS}


def test_an_empty_copy_is_never_written_to_the_database():
    store = MemoryStore()

    assert load_from_store_or_copy("gpu", store, dict) == {}
    assert store.replaced == []


def test_with_the_database_down_the_copy_is_used_and_nothing_fails():
    store = MemoryStore({"gpu": copy("Vieja")})
    store.broken = True

    assert load_from_store_or_copy("gpu", store, lambda: GPUS) == GPUS
    assert store.replaced == []


def test_without_a_database_the_copy_is_used_as_before():
    assert load_from_store_or_copy("cpu", None, lambda: CPUS) == CPUS


def test_the_catalogue_reads_again_after_a_reload():
    current = {"payload": copy("NVIDIA GeForce RTX 3060")}
    repository = JsonHardwareBenchmarkRepository(loader=lambda: current["payload"])

    assert [item.name for item in repository.list_all()] == [
        "NVIDIA GeForce RTX 3060"
    ]

    current["payload"] = GPUS

    assert len(repository.list_all()) == 1

    repository.reload()

    assert len(repository.list_all()) == 2
    assert repository.get_by_name("amd radeon rx 6600").score == 1001


# --- La carga administrativa --------------------------------------------------


def test_sync_stores_both_lists_and_tells_the_catalogues_to_reload():
    store = MemoryStore()
    reloaded = []
    sync = SyncHardwareBenchmarks(
        {"gpu": lambda: GPUS, "cpu": lambda: CPUS},
        store,
        on_loaded=lambda: reloaded.append(True),
    )

    result = sync.execute()

    assert result["loaded"] == {"gpu": 2, "cpu": 1}
    assert result["stored_in_database"] is True
    assert store.saved == {"gpu": GPUS, "cpu": CPUS}
    assert reloaded == [True]


@pytest.mark.parametrize("bad", [{}, {"items": []}, {"items": "x"}, None, []])
def test_sync_rejects_an_empty_copy_and_keeps_what_was_stored(bad):
    store = MemoryStore({"gpu": GPUS, "cpu": CPUS})
    reloaded = []
    sync = SyncHardwareBenchmarks(
        {"gpu": lambda: copy("Nueva"), "cpu": lambda: bad},
        store,
        on_loaded=lambda: reloaded.append(True),
    )

    with pytest.raises(BenchmarkSyncRejected) as error:
        sync.execute()

    # Ni siquiera la lista válida se guarda: o se cargan las dos o ninguna.
    assert error.value.kind == "cpu"
    assert store.saved == {"gpu": GPUS, "cpu": CPUS}
    assert reloaded == []


def test_sync_without_a_database_only_reloads_the_catalogues():
    reloaded = []
    sync = SyncHardwareBenchmarks(
        {"gpu": lambda: GPUS},
        None,
        on_loaded=lambda: reloaded.append(True),
    )

    result = sync.execute()

    assert result["loaded"] == {"gpu": 2}
    assert result["stored_in_database"] is False
    assert reloaded == [True]


# --- Endpoint POST /hardware/benchmarks/sync ----------------------------------


def test_endpoint_needs_the_admin_token():
    assert client.post("/hardware/benchmarks/sync").status_code == 401
    assert (
        client.post(
            "/hardware/benchmarks/sync",
            headers={"Authorization": "Bearer token-incorrecto"},
        ).status_code
        == 401
    )


def test_endpoint_loads_the_scores(monkeypatch):
    store = MemoryStore()
    monkeypatch.setattr(
        main,
        "sync_hardware_benchmarks",
        SyncHardwareBenchmarks({"gpu": lambda: GPUS, "cpu": lambda: CPUS}, store),
    )

    response = client.post("/hardware/benchmarks/sync", headers=ADMIN_HEADERS)

    assert response.status_code == 200
    assert response.json()["loaded"] == {"gpu": 2, "cpu": 1}
    assert set(store.saved) == {"gpu", "cpu"}


def test_endpoint_reports_an_empty_copy_without_losing_stored_scores(monkeypatch):
    store = MemoryStore({"gpu": GPUS})
    monkeypatch.setattr(
        main,
        "sync_hardware_benchmarks",
        SyncHardwareBenchmarks({"gpu": dict}, store),
    )

    response = client.post("/hardware/benchmarks/sync", headers=ADMIN_HEADERS)

    assert response.status_code == 503
    assert response.json()["detail"] == {
        "reason": "empty_benchmark_copy",
        "kind": "gpu",
        "stored_data_preserved": True,
    }
    assert store.saved == {"gpu": GPUS}


def test_endpoint_reports_a_database_failure(monkeypatch):
    store = MemoryStore()
    store.broken = True
    monkeypatch.setattr(
        main,
        "sync_hardware_benchmarks",
        SyncHardwareBenchmarks({"gpu": lambda: GPUS}, store),
    )

    response = client.post("/hardware/benchmarks/sync", headers=ADMIN_HEADERS)

    assert response.status_code == 503
    assert response.json()["detail"]["reason"] == "benchmark_store_unavailable"


# --- PostgreSQL ---------------------------------------------------------------

DATABASE_URL = os.getenv("DRIFT_TEST_DATABASE_URL", "").strip()

needs_database = pytest.mark.skipif(
    not DATABASE_URL,
    reason="DRIFT_TEST_DATABASE_URL no está definida",
)


@pytest.fixture
def postgres_store():
    from app.infrastructure.persistence.postgres_database import PostgresDatabase
    from app.infrastructure.persistence.postgres_hardware_benchmark_store import (
        PostgresHardwareBenchmarkStore,
    )

    database = PostgresDatabase(DATABASE_URL, acquire_timeout_seconds=5)

    with database.connection() as connection:
        connection.execute(
            "TRUNCATE hardware_benchmark, hardware_benchmark_set"
        )

    yield PostgresHardwareBenchmarkStore(database)

    database.close()


@needs_database
def test_postgres_keeps_the_list_with_its_order_and_source(postgres_store):
    assert postgres_store.load("gpu") == {}
    assert postgres_store.replace("gpu", GPUS) == 2
    assert postgres_store.load("gpu") == GPUS
    assert postgres_store.load("cpu") == {}


@needs_database
def test_postgres_replaces_the_whole_list_of_one_kind_only(postgres_store):
    postgres_store.replace("gpu", GPUS)
    postgres_store.replace("cpu", CPUS)

    newer = copy("NVIDIA GeForce RTX 5070", source="Copia nueva")
    postgres_store.replace("gpu", newer)

    assert postgres_store.load("gpu") == newer
    assert postgres_store.load("cpu") == CPUS


@needs_database
def test_postgres_drops_malformed_entries_and_refuses_an_empty_list(postgres_store):
    mixed = {
        "source": "Copia con errores",
        "items": [
            {"name": "NVIDIA GeForce RTX 3060", "score": 1000, "laptop": True},
            {"name": "", "score": 10},
            {"name": "Sin puntaje"},
            {"name": "Puntaje negativo", "score": -5},
            {"name": "Puntaje booleano", "score": True},
            "no es una entrada",
        ],
    }

    assert postgres_store.replace("gpu", mixed) == 1
    assert postgres_store.load("gpu")["items"] == [
        {"name": "NVIDIA GeForce RTX 3060", "score": 1000, "laptop": True}
    ]

    # Una lista sin entradas válidas no borra la que ya estaba.
    with pytest.raises(ValueError):
        postgres_store.replace("gpu", {"items": [{"name": ""}]})

    with pytest.raises(ValueError):
        postgres_store.replace("consola", GPUS)

    assert len(postgres_store.load("gpu")["items"]) == 1


@needs_database
def test_the_catalogue_works_on_top_of_postgres(postgres_store):
    postgres_store.replace("gpu", GPUS)

    repository = JsonHardwareBenchmarkRepository(
        loader=lambda: load_from_store_or_copy("gpu", postgres_store, dict)
    )

    assert repository.get_by_name("NVIDIA GeForce RTX 3060").score == 1000
    assert [item.name for item in repository.find_in_text("Requiere una RX 6600")] == [
        "AMD Radeon RX 6600"
    ]
    assert repository.describe_source()["source"] == "Copia de prueba"
