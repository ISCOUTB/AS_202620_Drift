"""
S13 — Mitigaciones del modelo de amenazas (docs/seguridad/modelo-amenazas.md).

A2/A5: operaciones administrativas protegidas con token (ADR-0011).
A3: límite de tasa en las rutas que llaman a fuentes externas (ADR-0012).
A9: CORS sin credenciales y con métodos acotados.
A10: registro de las sincronizaciones administrativas.

Ninguna prueba usa la red.
"""

import logging

from fastapi.testclient import TestClient

from tests.admin_auth import ADMIN_HEADERS

from app import main
from app.infrastructure.api.security import SlidingWindowRateLimiter, client_ip

client = TestClient(main.app)


# --- A2 y A5: token administrativo -------------------------------------------

def test_sync_without_token_is_rejected_and_does_not_call_the_source(monkeypatch):
    called = []
    monkeypatch.setattr(
        main.sync_playstation_catalog, "execute", lambda: called.append(True)
    )

    response = client.post("/games/sync/playstation")

    assert response.status_code == 401
    assert response.json()["detail"]["reason"] == "invalid_admin_token"
    assert response.headers["www-authenticate"] == "Bearer"
    assert called == []


def test_sync_with_a_wrong_token_is_rejected(monkeypatch):
    monkeypatch.setattr(main.sync_playstation_catalog, "execute", lambda: {})

    response = client.post(
        "/games/sync/playstation",
        headers={"Authorization": "Bearer otro-token"},
    )

    assert response.status_code == 401


def test_sync_is_disabled_when_the_server_has_no_token(monkeypatch):
    monkeypatch.delenv("DRIFT_ADMIN_TOKEN", raising=False)
    monkeypatch.setattr(main.sync_playstation_catalog, "execute", lambda: {})

    response = client.post("/games/sync/playstation", headers=ADMIN_HEADERS)

    assert response.status_code == 403
    assert response.json()["detail"]["reason"] == "admin_operation_disabled"


def test_sync_with_the_right_token_runs(monkeypatch):
    monkeypatch.setattr(
        main.sync_playstation_catalog,
        "execute",
        lambda: {"status": "ok", "games_loaded": 3},
    )

    response = client.post("/games/sync/playstation", headers=ADMIN_HEADERS)

    assert response.status_code == 200
    assert response.json()["games_loaded"] == 3


def test_metrics_require_the_admin_token():
    assert client.get("/metrics").status_code == 401
    assert client.get("/metrics", headers=ADMIN_HEADERS).status_code == 200


def test_public_endpoints_do_not_need_a_token():
    assert client.get("/health").status_code == 200
    assert client.get("/hardware/gpus").status_code == 200


# --- A10: registro de la sincronización --------------------------------------

def test_authorized_sync_is_logged_with_its_origin(monkeypatch, caplog):
    monkeypatch.setattr(
        main.sync_playstation_catalog,
        "execute",
        lambda: {"status": "ok", "games_loaded": 2},
    )
        # caplog solo ve los registros que se propagan al logger raíz.
    monkeypatch.setattr(main.logger, "propagate", True)

    with caplog.at_level(logging.INFO, logger="drift"):
        client.post("/games/sync/playstation", headers=ADMIN_HEADERS)

    events = {record.getMessage(): record for record in caplog.records}

    assert "admin_catalog_sync_requested" in events
    assert events["admin_catalog_sync_requested"].fields["client_ip"] == "testclient"
    assert events["admin_catalog_sync_completed"].fields["games_loaded"] == 2


# --- A3: límite de tasa -------------------------------------------------------

class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


def test_limiter_allows_up_to_the_limit_and_then_rejects():
    clock = FakeClock()
    limiter = SlidingWindowRateLimiter(limit=3, window_seconds=60, clock=clock)

    assert [limiter.check("1.2.3.4")[0] for _ in range(3)] == [True, True, True]

    allowed, retry_after = limiter.check("1.2.3.4")
    assert allowed is False
    assert 1 <= retry_after <= 61


