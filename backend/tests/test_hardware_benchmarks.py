from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app.application.usecases.estimate_compatibility import (
    EstimateCompatibility,
)
from app.application.usecases.list_hardware_catalogue import (
    ListHardwareCatalogue,
)
from app.domain.model.game_requirements import GameRequirements
from app.domain.ports.game_requirements_repository import (
    GameRequirementsRepository,
)
from app.domain.services.cpu_classifier import classify_cpu, cpu_level_from_score
from app.domain.services.gpu_classifier import level_from_score
from app.infrastructure.persistence import json_hardware_benchmark_repository
from app.infrastructure.persistence.json_hardware_benchmark_repository import (
    CPU_NOISE_WORDS,
    JsonHardwareBenchmarkRepository,
    cpu_benchmark_repository,
    load_benchmark_payload,
)

# Todos los puntajes de estas pruebas son inventados.
SNAPSHOT_FIXTURE = Path(__file__).parent / "fixtures" / "gpu_benchmarks_sample.json"
URL_VARIABLE = "DRIFT_GPU_BENCHMARKS_URL"


@pytest.fixture
def benchmarks():
    """Catálogo pequeño y fijo de gráficas."""

    return JsonHardwareBenchmarkRepository(
        payload={
            "source": "Fuente de prueba",
            "benchmark": "Benchmark de prueba",
            "retrieved_at": "2026-10-12",
            "items": [
                {"name": "NVIDIA GeForce RTX 3060", "score": 1978, "laptop": False},
                {"name": "NVIDIA GeForce RTX 3060 (notebook)", "score": 1801, "laptop": True},
                {"name": "NVIDIA GeForce RTX 3060 Ti", "score": 2691, "laptop": False},
                {"name": "NVIDIA GeForce GTX 1060", "score": 803, "laptop": False},
                {"name": "NVIDIA GeForce GTX 1060-3GB", "score": 156, "laptop": False},
                {"name": "NVIDIA GeForce GTX 1070", "score": 1236, "laptop": False},
                {"name": "AMD Radeon RX 580", "score": 1004, "laptop": False},
                {"name": "NVIDIA RTX 4050 (notebook)", "score": 1500, "laptop": True},
                {"name": "NVIDIA Titan Xp", "score": 2100, "laptop": False},
            ],
        },
    )


@pytest.fixture
def processors():
    """Catálogo pequeño y fijo de procesadores."""

    return JsonHardwareBenchmarkRepository(
        payload={
            "source": "Fuente de prueba",
            "benchmark": "Benchmark de procesadores de prueba",
            "retrieved_at": "2026-10-12",
            "items": [
                {"name": "Intel Core i5-12400 Processor", "score": 5889},
                {"name": "Intel Core i5-12400F Processor", "score": 5891},
                {"name": "AMD Ryzen 5 5600", "score": 5663},
                {"name": "AMD Ryzen 7 5800X3D", "score": 7258},
                {"name": "Procesador Nuevo 990", "score": 9500},
            ],
        },
        noise_words=CPU_NOISE_WORDS,
        variant_words=(),
    )


def _names(items):
    return sorted(item.name for item in items)


def test_catalogue_lists_and_finds_cards_by_exact_name(benchmarks):
    assert len(benchmarks.list_all()) == 9

    card = benchmarks.get_by_name("  nvidia geforce rtx 3060 (notebook) ")

    assert card.score == 1801
    assert card.laptop is True
    assert benchmarks.get_by_name("Tarjeta inventada") is None
    assert benchmarks.get_by_name(None) is None
    assert benchmarks.describe_source()["source"] == "Fuente de prueba"


