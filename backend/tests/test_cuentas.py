"""
ADR-0017 — Inicio de sesión con Google y dispositivos del usuario.

Ninguna prueba habla con Google ni usa una base de datos: el proveedor de
identidad es simulado y las cuentas viven en memoria. Las mismas pruebas del
almacén corren contra PostgreSQL si existe `DRIFT_TEST_DATABASE_URL`.
"""

import base64
import json
import os
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import main
from app.application.usecases.accounts import Devices, Sessions, hash_token
from app.domain.model.account import Device, GoogleIdentity, InvalidDevice, PcSpecs
from app.domain.ports.identity_provider import (
    IdentityProvider,
    IdentityProviderUnavailable,
    IdentityRejected,
)
from app.infrastructure.api.account_routes import (
    SESSION_COOKIE,
    STATE_COOKIE,
    AccountSettings,
    build_account_router,
)
from app.infrastructure.external.google import google_identity_provider
from app.infrastructure.external.google.google_identity_provider import (
    GoogleIdentityProvider,
)
from app.infrastructure.persistence.in_memory_account_repository import (
    InMemoryAccountRepository,
)

ORIGIN = "http://localhost:3000"
NOW = datetime(2026, 11, 12, 12, 0, tzinfo=timezone.utc)
ANA = GoogleIdentity("google-ana", "ana@example.test", "Ana", "https://img.test/ana.png")
LUIS = GoogleIdentity("google-luis", "luis@example.test", "Luis")

PC_SPECS = {"ram_gb": 16, "gpu_score": 3, "gpu_name": "RTX 3060"}


class FakeGoogle(IdentityProvider):
    """Proveedor simulado: el código es el nombre de quien inicia sesión."""

    def __init__(self):
        self.people = {"ana": ANA, "luis": LUIS}
        self.nonces = []

    def authorization_url(self, state, nonce):
        return f"https://accounts.example.test/auth?state={state}&nonce={nonce}"

    def identify(self, code, nonce):
        self.nonces.append(nonce)

        if code == "caido":
            raise IdentityProviderUnavailable()

        if code not in self.people:
            raise IdentityRejected("code_rejected")

        return self.people[code]


# --- El almacén de cuentas (memoria y, si hay base de datos, PostgreSQL) -------

DATABASE_URL = os.getenv("DRIFT_TEST_DATABASE_URL", "").strip()


def _postgres_repository():
    from app.infrastructure.persistence.postgres_account_repository import (
        PostgresAccountRepository,
    )
    from app.infrastructure.persistence.postgres_database import PostgresDatabase

    database = PostgresDatabase(DATABASE_URL, acquire_timeout_seconds=5)

    with database.connection() as connection:
        connection.execute("TRUNCATE app_user CASCADE")

    return PostgresAccountRepository(database), database


@pytest.fixture(
    params=[
        "memoria",
        pytest.param(
            "postgres",
            marks=pytest.mark.skipif(
                not DATABASE_URL,
                reason="DRIFT_TEST_DATABASE_URL no está definida",
            ),
        ),
    ]
)
def accounts(request):
    if request.param == "memoria":
        yield InMemoryAccountRepository()
        return

    repository, database = _postgres_repository()

    yield repository

    database.close()


def pc(user, device_id="11111111-1111-4111-8111-111111111111", name="Mi PC"):
    return Device(
        id=device_id,
        user_id=user.id,
        name=name,
        kind="pc",
        specs=PcSpecs(**PC_SPECS),
        created_at=NOW,
    )


def test_signing_in_twice_keeps_one_account_and_refreshes_its_data(accounts):
    first = accounts.save_user(ANA)
    again = accounts.save_user(
        GoogleIdentity("google-ana", "ana.nueva@example.test", "Ana María")
    )

    assert again.id == first.id
    assert again.email == "ana.nueva@example.test"
    assert again.name == "Ana María"
    assert again.picture is None


def test_a_session_finds_its_user_until_it_expires(accounts):
    ana = accounts.save_user(ANA)

    accounts.create_session("huella-1", ana.id, NOW + timedelta(days=30))

    assert accounts.find_user_by_session("huella-1", NOW).email == ANA.email
    assert accounts.find_user_by_session("otra-huella", NOW) is None
    assert accounts.find_user_by_session("huella-1", NOW + timedelta(days=31)) is None

    accounts.delete_session("huella-1")

    assert accounts.find_user_by_session("huella-1", NOW) is None


