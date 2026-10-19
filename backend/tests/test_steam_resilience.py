"""
S11 — Fallos parciales de la integración con Steam.

Ninguna prueba usa la red: `httpx.get` se reemplaza por respuestas
guionizadas (objetos `httpx.Response` reales, para que `raise_for_status`
y `json()` se comporten como en producción) y la espera entre reintentos
se registra sin dormir.
"""

import logging

import httpx
import pytest
from fastapi.testclient import TestClient

from app.infrastructure.external.resilient_http import (
    ExternalSourceError,
    RetryPolicy,
    get_json,
)
from app.infrastructure.external.steam import steam_game_repository
from app.infrastructure.external.steam.steam_game_repository import (
    SteamGameRepository,
)
from app.main import app

SEARCH_URL = "https://store.steampowered.com/api/storesearch/"
DETAILS_URL = "https://store.steampowered.com/api/appdetails"

POLICY = RetryPolicy(
    timeout_seconds=3.0,
    max_attempts=3,
    backoff_base_seconds=0.5,
    backoff_max_seconds=2.0,
    max_retry_after_seconds=2.0,
)

client = TestClient(app)


def response(status_code=200, payload=None, headers=None, content=None):
    request = httpx.Request("GET", SEARCH_URL)

    if content is not None:
        return httpx.Response(
            status_code,
            content=content,
            headers=headers,
            request=request,
        )

    return httpx.Response(
        status_code,
        json=payload,
        headers=headers,
        request=request,
    )


class Script:
    """Entrega en orden cada resultado; el último se repite sin límite."""

    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def __call__(self, url, params=None, **kwargs):
        self.calls.append({"url": url, "params": params, **kwargs})

        outcome = (
            self.outcomes.pop(0)
            if len(self.outcomes) > 1
            else self.outcomes[0]
        )

        if isinstance(outcome, Exception):
            raise outcome

        return outcome


@pytest.fixture
def steam_http(monkeypatch):
    """
    Rutas simuladas de Steam. Cualquier otra URL (CheapShark, PlayStation,
    tasa de cambio) falla con un error de conexión, de modo que las pruebas
    del endpoint nunca salen a internet.
    """

    routes = {}

    def fake_get(url, params=None, **kwargs):
        for key, script in routes.items():
            if key in url:
                return script(url, params, **kwargs)

        raise httpx.ConnectError(f"ruta no simulada: {url}")

    monkeypatch.setattr(steam_game_repository.httpx, "get", fake_get)

    return routes


def portal_search(items=None):
    items = [{"id": 620, "name": "Portal 2"}] if items is None else items
    return response(payload={"items": items})


def portal_details(final=2600):
    return response(payload={
        "620": {"success": True, "data": {"price_overview": {"final": final}}}
    })


def repository(sleeps=None):
    return SteamGameRepository(
        policy=POLICY,
        sleep=(sleeps if sleeps is not None else []).append,
    )


# --- get_json: política de timeout, reintentos y backoff -------------------


def test_timeout_is_explicit_and_exhausts_the_attempts(steam_http):
    steam_http["example.test"] = script = Script(httpx.ReadTimeout("lenta"))
    sleeps = []

    with pytest.raises(ExternalSourceError) as raised:
        get_json(
            "https://example.test/",
            {},
            source="Steam",
            policy=POLICY,
            sleep=sleeps.append,
            uniform=lambda: 1.0,
        )

    assert raised.value.reason == "timeout"
    # Intentos totales: la llamada inicial más dos reintentos.
    assert len(script.calls) == POLICY.max_attempts == 3
    assert all(call["timeout"] == 3.0 for call in script.calls)
    # Backoff exponencial con jitter máximo: 0.5 s y luego 1.0 s.
    assert sleeps == [0.5, 1.0]


@pytest.mark.parametrize(
    "first_failure",
    [
        httpx.ConnectError("sin conexión"),
        httpx.RemoteProtocolError("conexión cortada"),
        response(500),
        response(503),
    ],
)
def test_transient_failure_is_retried_and_recovers(steam_http, first_failure):
    steam_http["example.test"] = script = Script(first_failure, response(payload={"ok": 1}))
    sleeps = []

    result = get_json(
        "https://example.test/",
        {},
        source="Steam",
        policy=POLICY,
        sleep=sleeps.append,
    )

    assert result == {"ok": 1}
    assert len(script.calls) == 2
    assert len(sleeps) == 1


def test_429_waits_for_retry_after_when_it_is_tolerable(steam_http):
    steam_http["example.test"] = script = Script(
        response(429, headers={"Retry-After": "1"}),
        response(payload={"ok": 1}),
    )
    sleeps = []

    result = get_json(
        "https://example.test/", {}, source="Steam", policy=POLICY, sleep=sleeps.append
    )

    assert result == {"ok": 1}
    assert sleeps == [1.0]
    assert len(script.calls) == 2


