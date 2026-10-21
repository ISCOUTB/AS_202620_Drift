"""
S12 — Plazo total compartido por las llamadas de una operación.

Las pruebas usan un reloj virtual: la espera simulada de cada respuesta y el
backoff avanzan el reloj sin dormir, de modo que el resultado es exacto y no
depende de la máquina. La medición de p50/p95/p99 con tiempo real está en
`scripts/s12_latencia_steam.py`; estas pruebas verifican la regla.
"""

import importlib.util
from pathlib import Path

import httpx
import pytest

from app.infrastructure.external.resilient_http import (
    ExternalSourceError,
    RetryPolicy,
    TimeBudget,
    get_json,
)
from app.infrastructure.external.steam import steam_game_repository
from app.infrastructure.external.steam.steam_game_repository import (
    DEFAULT_TOTAL_DEADLINE_SECONDS,
    SteamGameRepository,
)

URL = "https://store.steampowered.com/api/storesearch/"


class VirtualClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


def hanging_get(clock, timeouts):
    """Un upstream que nunca responde: cada intento consume su timeout."""

    def fake_get(url, params=None, **kwargs):
        timeouts.append(kwargs["timeout"])
        clock.now += kwargs["timeout"]

        raise httpx.ReadTimeout("sin respuesta")

    return fake_get


def policy(deadline=None):
    return RetryPolicy(
        timeout_seconds=3.0,
        max_attempts=2,
        backoff_base_seconds=0.25,
        backoff_max_seconds=2.0,
        total_deadline_seconds=deadline,
    )


def call(clock, deadline, uniform=lambda: 1.0):
    budget = TimeBudget(deadline, clock) if deadline is not None else None

    return get_json(
        URL,
        {"term": "x"},
        source="Steam",
        policy=policy(deadline),
        sleep=clock.sleep,
        uniform=uniform,
        budget=budget,
    )


def test_without_a_total_deadline_timeouts_and_retries_add_up(monkeypatch):
    # Línea base (S11): dos timeouts de 3 s y un backoff superan el umbral de
    # 5 s de E6 aunque cada llamada respete su propio timeout.
    clock, timeouts = VirtualClock(), []
    monkeypatch.setattr(
        steam_game_repository.httpx, "get", hanging_get(clock, timeouts)
    )

    with pytest.raises(ExternalSourceError) as raised:
        call(clock, deadline=None)

    assert raised.value.reason == "timeout"
    assert timeouts == [3.0, 3.0]
    assert clock.now == 6.25


def test_a_total_deadline_bounds_timeouts_and_retries(monkeypatch):
    clock, timeouts = VirtualClock(), []
    monkeypatch.setattr(
        steam_game_repository.httpx, "get", hanging_get(clock, timeouts)
    )

    with pytest.raises(ExternalSourceError) as raised:
        call(clock, deadline=4.0)

    assert raised.value.reason == "timeout"
    # El segundo intento solo recibe lo que quedaba del plazo.
    assert timeouts == [3.0, 0.75]
    assert clock.now == 4.0


def test_retry_is_skipped_when_the_wait_does_not_fit(monkeypatch):
    clock, timeouts = VirtualClock(), []
    monkeypatch.setattr(
        steam_game_repository.httpx, "get", hanging_get(clock, timeouts)
    )

    with pytest.raises(ExternalSourceError):
        call(clock, deadline=3.1)

    # Tras 3 s quedan 0.1 s y el backoff es de 0.25 s: no se reintenta.
    assert timeouts == [3.0]
    assert clock.now == 3.0


def test_an_exhausted_budget_fails_without_calling_the_source(monkeypatch):
    clock, timeouts = VirtualClock(), []
    monkeypatch.setattr(
        steam_game_repository.httpx, "get", hanging_get(clock, timeouts)
    )
    budget = TimeBudget(1.0, clock)
    clock.now = 2.0

    with pytest.raises(ExternalSourceError) as raised:
        get_json(
            URL,
            {},
            source="Steam",
            policy=policy(1.0),
            sleep=clock.sleep,
            budget=budget,
        )

    assert raised.value.reason == "timeout"
    assert timeouts == []


def test_a_fast_success_is_not_affected_by_the_budget(monkeypatch):
    clock = VirtualClock()

    def fake_get(url, params=None, **kwargs):
        clock.now += 0.2

        return httpx.Response(
            200,
            json={"items": []},
            request=httpx.Request("GET", url),
        )

    monkeypatch.setattr(steam_game_repository.httpx, "get", fake_get)

    assert call(clock, deadline=4.0) == {"items": []}
    assert clock.now == 0.2


def test_search_and_details_share_one_budget(monkeypatch):
    # La búsqueda tarda 2.5 s; al pedir los detalles solo quedan 1.5 s. Sin un
    # plazo compartido cada fase tendría sus 3 s y la operación pasaría de 5 s.
    clock, timeouts = VirtualClock(), []

    def fake_get(url, params=None, **kwargs):
        if "storesearch" in url:
            clock.now += 2.5

            return httpx.Response(
                200,
                json={"items": [{"id": 620, "name": "Portal 2"}]},
                request=httpx.Request("GET", url),
            )

        timeouts.append(kwargs["timeout"])
        clock.now += kwargs["timeout"]

        raise httpx.ReadTimeout("sin respuesta")

    monkeypatch.setattr(steam_game_repository.httpx, "get", fake_get)

    repository = SteamGameRepository(
        policy=policy(4.0),
        sleep=clock.sleep,
        clock=clock,
    )

    with pytest.raises(ExternalSourceError) as raised:
        repository.search("portal 2")

    assert raised.value.reason == "timeout"
    assert timeouts == [1.5]
    assert clock.now == 4.0


def test_default_steam_policy_has_a_total_deadline_that_the_environment_can_change(
    monkeypatch,
):
    monkeypatch.delenv("DRIFT_STEAM_TOTAL_DEADLINE_SECONDS", raising=False)

    assert (
        SteamGameRepository()._policy.total_deadline_seconds
        == DEFAULT_TOTAL_DEADLINE_SECONDS
    )

    monkeypatch.setenv("DRIFT_STEAM_TOTAL_DEADLINE_SECONDS", "2.5")
    assert SteamGameRepository()._policy.total_deadline_seconds == 2.5

    monkeypatch.setenv("DRIFT_STEAM_TOTAL_DEADLINE_SECONDS", "off")
    assert SteamGameRepository()._policy.total_deadline_seconds is None


def test_invalid_total_deadline_is_rejected():
    with pytest.raises(ValueError):
        RetryPolicy(total_deadline_seconds=0)


def _load_script():
    path = Path(__file__).resolve().parents[2] / "scripts" / "s12_latencia_steam.py"
    spec = importlib.util.spec_from_file_location("s12_latencia_steam", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def test_percentiles_use_nearest_rank_and_require_enough_samples():
    script = _load_script()
    values = list(range(1, 101))  # 1..100

    assert script.percentile(values, 50) == 50
    assert script.percentile(values, 95) == 95
    assert script.percentile(values, 99) == 99
    assert script.percentile([], 95) is None

    few = script.summarize([1.0, 2.0, 3.0])
    assert few["n"] == 3
    assert few["p95"] is None and few["p99"] is None

    enough = script.summarize(values)
    assert enough["p95"] == 95 and enough["p99"] == 99