def test_devices_belong_to_their_owner(accounts):
    ana = accounts.save_user(ANA)
    luis = accounts.save_user(LUIS)

    accounts.save_device(pc(ana))
    accounts.save_device(
        Device(
            id="22222222-2222-4222-8222-222222222222",
            user_id=ana.id,
            name="PS5 de la sala",
            kind="playstation",
            created_at=NOW + timedelta(minutes=1),
        )
    )

    devices = accounts.list_devices(ana.id)

    assert [device.name for device in devices] == ["Mi PC", "PS5 de la sala"]
    assert devices[0].specs == PcSpecs(**PC_SPECS)
    assert devices[1].specs is None
    assert accounts.list_devices(luis.id) == []

    # Otra persona no puede borrar ni sobrescribir un dispositivo ajeno.
    assert accounts.delete_device(luis.id, devices[0].id) is False

    accounts.save_device(pc(luis, device_id=devices[0].id, name="Robado"))

    assert accounts.list_devices(ana.id)[0].name == "Mi PC"


def test_saving_a_device_again_replaces_it(accounts):
    ana = accounts.save_user(ANA)

    accounts.save_device(pc(ana))
    accounts.save_device(pc(ana, name="PC de escritorio"))

    devices = accounts.list_devices(ana.id)

    assert [device.name for device in devices] == ["PC de escritorio"]
    assert accounts.delete_device(ana.id, devices[0].id) is True
    assert accounts.list_devices(ana.id) == []


def test_deleting_an_account_removes_everything_it_owned(accounts):
    ana = accounts.save_user(ANA)
    luis = accounts.save_user(LUIS)

    accounts.create_session("huella-ana", ana.id, NOW + timedelta(days=1))
    accounts.create_session("huella-luis", luis.id, NOW + timedelta(days=1))
    accounts.save_device(pc(ana))

    accounts.delete_user(ana.id)

    assert accounts.find_user_by_session("huella-ana", NOW) is None
    assert accounts.list_devices(ana.id) == []
    assert accounts.find_user_by_session("huella-luis", NOW).email == LUIS.email

    # Si vuelve a entrar, empieza con una cuenta nueva y vacía.
    assert accounts.save_user(ANA).id != ana.id


# --- Reglas de los dispositivos ------------------------------------------------


def test_a_pc_needs_its_specs_and_a_console_does_not_take_them():
    repository = InMemoryAccountRepository()
    ana = repository.save_user(ANA)
    devices = Devices(repository, now=lambda: NOW)

    saved = devices.add(ana, "  Mi PC  ", "pc", PC_SPECS)

    assert saved.name == "Mi PC"
    assert devices.add(ana, "Xbox", "xbox", None).specs is None

    for name, kind, specs in [
        ("Mi PC", "pc", None),
        ("Xbox", "xbox", PC_SPECS),
        ("Switch", "switch", None),
        ("", "xbox", None),
        ("x" * 41, "xbox", None),
        ("Mi PC", "pc", {"ram_gb": 0, "gpu_score": 3}),
        ("Mi PC", "pc", {"ram_gb": 16, "gpu_score": True}),
        ("Mi PC", "pc", {"ram_gb": 16, "gpu_score": 3, "campo_raro": 1}),
        ("Mi PC", "pc", {"ram_gb": 16, "gpu_score": 3, "gpu_name": "x" * 121}),
    ]:
        with pytest.raises(InvalidDevice):
            devices.add(ana, name, kind, specs)

    assert len(devices.list(ana)) == 2


def test_a_user_cannot_register_devices_without_limit():
    repository = InMemoryAccountRepository()
    ana = repository.save_user(ANA)
    devices = Devices(repository, now=lambda: NOW)

    for number in range(10):
        devices.add(ana, f"Consola {number}", "xbox", None)

    with pytest.raises(InvalidDevice):
        devices.add(ana, "Una más", "xbox", None)


# --- Sesiones ------------------------------------------------------------------