def test_limiter_counts_each_client_separately():
    limiter = SlidingWindowRateLimiter(limit=1, clock=FakeClock())

    assert limiter.check("1.1.1.1")[0] is True
    assert limiter.check("2.2.2.2")[0] is True
    assert limiter.check("1.1.1.1")[0] is False


def test_limiter_frees_the_slot_when_the_window_passes():
    clock = FakeClock()
    limiter = SlidingWindowRateLimiter(limit=1, window_seconds=60, clock=clock)

    assert limiter.check("cliente")[0] is True
    assert limiter.check("cliente")[0] is False

    clock.now += 61

    assert limiter.check("cliente")[0] is True


def test_limiter_with_zero_does_not_limit():
    limiter = SlidingWindowRateLimiter(limit=0)

    assert all(limiter.check("cliente")[0] for _ in range(500))


def test_search_answers_429_with_retry_after_once_the_limit_is_reached(monkeypatch):
    monkeypatch.setattr(main.rate_limiter, "limit", 2)
    monkeypatch.setattr(main.rate_limiter, "_hits", {})
    monkeypatch.setattr(
        main.search_games,
        "execute",
        lambda query, platforms=None: [],
    )

    statuses = [
        client.get("/games/search", params={"q": "portal"}).status_code
        for _ in range(3)
    ]

    assert statuses == [200, 200, 429]

    response = client.get("/games/search", params={"q": "portal"})
    assert response.json()["detail"]["reason"] == "rate_limited"
    assert int(response.headers["retry-after"]) >= 1


def test_rate_limit_does_not_apply_to_health_or_hardware(monkeypatch):
    monkeypatch.setattr(main.rate_limiter, "limit", 1)
    monkeypatch.setattr(main.rate_limiter, "_hits", {})

    assert all(client.get("/health").status_code == 200 for _ in range(5))
    assert all(client.get("/hardware/cpus").status_code == 200 for _ in range(5))


def test_client_ip_ignores_forwarded_for_unless_the_proxy_is_trusted(monkeypatch):
    class FakeRequest:
        headers = {"x-forwarded-for": "6.6.6.6, 9.9.9.9"}

        class client:
            host = "10.0.0.1"

    monkeypatch.delenv("DRIFT_TRUST_FORWARDED_FOR", raising=False)
    assert client_ip(FakeRequest) == "10.0.0.1"

    monkeypatch.setenv("DRIFT_TRUST_FORWARDED_FOR", "true")
    # La última entrada la agrega el proxy; la primera la puede inventar el cliente.
    assert client_ip(FakeRequest) == "9.9.9.9"


def test_client_ip_drops_the_port_some_proxies_add(monkeypatch):
    monkeypatch.setenv("DRIFT_TRUST_FORWARDED_FOR", "true")

    def request_from(forwarded):
        class FakeRequest:
            headers = {"x-forwarded-for": forwarded}
            client = None

        return FakeRequest

    assert client_ip(request_from("1.2.3.4:51234")) == "1.2.3.4"
    assert client_ip(request_from("[2001:db8::1]:443")) == "2001:db8::1"
    assert client_ip(request_from("2001:db8::1")) == "2001:db8::1"


# --- A9: CORS -----------------------------------------------------------------

def test_cors_allows_credentials_only_for_the_configured_origin():
    # ADR-0017 modifica a ADR-0012: la sesión viaja en una cookie, así que el
    # origen configurado puede enviar credenciales. Nunca se combina con «*».
    origin = main.allowed_origins[0]

    response = client.options(
        "/games/1/compatibility",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
    assert response.headers["access-control-allow-credentials"] == "true"
    assert "*" not in main.allowed_origins
    assert "PATCH" not in response.headers["access-control-allow-methods"]


def test_cors_rejects_unknown_origins():
    response = client.options(
        "/games/search",
        headers={
            "Origin": "https://sitio-malicioso.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert "access-control-allow-origin" not in response.headers