@pytest.mark.parametrize(
    "text, expected",
    [
        # Alternativas de un mismo requisito.
        (
            "Nvidia GeForce GTX 1060 6GB / AMD Radeon RX 580 4GB",
            ["AMD Radeon RX 580", "NVIDIA GeForce GTX 1060"],
        ),
        # La variante por VRAM es una tarjeta distinta.
        ("NVIDIA GEFORCE GTX 1060 3 GB", ["NVIDIA GeForce GTX 1060-3GB"]),
        ("GeForce GTX 1060 (3 GB)", ["NVIDIA GeForce GTX 1060-3GB"]),
        # "Ti" no es el modelo base.
        ("GeForce RTX 3060 Ti", ["NVIDIA GeForce RTX 3060 Ti"]),
        ("GeForce RTX 3060", ["NVIDIA GeForce RTX 3060"]),
        # Portátil solo si el texto lo dice, o si no hay versión de escritorio.
        ("RTX 3060 laptop GPU", ["NVIDIA GeForce RTX 3060 (notebook)"]),
        ("GeForce RTX 4050", ["NVIDIA RTX 4050 (notebook)"]),
        # Variante que el catálogo no tiene: no se confunde con la base.
        ("GeForce GTX 1070 Ti", []),
        ("Compatible con DirectX 11 y 2 GB de VRAM", []),
        ("", []),
        (None, []),
    ],
)
def test_catalogue_recognises_cards_inside_requirement_text(benchmarks, text, expected):
    assert _names(benchmarks.find_in_text(text)) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        (
            "Intel Core i5-12400 / AMD Ryzen 5 5600",
            ["AMD Ryzen 5 5600", "Intel Core i5-12400 Processor"],
        ),
        # La variante "F" es otro modelo del catálogo.
        ("Intel Core i5-12400F", ["Intel Core i5-12400F Processor"]),
        ("AMD Ryzen 7 5800X3D", ["AMD Ryzen 7 5800X3D"]),
        # Procesadores antiguos o genéricos que el catálogo no tiene.
        ("Intel Core i5-2500K / AMD FX-6300", []),
        ("Dual Core 2.4 GHz", []),
    ],
)
def test_catalogue_recognises_processors_inside_requirement_text(processors, text, expected):
    assert _names(processors.find_in_text(text)) == expected


@pytest.mark.parametrize(
    "text, level",
    [
        ("Intel Core i5-2500K / AMD FX-6300", 2),
        ("Intel Core i7-4770K / AMD Ryzen 5 1500X", 3),
        ("INTEL CORE I5-8400 or AMD RYZEN 3 3300X", 3),
        ("INTEL CORE I7-8700K or AMD RYZEN 5 3600X", 4),
        ("Intel Core i5-12400", 4),
        ("Intel Core i7-12700H", 5),
        # Bajo consumo de portátil: un nivel menos que su gama.
        ("Intel Core i5-1135G7", 3),
        ("Intel Core i7-8550U", 3),
        ("Intel Core Ultra 7 265K", 5),
        ("AMD Ryzen Threadripper 3970X", 5),
        ("Core 2 Duo E8400", 1),
        ("AMD FX-4300", 1),
        # Los textos genéricos no se adivinan.
        ("Dual Core 2.4 GHz", None),
        ("", None),
        (None, None),
    ],
)
def test_cpu_classifier_levels(text, level):
    assert classify_cpu(text) == level


@pytest.mark.parametrize(
    "score, level",
    [(1000, 1), (2500, 2), (4000, 3), (6000, 4), (12000, 5)],
)
def test_cpu_level_from_score(score, level):
    assert cpu_level_from_score(score) == level


@pytest.mark.parametrize(
    "score, level",
    [(100, 1), (250, 2), (800, 3), (1500, 4), (5000, 5)],
)
def test_level_from_score(score, level):
    assert level_from_score(score) == level


def test_local_snapshot_is_preferred_and_needs_no_network(monkeypatch):
    def forbidden_get(*args, **kwargs):
        raise AssertionError("con archivo local no debe usarse la red")

    monkeypatch.setattr(json_hardware_benchmark_repository.httpx, "get", forbidden_get)
    monkeypatch.setenv(URL_VARIABLE, "https://privado.invalid/gpus.json")

    payload = load_benchmark_payload(SNAPSHOT_FIXTURE, URL_VARIABLE)

    assert payload["items"][0]["name"] == "NVIDIA GeForce RTX 3060"


def _remote_repository():
    return JsonHardwareBenchmarkRepository(
        loader=lambda: load_benchmark_payload("no-existe/gpus.json", URL_VARIABLE),
    )


def test_snapshot_is_downloaded_from_the_private_url(monkeypatch):
    requested = []

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"items": [{"name": "NVIDIA GeForce RTX 3060", "score": 1978}]}

    def mock_get(url, **kwargs):
        requested.append(url)
        return Response()

    monkeypatch.setattr(json_hardware_benchmark_repository.httpx, "get", mock_get)
    monkeypatch.setenv(URL_VARIABLE, "https://privado.invalid/gpus.json")

    repository = _remote_repository()

    assert repository.get_by_name("NVIDIA GeForce RTX 3060").score == 1978
    assert requested == ["https://privado.invalid/gpus.json"]


def test_catalogue_is_empty_without_file_or_url(monkeypatch):
    monkeypatch.delenv(URL_VARIABLE, raising=False)

    repository = _remote_repository()

    assert repository.list_all() == []
    assert repository.find_in_text("GeForce RTX 3060") == []
    assert repository.get_by_name("NVIDIA GeForce RTX 3060") is None
    assert repository.describe_source() == {}