def test_only_the_hash_of_the_session_token_is_stored():
    repository = InMemoryAccountRepository()
    sessions = Sessions(repository, FakeGoogle(), now=lambda: NOW)

    session = sessions.complete("ana", "nonce")

    assert session["token"] not in repository._sessions
    assert hash_token(session["token"]) in repository._sessions
    assert session["expires_at"] == NOW + timedelta(days=30)
    assert sessions.current_user(session["token"]).email == ANA.email
    assert sessions.current_user("token-inventado") is None
    assert sessions.current_user(None) is None


def test_each_login_attempt_gets_its_own_state_and_nonce():
    sessions = Sessions(InMemoryAccountRepository(), FakeGoogle())

    first, second = sessions.begin(), sessions.begin()

    assert first["state"] != second["state"]
    assert first["nonce"] != second["nonce"]
    assert len(first["state"]) >= 32
    assert first["state"] in first["url"]


# --- El adaptador de Google ----------------------------------------------------

CLIENT_ID = "cliente-de-prueba.apps.googleusercontent.com"


def id_token(**changes):
    claims = {
        "iss": "https://accounts.google.com",
        "aud": CLIENT_ID,
        "exp": NOW.timestamp() + 3600,
        "nonce": "nonce-esperado",
        "sub": "google-ana",
        "email": "ana@example.test",
        "email_verified": True,
        "name": "Ana",
        "picture": "https://img.test/ana.png",
    }
    claims.update(changes)

    payload = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode()

    return f"cabecera.{payload.rstrip('=')}.firma"


@pytest.fixture
def google(monkeypatch):
    """Simula el intercambio del código en el servidor de Google."""

    outcome = {"response": None, "calls": []}

    def fake_post(url, data=None, timeout=None):
        outcome["calls"].append({"url": url, "data": data})

        if isinstance(outcome["response"], Exception):
            raise outcome["response"]

        return outcome["response"]

    monkeypatch.setattr(google_identity_provider.httpx, "post", fake_post)

    return outcome


def provider():
    return GoogleIdentityProvider(
        CLIENT_ID,
        "secreto-de-prueba",
        "http://localhost:8000/auth/google/callback",
        clock=lambda: NOW.timestamp(),
    )


def _token_response(token, status_code=200):
    return httpx.Response(
        status_code,
        json={"id_token": token} if token is not None else {"error": "invalid_grant"},
        request=httpx.Request("POST", "https://oauth2.googleapis.com/token"),
    )


def test_google_login_asks_only_for_identity_email_and_profile():
    url = urlparse(provider().authorization_url("estado", "nonce"))
    query = parse_qs(url.query)

    assert url.netloc == "accounts.google.com"
    assert query["scope"] == ["openid email profile"]
    assert query["response_type"] == ["code"]
    assert query["state"] == ["estado"]
    assert query["nonce"] == ["nonce"]
    assert query["redirect_uri"] == ["http://localhost:8000/auth/google/callback"]
    assert "client_secret" not in url.query


def test_google_identity_is_read_from_a_valid_token(google):
    google["response"] = _token_response(id_token())

    identity = provider().identify("codigo", "nonce-esperado")

    assert identity == GoogleIdentity(
        "google-ana", "ana@example.test", "Ana", "https://img.test/ana.png"
    )
    assert google["calls"][0]["data"]["grant_type"] == "authorization_code"


@pytest.mark.parametrize(
    "changes",
    [
        {"iss": "https://sitio-falso.example"},
        {"aud": "otro-cliente.apps.googleusercontent.com"},
        {"exp": NOW.timestamp() - 1},
        {"nonce": "nonce-de-otro-intento"},
        {"email_verified": False},
        {"sub": ""},
    ],
)
def test_google_token_that_does_not_match_is_rejected(google, changes):
    google["response"] = _token_response(id_token(**changes))

    with pytest.raises(IdentityRejected):
        provider().identify("codigo", "nonce-esperado")


@pytest.mark.parametrize("token", ["no-es-un-token", "a.b.c", None])
def test_google_malformed_or_rejected_answer_is_rejected(google, token):
    google["response"] = _token_response(token, 200 if token else 400)

    with pytest.raises(IdentityRejected):
        provider().identify("codigo", "nonce-esperado")