def test_429_with_excessive_retry_after_fails_fast(steam_http):
    steam_http["example.test"] = script = Script(
        response(429, headers={"Retry-After": "60"})
    )
    sleeps = []

    with pytest.raises(ExternalSourceError) as raised:
        get_json(
            "https://example.test/", {}, source="Steam", policy=POLICY, sleep=sleeps.append
        )

    assert raised.value.reason == "rate_limited"
    assert raised.value.status_code == 429
    # Reintentar antes de lo que Steam pidió sería ignorar su indicación.
    assert len(script.calls) == 1
    assert sleeps == []


def test_429_without_retry_after_uses_backoff(steam_http):
    steam_http["example.test"] = Script(response(429), response(payload={"ok": 1}))
    sleeps = []

    get_json(
        "https://example.test/",
        {},
        source="Steam",
        policy=POLICY,
        sleep=sleeps.append,
        uniform=lambda: 1.0,
    )

    assert sleeps == [0.5]


def test_persistent_5xx_ends_as_controlled_error(steam_http):
    steam_http["example.test"] = script = Script(response(502))

    with pytest.raises(ExternalSourceError) as raised:
        get_json(
            "https://example.test/", {}, source="Steam", policy=POLICY, sleep=lambda _: None
        )

    assert raised.value.reason == "server_error"
    assert raised.value.status_code == 502
    assert len(script.calls) == POLICY.max_attempts


@pytest.mark.parametrize("status_code", [400, 403, 404])
def test_permanent_4xx_is_never_retried(steam_http, status_code):
    steam_http["example.test"] = script = Script(response(status_code))
    sleeps = []

    with pytest.raises(ExternalSourceError) as raised:
        get_json(
            "https://example.test/", {}, source="Steam", policy=POLICY, sleep=sleeps.append
        )

    assert raised.value.reason == "client_error"
    assert raised.value.status_code == status_code
    assert len(script.calls) == 1
    assert sleeps == []


def test_invalid_json_is_a_controlled_error_without_retry(steam_http):
    steam_http["example.test"] = script = Script(
        response(content=b"<html>mantenimiento</html>")
    )

    with pytest.raises(ExternalSourceError) as raised:
        get_json(
            "https://example.test/", {}, source="Steam", policy=POLICY, sleep=lambda _: None
        )

    assert raised.value.reason == "invalid_response"
    assert len(script.calls) == 1


def test_a_single_attempt_policy_disables_retries(steam_http):
    steam_http["example.test"] = script = Script(httpx.ConnectError("caída"))

    with pytest.raises(ExternalSourceError):
        get_json(
            "https://example.test/",
            {},
            source="Steam",
            policy=RetryPolicy(max_attempts=1),
            sleep=lambda _: None,
        )

    assert len(script.calls) == 1


def test_backoff_is_exponential_jittered_and_capped():
    assert POLICY.backoff_seconds(1, uniform=lambda: 0.0) == 0.0
    assert POLICY.backoff_seconds(1, uniform=lambda: 1.0) == 0.5
    assert POLICY.backoff_seconds(2, uniform=lambda: 1.0) == 1.0
    assert POLICY.backoff_seconds(3, uniform=lambda: 0.5) == 1.0
    # El tope impide que la espera crezca sin límite.
    assert POLICY.backoff_seconds(20, uniform=lambda: 1.0) == 2.0


def test_policy_is_configurable_from_the_environment(monkeypatch):
    monkeypatch.setenv("DRIFT_STEAM_TIMEOUT_SECONDS", "1.5")
    monkeypatch.setenv("DRIFT_STEAM_MAX_ATTEMPTS", "4")

    policy = RetryPolicy.from_env("DRIFT_STEAM")

    assert policy.timeout_seconds == 1.5
    assert policy.max_attempts == 4
    assert policy.backoff_base_seconds == RetryPolicy().backoff_base_seconds


def test_invalid_policy_is_rejected():
    with pytest.raises(ValueError):
        RetryPolicy(max_attempts=0)


def test_logs_report_retries_and_failures_without_the_user_query(steam_http):
    records = []

    class Capture(logging.Handler):
        def emit(self, record):
            records.append(record)

    logger = logging.getLogger("drift")
    handler = Capture()
    previous_level = logger.level
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    try:
        steam_http["example.test"] = Script(httpx.ReadTimeout("lenta"))

        with pytest.raises(ExternalSourceError):
            get_json(
                "https://example.test/",
                {"term": "consulta-secreta"},
                source="Steam",
                policy=POLICY,
                sleep=lambda _: None,
            )
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous_level)

    events = [record.getMessage() for record in records]

    assert events.count("external_retry") == POLICY.max_attempts - 1
    assert events[-1] == "external_request_failed"
    assert records[-1].fields["reason"] == "timeout"
    assert records[-1].fields["attempts"] == POLICY.max_attempts
    assert "elapsed_ms" in records[-1].fields

    for record in records:
        assert "consulta-secreta" not in record.getMessage()
        assert "consulta-secreta" not in str(record.fields)


# --- SteamGameRepository: validación de respuestas y caché ------------------


def test_adapter_recovers_when_a_detail_call_fails_once(steam_http):
    steam_http["storesearch"] = Script(portal_search())
    steam_http["appdetails"] = Script(response(503), portal_details())

    games = repository().search("portal recuperacion")

    assert [game.name for game in games] == ["Portal 2"]
    assert games[0].prices == {"Steam": 26.0}