def test_failed_download_is_retried_later_not_on_every_request(monkeypatch):
    attempts = []

    def failing_get(url, **kwargs):
        attempts.append(url)
        raise httpx.ConnectError("sin red")

    monkeypatch.setattr(json_hardware_benchmark_repository.httpx, "get", failing_get)
    monkeypatch.setenv(URL_VARIABLE, "https://privado.invalid/gpus.json")

    repository = _remote_repository()

    assert repository.list_all() == []
    assert repository.list_all() == []
    assert len(attempts) == 1

    # Pasado el tiempo de espera vuelve a intentarlo.
    repository._next_attempt_at = 0.0
    repository.list_all()

    assert len(attempts) == 2


def test_processor_catalogue_factory_builds_without_touching_the_network(monkeypatch):
    def forbidden_get(*args, **kwargs):
        raise AssertionError("crear el catálogo no debe consultar nada")

    monkeypatch.setattr(json_hardware_benchmark_repository.httpx, "get", forbidden_get)

    assert cpu_benchmark_repository() is not None


class _Requirements(GameRequirementsRepository):
    def __init__(self, minimum, recommended=None):
        self.requirements = GameRequirements(
            game_id=1,
            minimum_ram_gb=8,
            recommended_ram_gb=16,
            minimum_gpu_score=3,
            recommended_gpu_score=4,
            minimum_details=minimum,
            recommended_details=recommended or {},
            source="Steam",
            minimum_cpu_score=classify_cpu(minimum.get("processor")),
            recommended_cpu_score=classify_cpu((recommended or {}).get("processor")),
        )

    def get_by_game_id(self, game_id):
        return self.requirements


def _check(result, component):
    return next(
        check
        for check in result["checks"]
        if check["component"] == component
    )


def test_gpu_is_compared_by_benchmark_when_both_cards_are_known(benchmarks):
    estimate = EstimateCompatibility(
        _Requirements(
            {"graphics": "GeForce GTX 1060 6GB / Radeon RX 580"},
            {"graphics": "GeForce GTX 1070"},
        ),
        benchmarks,
    )

    result = estimate.execute(
        game_id=1,
        ram_gb=16,
        gpu_score=1,
        gpu_name="NVIDIA GeForce RTX 3060 (notebook)",
    )

    check = _check(result, "gpu")

    assert check["basis"] == "benchmark"
    assert check["level"] == "recommended"
    assert check["yours_name"] == "NVIDIA GeForce RTX 3060 (notebook)"

    # Los puntajes deciden el veredicto, pero no se entregan.
    assert (check["yours"], check["minimum"], check["recommended"]) == (None, None, None)

    # Varias alternativas: la referencia es el promedio de sus puntajes.
    assert check["minimum_name"] == (
        "promedio de AMD Radeon RX 580 y NVIDIA GeForce GTX 1060"
    )
    assert check["recommended_name"] == "NVIDIA GeForce GTX 1070"
    assert result["gpu_benchmark"]["source"] == "Fuente de prueba"


def test_gpu_below_the_required_score_is_insufficient(benchmarks):
    estimate = EstimateCompatibility(
        _Requirements({"graphics": "GeForce RTX 3060 Ti"}),
        benchmarks,
    )

    result = estimate.execute(
        game_id=1,
        ram_gb=16,
        gpu_score=5,
        gpu_name="NVIDIA GeForce GTX 1060",
    )

    assert _check(result, "gpu")["level"] == "insufficient"
    assert result["status"] == "No compatible"


def test_gpu_falls_back_to_levels_when_the_requirement_is_not_in_the_catalogue(benchmarks):
    estimate = EstimateCompatibility(
        _Requirements({"graphics": "Nvidia GeForce GTX 770 2GB / AMD Radeon R9 280 3GB"}),
        benchmarks,
    )

    result = estimate.execute(
        game_id=1,
        ram_gb=16,
        gpu_score=1,
        gpu_name="NVIDIA GeForce RTX 3060",
    )

    check = _check(result, "gpu")

    assert check["basis"] == "level"
    assert check["yours"] == 4
    assert check["level"] == "recommended"
    assert result["gpu_benchmark"] is None


def test_known_family_keeps_its_level_regardless_of_the_score(benchmarks):
    estimate = EstimateCompatibility(
        _Requirements({"graphics": "Tarjeta sin modelo reconocible"}),
        benchmarks,
    )

    result = estimate.execute(
        game_id=1,
        ram_gb=16,
        gpu_score=1,
        gpu_name="NVIDIA Titan Xp",
    )

    assert result["gpu_score_used"] == 5
    assert result["gpu_recognized"] is True