def test_google_outage_is_reported_as_unavailable(google):
    google["response"] = httpx.ConnectError("sin conexión")

    with pytest.raises(IdentityProviderUnavailable):
        provider().identify("codigo", "nonce-esperado")

    google["response"] = _token_response(None, 503)

    with pytest.raises(IdentityProviderUnavailable):
        provider().identify("codigo", "nonce-esperado")


# --- La API --------------------------------------------------------------------


@pytest.fixture
def api():
    repository = InMemoryAccountRepository()
    fake_google = FakeGoogle()
    app = FastAPI()
    app.include_router(
        build_account_router(
            Sessions(repository, fake_google),
            Devices(repository),
            AccountSettings(
                frontend_url=ORIGIN,
                allowed_origins=[ORIGIN],
                secure_cookies=False,
            ),
        )
    )

    client = TestClient(app, follow_redirects=False)
    client.google = fake_google
    client.repository = repository

    return client


def sign_in(client, who="ana"):
    start = client.get("/auth/google/login")
    state = parse_qs(urlparse(start.headers["location"]).query)["state"][0]

    return client.get(f"/auth/google/callback?code={who}&state={state}")


TRUSTED = {"Origin": ORIGIN}


def test_login_sends_the_person_to_google_and_back_with_a_session(api):
    assert api.get("/auth/me").json() == {
        "login_available": True,
        "authenticated": False,
        "user": None,
    }

    start = api.get("/auth/google/login")

    assert start.status_code == 303
    assert start.headers["location"].startswith("https://accounts.example.test/auth")

    state_cookie = start.headers.get_list("set-cookie")[0].lower()

    assert "httponly" in state_cookie
    assert "samesite=lax" in state_cookie

    done = sign_in(api)

    assert done.status_code == 303
    assert done.headers["location"] == f"{ORIGIN}?login=ok"

    session_cookie = next(
        cookie
        for cookie in done.headers.get_list("set-cookie")
        if cookie.startswith(SESSION_COOKIE)
    ).lower()

    assert "httponly" in session_cookie
    assert "samesite=lax" in session_cookie

    me = api.get("/auth/me").json()

    assert me["authenticated"] is True
    assert me["user"] == {
        "name": "Ana",
        "email": "ana@example.test",
        "picture": "https://img.test/ana.png",
    }

    # El `nonce` que recibe Google es el de este intento.
    assert api.google.nonces[-1]


def test_login_is_rejected_without_the_state_this_browser_received(api):
    api.get("/auth/google/login")

    forged = api.get("/auth/google/callback?code=ana&state=estado-de-otro-sitio")

    assert forged.headers["location"] == f"{ORIGIN}?login=error"
    assert api.get("/auth/me").json()["authenticated"] is False

    # Sin haber empezado el inicio de sesión en este navegador tampoco.
    fresh = TestClient(api.app, follow_redirects=False)
    direct = fresh.get("/auth/google/callback?code=ana&state=cualquiera")

    assert direct.headers["location"] == f"{ORIGIN}?login=error"
    assert api.google.nonces == []


def test_login_reports_a_rejected_code_and_a_google_outage(api):
    assert sign_in(api, "desconocido").headers["location"] == f"{ORIGIN}?login=error"
    assert sign_in(api, "caido").headers["location"] == f"{ORIGIN}?login=unavailable"
    assert api.get("/auth/me").json()["authenticated"] is False


def test_logout_ends_the_session(api):
    sign_in(api)

    assert api.post("/auth/logout", headers=TRUSTED).status_code == 200
    assert api.get("/auth/me").json()["authenticated"] is False
    assert api.repository._sessions == {}


def test_devices_need_a_session(api):
    assert api.get("/devices").status_code == 401
    assert (
        api.post(
            "/devices",
            json={"name": "Xbox", "kind": "xbox"},
            headers=TRUSTED,
        ).status_code
        == 401
    )


