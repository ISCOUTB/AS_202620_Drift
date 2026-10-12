import httpx
import pytest
from fastapi.testclient import TestClient

from app.application.usecases.estimate_compatibility import (
    EstimateCompatibility,
)
from app.domain.model.game_requirements import GameRequirements
from app.domain.ports.game_requirements_repository import (
    GameRequirementsRepository,
)
from app.domain.services.gpu_classifier import classify_gpu
from app.infrastructure.external.steam import steam_game_requirements_repository
from app.infrastructure.external.steam.steam_game_requirements_repository import (
    SteamGameRequirementsRepository,
    parse_requirement_block,
)
from app.infrastructure.persistence.fallback_game_requirements_repository import (
    FallbackGameRequirementsRepository,
)
from app.infrastructure.persistence.in_memory_game_requirements_repository import (
    InMemoryGameRequirementsRepository,
)

RDR2_MINIMUM = (
    '<strong>Mínimo:</strong><br><ul class="bb_ul">'
    "<li>Requiere un procesador y un sistema operativo de 64 bits<br></li>"
    "<li><strong>SO:</strong> Windows 10 - 64-bit<br></li>"
    "<li><strong>Procesador:</strong> Intel® Core™ i5-2500K / AMD FX-6300<br></li>"
    "<li><strong>Memoria:</strong> 8 GB de RAM<br></li>"
    "<li><strong>Gráficos:</strong> Nvidia GeForce GTX 770 2GB / AMD Radeon R9 280 3GB<br></li>"
    "<li><strong>Almacenamiento:</strong> 150 GB de espacio disponible<br></li></ul>"
)

RDR2_RECOMMENDED = (
    '<strong>Recomendado:</strong><br><ul class="bb_ul">'
    "<li><strong>Memoria:</strong> 12 GB de RAM<br></li>"
    "<li><strong>Gráficos:</strong> Nvidia GeForce GTX 1060 6GB / AMD Radeon RX 480 4GB<br></li>"
    "<li><strong>Almacenamiento:</strong> 150 GB de espacio disponible</li></ul>"
)


class _MockResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def _mock_steam(monkeypatch, payload, calls=None):
    def mock_get(url, params=None, timeout=None):
        if calls is not None:
            calls.append(params["appids"])

        return _MockResponse(payload)

    monkeypatch.setattr(
        steam_game_requirements_repository.httpx,
        "get",
        mock_get,
    )


@pytest.mark.parametrize(
    "text, level",
    [
        ("Nvidia GeForce GTX 770 2GB / AMD Radeon R9 280 3GB", 3),
        ("GeForce RTX 2060, Radeon RX 5600 XT, or Intel Arc A580", 4),
        ("NVIDIA GeForce RTX 4070", 5),
        ("GTX 1080 Ti", 5),
        ("GTX 1050 Ti", 3),
        ("GTX 1050", 2),
        # "RX 560" no debe confundirse con "RX 5600".
        ("AMD Radeon RX 5600 XT", 4),
        ("Radeon RX 560", 2),
        # Cualquiera de las alternativas cumple: se toma la más baja.
        ("GeForce GTX 950, Radeon R7 360, or Intel HD Graphics 630", 1),
        ("Gráficos HD Intel 2000 o superior", 1),
        ("Compatible con DirectX 11", None),
        ("", None),
        (None, None),
    ],
)
def test_gpu_classifier_levels(text, level):
    assert classify_gpu(text) == level


def test_parse_requirement_block_extracts_labelled_values():
    details = parse_requirement_block(RDR2_MINIMUM)

    assert details == {
        "os": "Windows 10 - 64-bit",
        "processor": "Intel® Core™ i5-2500K / AMD FX-6300",
        "memory": "8 GB de RAM",
        "graphics": "Nvidia GeForce GTX 770 2GB / AMD Radeon R9 280 3GB",
        "storage": "150 GB de espacio disponible",
    }

    assert parse_requirement_block(None) == {}


def test_steam_requirements_are_parsed_and_cached(monkeypatch):
    calls = []

    _mock_steam(
        monkeypatch,
        {
            "1174180": {
                "success": True,
                "data": {
                    "pc_requirements": {
                        "minimum": RDR2_MINIMUM,
                        "recommended": RDR2_RECOMMENDED,
                    }
                },
            }
        },
        calls,
    )

    repository = SteamGameRequirementsRepository()
    requirements = repository.get_by_game_id(1174180)
    repository.get_by_game_id(1174180)

    assert requirements.source == "Steam"
    assert requirements.minimum_ram_gb == 8
    assert requirements.recommended_ram_gb == 12
    assert requirements.minimum_gpu_score == 3
    assert requirements.recommended_gpu_score == 3
    assert requirements.minimum_storage_gb == 150
    assert requirements.minimum_details["memory"] == "8 GB de RAM"
    assert len(calls) == 1


def test_steam_requirements_handle_megabytes_and_missing_recommended(monkeypatch):
    _mock_steam(
        monkeypatch,
        {
            "10": {
                "data": {
                    "pc_requirements": {
                        "minimum": (
                            "<ul><li><strong>Memory:</strong> 512 MB RAM</li>"
                            "<li><strong>Graphics:</strong> DirectX 9 compatible</li>"
                            "<li><strong>Hard Drive:</strong> 4,5 GB available</li></ul>"
                        )
                    }
                }
            }
        },
    )

    requirements = SteamGameRequirementsRepository().get_by_game_id(10)

    assert requirements.minimum_ram_gb == 1
    assert requirements.recommended_ram_gb == 1
    assert requirements.minimum_gpu_score is None
    assert requirements.minimum_storage_gb == 5