def test_processor_is_compared_by_benchmark_when_both_are_known(benchmarks, processors):
    estimate = EstimateCompatibility(
        _Requirements(
            {"processor": "Intel Core i5-12400 / AMD Ryzen 5 5600"},
            {"processor": "AMD Ryzen 7 5800X3D"},
        ),
        benchmarks,
        processors,
    )

    result = estimate.execute(
        game_id=1,
        ram_gb=16,
        gpu_score=4,
        cpu_name="Intel Core i5-12400F Processor",
    )

    check = _check(result, "cpu")

    # 5891 puntos frente a un promedio de 5776 y un recomendado de 7258.
    assert check["basis"] == "benchmark"
    assert check["level"] == "minimum"
    assert check["minimum_name"] == (
        "promedio de AMD Ryzen 5 5600 y Intel Core i5-12400 Processor"
    )
    assert (check["yours"], check["minimum"], check["recommended"]) == (None, None, None)
    assert result["cpu_benchmark"]["benchmark"] == "Benchmark de procesadores de prueba"


def test_processor_falls_back_to_levels_for_old_requirements(benchmarks, processors):
    estimate = EstimateCompatibility(
        _Requirements(
            {"processor": "Intel Core i5-2500K / AMD FX-6300"},
            {"processor": "Intel Core i7-4770K / AMD Ryzen 5 1500X"},
        ),
        benchmarks,
        processors,
    )

    result = estimate.execute(
        game_id=1,
        ram_gb=16,
        gpu_score=4,
        cpu_name="AMD Ryzen 5 5600",
    )

    check = _check(result, "cpu")

    assert check["basis"] == "level"
    assert (check["yours"], check["minimum"], check["recommended"]) == (4, 2, 3)
    assert check["level"] == "recommended"
    assert result["cpu_recognized"] is True
    assert result["cpu_benchmark"] is None


def test_new_processor_gets_its_level_from_the_benchmark_score(benchmarks, processors):
    estimate = EstimateCompatibility(
        _Requirements({"processor": "Intel Core i5-8400"}),
        benchmarks,
        processors,
    )

    result = estimate.execute(
        game_id=1,
        ram_gb=16,
        gpu_score=4,
        cpu_name="Procesador Nuevo 990",
    )

    # Las reglas por familia no lo conocen: su nivel sale del puntaje.
    assert result["cpu_score_used"] == 5
    assert _check(result, "cpu")["level"] == "recommended"


def test_processor_is_not_compared_when_the_user_gives_none(benchmarks, processors):
    estimate = EstimateCompatibility(
        _Requirements({"processor": "Dual Core 2.4 GHz"}),
        benchmarks,
        processors,
    )

    result = estimate.execute(game_id=1, ram_gb=16, gpu_score=4)

    assert _check(result, "cpu")["level"] == "unknown"
    assert result["cpu_recognized"] is None
    assert result["partial"] is True


def test_catalogue_use_case_lists_names_and_levels_without_scores(benchmarks):
    catalogue = ListHardwareCatalogue(
        benchmarks,
        classify=lambda name: 4 if "3060" in name else None,
        level_from_score=lambda score: 2,
    ).execute()

    assert catalogue["source"] == "Fuente de prueba"
    assert len(catalogue["items"]) == 9

    # Los puntajes no se publican en el catálogo.
    assert all(set(item) == {"name", "laptop", "level"} for item in catalogue["items"])

    levels = {item["name"]: item["level"] for item in catalogue["items"]}

    # Nivel por familia cuando se reconoce; si no, a partir del puntaje.
    assert levels["NVIDIA GeForce RTX 3060"] == 4
    assert levels["AMD Radeon RX 580"] == 2


@pytest.mark.parametrize(
    "path, use_case",
    [("gpus", "list_gpu_catalogue"), ("cpus", "list_cpu_catalogue")],
)
def test_hardware_endpoints_delegate_to_the_use_case(benchmarks, monkeypatch, path, use_case):
    import app.main as main

    monkeypatch.setattr(getattr(main, use_case), "benchmarks", benchmarks)

    body = TestClient(main.app).get(f"/hardware/{path}").json()

    assert body["source"] == "Fuente de prueba"
    assert len(body["items"]) == 9
    assert all(set(item) == {"name", "laptop", "level"} for item in body["items"])
    assert all(1 <= item["level"] <= 5 for item in body["items"])