def test_a_user_manages_their_devices(api):
    sign_in(api)

    created = api.post(
        "/devices",
        json={"name": "Mi PC", "kind": "pc", "specs": PC_SPECS},
        headers=TRUSTED,
    )

    assert created.status_code == 201

    device = created.json()

    assert device["name"] == "Mi PC"
    assert device["specs"]["ram_gb"] == 16
    assert "user_id" not in device

    api.post("/devices", json={"name": "PS5", "kind": "playstation"}, headers=TRUSTED)

    assert [item["kind"] for item in api.get("/devices").json()] == [
        "pc",
        "playstation",
    ]

    updated = api.put(
        f"/devices/{device['id']}",
        json={"name": "PC nuevo", "kind": "pc", "specs": {**PC_SPECS, "ram_gb": 32}},
        headers=TRUSTED,
    )

    assert updated.json()["specs"]["ram_gb"] == 32
    assert api.delete(f"/devices/{device['id']}", headers=TRUSTED).status_code == 200
    assert api.delete(f"/devices/{device['id']}", headers=TRUSTED).status_code == 404
    assert [item["name"] for item in api.get("/devices").json()] == ["PS5"]


def test_invalid_devices_are_rejected_with_a_reason(api):
    sign_in(api)

    missing_specs = api.post(
        "/devices",
        json={"name": "Mi PC", "kind": "pc"},
        headers=TRUSTED,
    )

    assert missing_specs.status_code == 422
    assert missing_specs.json()["detail"]["reason"] == "invalid_device"

    assert (
        api.post(
            "/devices",
            json={"name": "Switch", "kind": "switch"},
            headers=TRUSTED,
        ).status_code
        == 422
    )


def test_one_user_cannot_touch_the_devices_of_another(api):
    sign_in(api, "ana")
    device = api.post(
        "/devices",
        json={"name": "PC de Ana", "kind": "pc", "specs": PC_SPECS},
        headers=TRUSTED,
    ).json()

    luis = TestClient(api.app, follow_redirects=False)
    sign_in(luis, "luis")

    assert luis.get("/devices").json() == []
    assert luis.delete(f"/devices/{device['id']}", headers=TRUSTED).status_code == 404
    assert (
        luis.put(
            f"/devices/{device['id']}",
            json={"name": "Mío", "kind": "xbox"},
            headers=TRUSTED,
        ).status_code
        == 404
    )
    assert api.get("/devices").json()[0]["name"] == "PC de Ana"


@pytest.mark.parametrize("headers", [{}, {"Origin": "https://sitio-malicioso.example"}])
def test_changes_from_another_site_are_refused(api, headers):
    sign_in(api)

    assert (
        api.post(
            "/devices",
            json={"name": "Xbox", "kind": "xbox"},
            headers=headers,
        ).status_code
        == 403
    )
    assert api.post("/auth/logout", headers=headers).status_code == 403
    assert api.delete("/auth/me", headers=headers).status_code == 403
    assert api.get("/auth/me").json()["authenticated"] is True


def test_deleting_the_account_removes_the_user_and_their_devices(api):
    sign_in(api)
    api.post("/devices", json={"name": "Xbox", "kind": "xbox"}, headers=TRUSTED)

    assert api.delete("/auth/me", headers=TRUSTED).json() == {"deleted": True}
    assert api.get("/auth/me").json()["authenticated"] is False
    assert api.repository._users == {}
    assert api.repository._devices == {}
    assert api.repository._sessions == {}


def test_a_failing_account_store_answers_unavailable_not_a_crash(api):
    sign_in(api)

    def broken(*args, **kwargs):
        raise ConnectionError("base de datos caída")

    api.repository.list_devices = broken

    response = api.get("/devices")

    assert response.status_code == 503
    assert response.json()["detail"]["reason"] == "accounts_unavailable"


def test_without_a_google_client_login_is_off_and_the_rest_keeps_working():
    app = FastAPI()
    app.include_router(
        build_account_router(
            None,
            None,
            AccountSettings(ORIGIN, [ORIGIN], secure_cookies=False),
        )
    )
    client = TestClient(app, follow_redirects=False)

    assert client.get("/auth/me").json() == {
        "login_available": False,
        "authenticated": False,
        "user": None,
    }
    assert client.get("/auth/google/login").status_code == 404
    assert client.get("/devices").status_code == 404


def test_the_real_app_exposes_the_account_routes():
    # En las pruebas no hay cliente de Google configurado.
    response = TestClient(main.app).get("/auth/me")

    assert response.status_code == 200
    assert response.json()["authenticated"] is False


def test_the_state_cookie_name_is_not_the_session_cookie():
    assert STATE_COOKIE != SESSION_COOKIE