@pytest.mark.parametrize(
    "payload",
    [
        {"7": {"success": False}},
        {"7": {"success": True, "data": []}},
        {"7": {"data": {"pc_requirements": []}}},
        {"7": {"data": {"pc_requirements": {"minimum": "<ul><li>Sin datos</li></ul>"}}}},
    ],
)
def test_steam_requirements_unavailable(monkeypatch, payload):
    _mock_steam(monkeypatch, payload)

    assert SteamGameRequirementsRepository().get_by_game_id(7) is None


def test_steam_requirements_survive_network_failure_and_invalid_ids(monkeypatch):
    calls = []

    def failing_get(url, params=None, timeout=None):
        calls.append(params["appids"])
        raise httpx.ConnectError("Steam no disponible")

    monkeypatch.setattr(
        steam_game_requirements_repository.httpx,
        "get",
        failing_get,
    )

    repository = SteamGameRequirementsRepository()

    assert repository.get_by_game_id(620) is None

    # Los identificadores imposibles ni siquiera se consultan.
    assert repository.get_by_game_id(0) is None
    assert repository.get_by_game_id(-5) is None
    assert repository.get_by_game_id(10**12) is None
    assert calls == [620]


def test_fallback_prefers_curated_requirements(monkeypatch):
    class NeverCalled(GameRequirementsRepository):
        def get_by_game_id(self, game_id):
            raise AssertionError("no debía consultarse")

    repository = FallbackGameRequirementsRepository([
        InMemoryGameRequirementsRepository(),
        NeverCalled(),
    ])

    assert repository.get_by_game_id(620).source == "DRIFT"

    empty = FallbackGameRequirementsRepository([
        InMemoryGameRequirementsRepository(),
    ])

    assert empty.get_by_game_id(999) is None


class _FixedRequirements(GameRequirementsRepository):
    def __init__(self, **overrides):
        values = {
            "game_id": 1,
            "minimum_ram_gb": 8,
            "recommended_ram_gb": 12,
            "minimum_gpu_score": 3,
            "recommended_gpu_score": 4,
            "minimum_storage_gb": 150,
            "recommended_storage_gb": 150,
            "source": "Steam",
        }
        values.update(overrides)
        self.requirements = GameRequirements(**values)

    def get_by_game_id(self, game_id):
        return self.requirements


def _levels(result):
    return {check["component"]: check["level"] for check in result["checks"]}


def test_compatibility_breaks_down_each_component():
    estimate = EstimateCompatibility(_FixedRequirements())

    result = estimate.execute(
        game_id=1,
        ram_gb=16,
        gpu_score=1,
        storage_gb=200,
        gpu_name="NVIDIA GeForce GTX 1060",
    )

    assert result["status"] == "Compatible con limitaciones"
    assert _levels(result) == {
        "ram": "recommended",
        "cpu": "unknown",
        "gpu": "minimum",
        "storage": "recommended",
    }

    # El modelo reconocido prevalece sobre el número enviado.
    assert result["gpu_score_used"] == 3
    assert result["gpu_recognized"] is True
    # El usuario no indicó procesador: ese componente queda sin comparar.
    assert result["partial"] is True


def test_compatibility_fails_when_one_component_is_insufficient():
    estimate = EstimateCompatibility(_FixedRequirements())

    result = estimate.execute(
        game_id=1,
        ram_gb=32,
        gpu_score=5,
        storage_gb=50,
    )

    assert result["status"] == "No compatible"
    assert _levels(result)["storage"] == "insufficient"
    assert result["gpu_recognized"] is None


def test_compatibility_is_partial_when_a_component_cannot_be_compared():
    estimate = EstimateCompatibility(
        _FixedRequirements(
            minimum_gpu_score=None,
            recommended_gpu_score=None,
        )
    )

    result = estimate.execute(
        game_id=1,
        ram_gb=16,
        gpu_score=2,
        gpu_name="una gráfica desconocida",
    )

    # Sin gráfica ni almacenamiento comparables, decide la RAM.
    assert result["status"] == "Compatible"
    assert result["partial"] is True
    assert result["gpu_recognized"] is False
    assert _levels(result) == {
        "ram": "recommended",
        "cpu": "unknown",
        "gpu": "unknown",
        "storage": "unknown",
    }


def test_compatibility_endpoint_uses_steam_requirements(monkeypatch):
    from app.main import app

    _mock_steam(
        monkeypatch,
        {
            "424242": {
                "data": {
                    "pc_requirements": {
                        "minimum": RDR2_MINIMUM,
                        "recommended": RDR2_RECOMMENDED,
                    }
                }
            }
        },
    )

    response = TestClient(app).post(
        "/games/424242/compatibility",
        json={
            "ram_gb": 16,
            "gpu_score": 1,
            "gpu_name": "NVIDIA GeForce RTX 3060",
            "storage_gb": 500,
        },
    )

    body = response.json()

    assert response.status_code == 200
    assert body["status"] == "Compatible"
    assert body["source"] == "Steam"
    assert body["minimum_storage_gb"] == 150
    assert body["requirements_text"]["minimum"]["memory"] == "8 GB de RAM"