def test_no_results_is_not_confused_with_a_failed_source(steam_http):
    steam_http["storesearch"] = Script(portal_search(items=[]))

    assert repository().search("sin resultados") == []


@pytest.mark.parametrize(
    "payload",
    [
        ["no", "es", "un", "objeto"],
        {"items": "no es una lista"},
        {"items": [{"nombre": "sin id"}, "texto", {"id": "620", "name": "x"}]},
    ],
)
def test_malformed_search_payload_is_an_error_not_an_empty_result(
    steam_http, payload
):
    steam_http["storesearch"] = Script(response(payload=payload))

    with pytest.raises(ExternalSourceError) as raised:
        repository().search("payload invalido")

    assert raised.value.reason == "invalid_response"


def test_malformed_items_are_skipped_when_valid_ones_remain(steam_http):
    steam_http["storesearch"] = Script(
        portal_search(items=[{"nombre": "sin id"}, {"id": 620, "name": "Portal 2"}])
    )
    steam_http["appdetails"] = Script(portal_details())

    games = repository().search("items mezclados")

    assert [game.name for game in games] == ["Portal 2"]


@pytest.mark.parametrize(
    "details",
    [
        {"620": {"success": False}},
        {"620": {"success": True, "data": {}}},
        {"620": {"data": {"price_overview": {}}}},
        {"620": {"data": {"price_overview": {"final": "no numerico"}}}},
        {},
    ],
)
def test_incomplete_details_yield_a_game_without_price(steam_http, details):
    steam_http["storesearch"] = Script(portal_search())
    steam_http["appdetails"] = Script(response(payload=details))

    games = repository().search("detalles incompletos")

    assert games[0].prices == {}
    assert games[0].links == {}


def test_malformed_details_payload_is_an_error(steam_http):
    steam_http["storesearch"] = Script(portal_search())
    steam_http["appdetails"] = Script(response(payload=["x"]))

    with pytest.raises(ExternalSourceError):
        repository().search("detalles invalidos")


def test_repeating_a_search_is_a_side_effect_free_read(steam_http):
    steam_http["storesearch"] = search = Script(portal_search())
    steam_http["appdetails"] = details = Script(portal_details())
    steam = repository()

    first = steam.search("Portal Repetida")
    first[0].prices["Steam"] = 1.0
    first[0].unavailable_sources.append("CheapShark")

    second = steam.search("  portal repetida ")

    # La segunda lectura sale de la caché: Steam no vuelve a consultarse.
    assert len(search.calls) == 1
    assert len(details.calls) == 1
    # El significado de la búsqueda se conserva y lo mutado no se filtra.
    assert [game.name for game in second] == ["Portal 2"]
    assert second[0].prices == {"Steam": 26.0}
    assert second[0].unavailable_sources == []


def test_a_failed_search_is_not_cached(steam_http):
    steam_http["storesearch"] = search = Script(
        response(403), portal_search()
    )
    steam_http["appdetails"] = Script(portal_details())
    steam = repository()

    with pytest.raises(ExternalSourceError):
        steam.search("no cachea errores")

    assert [g.name for g in steam.search("no cachea errores")] == ["Portal 2"]
    assert len(search.calls) == 2


# --- Endpoint GET /games/search: contrato bajo fallo ------------------------

RESULT_KEYS = {"id", "name", "prices", "unavailable_sources", "image", "links"}


def _steam_search_calls(script):
    return [call for call in script.calls if call["url"] == SEARCH_URL]


@pytest.mark.parametrize(
    "failure",
    [
        httpx.ReadTimeout("Steam lenta"),
        httpx.ConnectError("Steam caída"),
        response(503),
        response(429),
        response(403),
        response(content=b"no es json"),
    ],
)
def test_endpoint_reports_a_steam_failure_instead_of_a_silent_empty_search(
    steam_http, failure
):
    steam_http["storesearch"] = Script(failure)

    result = client.get("/games/search?q=Minecraft")

    assert result.status_code == 200

    data = result.json()

    # La caída de Steam no se disfraza de «sin resultados»: hay respaldo
    # y cada juego lleva el aviso en `unavailable_sources`.
    assert data
    assert all(set(item) == RESULT_KEYS for item in data)
    assert all("Steam" in item["unavailable_sources"] for item in data)


def test_endpoint_does_not_retry_a_permanent_4xx(steam_http):
    steam_http["storesearch"] = search = Script(response(403))

    assert client.get("/games/search?q=Minecraft").status_code == 200
    assert len(_steam_search_calls(search)) == 1


def test_endpoint_retries_a_transient_error_and_returns_steam_prices(
    steam_http,
):
    steam_http["storesearch"] = search = Script(
        response(503), portal_search()
    )
    steam_http["appdetails"] = Script(portal_details())

    data = client.get("/games/search?q=Portal 2 transitorio").json()

    assert len(_steam_search_calls(search)) == 2
    assert data[0]["name"] == "Portal 2"
    assert data[0]["prices"]["Steam"] == 26.0
    assert "Steam" not in data[0]["unavailable_sources"]
