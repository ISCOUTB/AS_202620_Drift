"""
IsThereAnyDeal: precios de las tiendas de PC, control de cuota e historial.

Ninguna prueba usa la red ni una llave real: `httpx.get` y `httpx.post` se
reemplazan por respuestas con la forma que entrega la API.
"""

from datetime import datetime, timedelta, timezone

import httpx
import pytest
from fastapi.testclient import TestClient

from app import main
from app.application.usecases.get_price_history import GetPriceHistory
from app.domain.model.price_history import PriceChange
from app.domain.ports.exchange_rate_provider import ExchangeRateProvider
from app.domain.services.price_timeline import best_price_timeline, lowest_point
from app.infrastructure.external.isthereanydeal import itad_client
from app.infrastructure.external.isthereanydeal.itad_client import ItadClient
from app.infrastructure.external.isthereanydeal.itad_game_repository import (
    ItadGameRepository,
)
from app.infrastructure.external.isthereanydeal.itad_price_history_repository import (
    ItadPriceHistoryRepository,
)
from app.infrastructure.external.resilient_http import (
    ExternalSourceError,
    RetryPolicy,
)
from app.infrastructure.persistence.in_memory_source_snapshot_store import (
    InMemorySourceSnapshotStore,
)
from app.infrastructure.persistence.stale_fallback_game_repository import (
    StaleFallbackGameRepository,
)

API_KEY = "llave-de-prueba"
POLICY = RetryPolicy(timeout_seconds=3.0, max_attempts=2, backoff_base_seconds=0.0)
NOW = datetime(2026, 11, 12, 12, 0, tzinfo=timezone.utc)

ELDEN = "018d937f-590c-728b-ac35-38bcff85f086"
PORTAL = "018d937f-21e1-728e-86d7-9acb3c59f2bb"


class FixedRate(ExchangeRateProvider):
    def usd_to_cop(self) -> float:
        return 4000.0


def _response(payload, status_code=200, headers=None):
    return httpx.Response(
        status_code,
        json=payload,
        headers=headers,
        request=httpx.Request("GET", "https://example.test"),
    )


def usd(amount):
    return {"amount": amount, "amountInt": round(amount * 100), "currency": "USD"}


def deal(shop, amount, regular=None, cut=0, url="https://itad.link/x/"):
    return {
        "shop": {"id": 1, "name": shop},
        "price": usd(amount),
        "regular": usd(amount if regular is None else regular),
        "cut": cut,
        "url": url,
    }


def title(game_id, name):
    return {
        "id": game_id,
        "title": name,
        "type": "game",
        "assets": {"banner400": f"https://assets.test/{game_id}.jpg"},
    }


def change(when, shop, amount, cut=0):
    return {
        "timestamp": when,
        "shop": {"id": 1, "name": shop},
        "deal": {"price": usd(amount), "regular": usd(60), "cut": cut},
    }


@pytest.fixture
def itad_http(monkeypatch):
    """Rutas simuladas por fragmento de URL; registra cada llamada."""

    routes = {}
    calls = []

    def answer(url, kwargs):
        calls.append({"url": url, **kwargs})

        for key, outcome in routes.items():
            if key in url:
                if isinstance(outcome, list) and outcome and isinstance(
                    outcome[0], (httpx.Response, Exception)
                ):
                    outcome = outcome.pop(0) if len(outcome) > 1 else outcome[0]

                if isinstance(outcome, Exception):
                    raise outcome

                return outcome

        raise httpx.ConnectError(f"ruta no simulada: {url}")

    monkeypatch.setattr(
        itad_client.httpx, "get", lambda url, **kwargs: answer(url, kwargs)
    )
    monkeypatch.setattr(
        itad_client.httpx, "post", lambda url, **kwargs: answer(url, kwargs)
    )

    routes["calls"] = calls

    return routes


def client(**options):
    return ItadClient(API_KEY, policy=POLICY, sleep=lambda _: None, **options)


# --- Precios de las tiendas de PC ----------------------------------------------


def test_search_returns_pc_stores_in_pesos_with_discount_and_link(itad_http):
    itad_http["/games/search/v1"] = _response([title(ELDEN, "Elden Ring")])
    itad_http["/games/prices/v3"] = _response(
        [
            {
                "id": ELDEN,
                "deals": [
                    deal("GameBillet", 52.69, 59.99, 12, "https://itad.link/gb/"),
                    deal("Humble Store", 59.99),
                    # Steam y Microsoft Store ya se consultan directamente.
                    deal("Steam", 59.99),
                    deal("Microsoft Store", 59.99),
                ],
            }
        ]
    )

    games = ItadGameRepository(client(), FixedRate()).search("elden ring")

    assert len(games) == 1
    assert games[0].id == f"itad-{ELDEN}"
    assert games[0].name == "Elden Ring"
    assert games[0].prices == {"GameBillet": 210760.0, "Humble Store": 239960.0}
    assert games[0].discounts == {"GameBillet": 12}
    assert games[0].links["GameBillet"] == "https://itad.link/gb/"
    assert games[0].image == f"https://assets.test/{ELDEN}.jpg"
    assert games[0].platforms == ["PC"]

    search_call, prices_call = itad_http["calls"]

    # La llave viaja en la cabecera, nunca en la URL.
    assert search_call["headers"]["ITAD-API-Key"] == API_KEY
    assert API_KEY not in search_call["url"]
    assert "key" not in search_call["params"]

    # Todos los juegos se piden en una sola llamada.
    assert prices_call["json"] == [ELDEN]
    assert prices_call["params"]["country"] == "CO"


def test_search_asks_for_all_prices_in_one_call_and_keeps_the_order(itad_http):
    itad_http["/games/search/v1"] = _response(
        [title(ELDEN, "Elden Ring"), title(PORTAL, "Portal 2"), "basura"]
    )
    itad_http["/games/prices/v3"] = _response(
        [
            {"id": PORTAL, "deals": [deal("GOG", 9.99)]},
            {"id": ELDEN, "deals": [deal("GOG", 59.99)]},
            {"id": "otro", "deals": [deal("GOG", 1.0)]},
        ]
    )

    games = ItadGameRepository(client(), FixedRate()).search("x")

    assert [game.name for game in games] == ["Elden Ring", "Portal 2"]
    assert len(itad_http["calls"]) == 2


def test_a_game_without_usable_offers_is_left_out(itad_http):
    itad_http["/games/search/v1"] = _response([title(ELDEN, "Elden Ring")])
    itad_http["/games/prices/v3"] = _response(
        [
            {
                "id": ELDEN,
                "deals": [
                    deal("Steam", 59.99),
                    {"shop": {"name": "GOG"}, "price": {"amount": 5, "currency": "EUR"}},
                    {"shop": {"name": "GOG"}, "price": {"amount": True, "currency": "USD"}},
                    "no es una oferta",
                ],
            }
        ]
    )

    assert ItadGameRepository(client(), FixedRate()).search("elden ring") == []


def test_no_results_needs_a_single_call(itad_http):
    itad_http["/games/search/v1"] = _response([])

    assert ItadGameRepository(client(), FixedRate()).search("zzzz") == []
    assert len(itad_http["calls"]) == 1


@pytest.mark.parametrize("payload", [{}, {"error": "x"}, "texto"])
def test_an_unexpected_answer_is_a_failure_not_an_empty_result(itad_http, payload):
    itad_http["/games/search/v1"] = _response(payload)

    games = ItadGameRepository(client(), FixedRate())

    with pytest.raises(ExternalSourceError) as error:
        games.search("elden ring")

    assert error.value.reason == "invalid_response"


# --- Control de cuota ----------------------------------------------------------


def test_calls_stop_before_reaching_the_limit_of_the_source(itad_http):
    itad_http["/games/search/v1"] = _response([])
    ticks = [0.0]
    limited = client(quota_limit=3, monotonic=lambda: ticks[0])

    for _ in range(3):
        limited.get("/games/search/v1", {"title": "x"})

    # La cuarta no sale a la red: falla como «sin cuota».
    with pytest.raises(ExternalSourceError) as error:
        limited.get("/games/search/v1", {"title": "x"})

    assert error.value.reason == "rate_limited"
    assert len(itad_http["calls"]) == 3
    assert limited.quota_snapshot()["calls_in_window"] == 3

    # Pasada la ventana de 5 minutos vuelve a llamar.
    ticks[0] = 301.0
    limited.get("/games/search/v1", {"title": "x"})

    assert len(itad_http["calls"]) == 4


def test_after_a_429_the_source_is_left_alone_for_a_while(itad_http):
    itad_http["/games/search/v1"] = _response({}, status_code=429)
    ticks = [0.0]
    paused = client(pause_seconds=60, monotonic=lambda: ticks[0])

    with pytest.raises(ExternalSourceError):
        paused.get("/games/search/v1", {"title": "x"})

    calls_after_429 = len(itad_http["calls"])

    with pytest.raises(ExternalSourceError) as error:
        paused.get("/games/search/v1", {"title": "x"})

    assert error.value.reason == "rate_limited"
    assert len(itad_http["calls"]) == calls_after_429
    assert paused.quota_snapshot()["paused"] is True

    ticks[0] = 61.0
    itad_http["/games/search/v1"] = _response([])

    assert paused.get("/games/search/v1", {"title": "x"}) == []


def test_without_quota_the_search_answers_from_its_backup(itad_http):
    itad_http["/games/search/v1"] = _response([title(ELDEN, "Elden Ring")])
    itad_http["/games/prices/v3"] = _response(
        [{"id": ELDEN, "deals": [deal("GOG", 59.99)]}]
    )
    ticks = [0.0]
    moment = [NOW]
    limited = client(quota_limit=2, monotonic=lambda: ticks[0])
    repository = StaleFallbackGameRepository(
        ItadGameRepository(limited, FixedRate()),
        "IsThereAnyDeal",
        InMemorySourceSnapshotStore(),
        fresh_seconds=900,
        stale_seconds=259200,
        now=lambda: moment[0],
    )

    repository.search("elden ring")

    # Una hora después (otra búsqueda ya gastó la cuota de la ventana).
    moment[0] = NOW + timedelta(hours=1)
    ticks[0] = 100.0
    limited._calls.extend([100.0, 100.0])
    repository._repository._cache._entries.clear()

    games = repository.search("elden ring")

    assert games[0].prices == {"GOG": 239960.0}
    assert games[0].cached_sources == {"IsThereAnyDeal": NOW.isoformat()}
    assert len(itad_http["calls"]) == 2


# --- La línea del mejor precio -------------------------------------------------


def at(day, store, price, discount=0):
    return PriceChange(
        date=datetime(2026, 1, day, tzinfo=timezone.utc),
        store=store,
        price=price,
        discount=discount,
    )


def test_timeline_follows_the_cheapest_store_at_each_moment():
    timeline = best_price_timeline(
        [
            at(5, "GOG", 50.0, 50),
            at(1, "GOG", 100.0),
            at(3, "Humble", 80.0, 20),
            # La oferta de GOG termina: Humble vuelve a ser la más barata.
            at(9, "GOG", 100.0),
            # Sube una tienda que no era la más barata: no hay punto nuevo.
            at(10, "GOG", 120.0),
        ]
    )

    assert [(point.date.day, point.store, point.price) for point in timeline] == [
        (1, "GOG", 100.0),
        (3, "Humble", 80.0),
        (5, "GOG", 50.0),
        (9, "Humble", 80.0),
    ]
    assert timeline[2].discount == 50
    assert lowest_point(timeline).price == 50.0
    assert best_price_timeline([]) == []
    assert lowest_point([]) is None


# --- Historial de precios ------------------------------------------------------


def history_repository(http_client=None):
    return ItadPriceHistoryRepository(
        http_client or client(),
        FixedRate(),
        now=lambda: NOW,
    )


def test_history_of_a_steam_game_ends_at_todays_best_price(itad_http):
    itad_http["/lookup/id/shop/61/v1"] = _response({"app/1245620": ELDEN})
    itad_http["/games/history/v2"] = _response(
        [
            # Llegan del más reciente al más antiguo.
            change("2026-09-01T10:00:00+02:00", "GameBillet", 52.0, 12),
            change("2026-07-22T10:00:00+02:00", "2game", 31.0, 48),
            change("2026-03-19T20:41:37+01:00", "GameBillet", 28.0, 53),
            change("2026-03-19T18:00:00+01:00", "Steam", 38.99, 35),
            change("2026-01-10T10:00:00+01:00", "GameBillet", 55.0, 8),
            {"timestamp": "no es una fecha", "shop": {"name": "GOG"}},
            "basura",
        ]
    )
    itad_http["/games/prices/v3"] = _response(
        [{"id": ELDEN, "deals": [deal("GameBillet", 52.0, 59.99, 12), deal("Steam", 59.99)]}]
    )

    history = history_repository().get("1245620")

    # 2game ya no vende el juego: su oferta de julio no figura como precio
    # actual, pero sí cuenta para el más bajo registrado.
    assert [(p.store, p.price) for p in history.points] == [
        ("GameBillet", 220000.0),
        ("GameBillet", 112000.0),
        ("GameBillet", 208000.0),
    ]
    assert history.current.price == 208000.0
    assert history.lowest.store == "GameBillet"
    assert history.lowest.price == 112000.0
    assert history.lowest.date == datetime(2026, 3, 19, 19, 41, 37, tzinfo=timezone.utc)

    # El importe de Steam en dólares no se usa; su descuento sí.
    assert history.steam_best_discount.discount == 35
    assert history.since == NOW - timedelta(days=365)
    assert history.cached_at is None


def test_steam_enters_the_history_in_pesos_using_its_regional_price(itad_http):
    itad_http["/lookup/id/shop/61/v1"] = _response({"app/620": PORTAL})
    itad_http["/games/history/v2"] = _response(
        [
            change("2026-10-08T19:00:00+02:00", "Steam", 9.99, 0),
            change("2026-10-01T19:00:00+02:00", "Steam", 1.99, 80),
            change("2026-06-01T19:00:00+02:00", "Steam", 9.99, 0),
        ]
    )
    # Un juego que solo se vende en Steam: sin otras tiendas de PC.
    itad_http["/games/prices/v3"] = _response(
        [{"id": PORTAL, "deals": [deal("Steam", 9.99)]}]
    )
    asked = []

    def steam_prices(app_id):
        asked.append(app_id)
        # Precio normal, precio de hoy y descuento en Colombia.
        return (24499.0, 24499.0, 0)

    history = ItadPriceHistoryRepository(
        client(),
        FixedRate(),
        now=lambda: NOW,
        steam_prices=steam_prices,
    ).get("620")

    # Se usa el precio de Colombia con el descuento de cada fecha, no los
    # 9,99 dólares convertidos (que serían 39.960).
    assert asked == ["620"]
    assert [(p.store, p.price, p.discount) for p in history.points] == [
        ("Steam", 24499.0, 0),
        ("Steam", 4899.8, 80),
        ("Steam", 24499.0, 0),
    ]
    assert history.lowest.price == 4899.8
    assert history.current.price == 24499.0


def test_steam_is_found_for_a_game_that_did_not_come_from_steam(itad_http):
    itad_http["/lookup/shop/61/id/v1"] = _response(
        {ELDEN: ["sub/432247", "app/1245620"]}
    )
    itad_http["/games/history/v2"] = _response(
        [change("2026-09-01T10:00:00+02:00", "Steam", 35.99, 40)]
    )
    itad_http["/games/prices/v3"] = _response(
        [{"id": ELDEN, "deals": [deal("GOG", 59.99)]}]
    )
    asked = []

    history = ItadPriceHistoryRepository(
        client(),
        FixedRate(),
        now=lambda: NOW,
        steam_prices=lambda app_id: asked.append(app_id) or (201900.0, 201900.0, 0),
    ).get(f"itad-{ELDEN}")

    assert asked == ["1245620"]
    assert history.lowest.store == "Steam"
    assert history.lowest.price == 121140.0
    # Hoy Steam (201.900) es más barato que GOG (239.960).
    assert history.current.store == "Steam"


def test_history_works_without_steam_when_steam_does_not_answer(itad_http):
    itad_http["/lookup/id/shop/61/v1"] = _response({"app/1245620": ELDEN})
    itad_http["/games/history/v2"] = _response(
        [
            change("2026-09-01T10:00:00+02:00", "GOG", 50.0),
            change("2026-08-01T10:00:00+02:00", "Steam", 35.99, 40),
        ]
    )
    itad_http["/games/prices/v3"] = _response(
        [{"id": ELDEN, "deals": [deal("GOG", 50.0)]}]
    )

    history = ItadPriceHistoryRepository(
        client(),
        FixedRate(),
        now=lambda: NOW,
        steam_prices=lambda app_id: None,
    ).get("1245620")

    assert [point.store for point in history.points] == ["GOG"]
    assert history.steam_best_discount.discount == 40


def test_history_closes_with_todays_price_when_it_differs_from_the_last_change(
    itad_http,
):
    itad_http["/games/history/v2"] = _response(
        [change("2026-09-01T10:00:00+02:00", "GOG", 50.0)]
    )
    itad_http["/games/prices/v3"] = _response(
        [{"id": ELDEN, "deals": [deal("GOG", 50.0), deal("Humble Store", 40.0, 50.0, 20)]}]
    )

    history = history_repository().get(f"itad-{ELDEN}")

    assert history.current.store == "Humble Store"
    assert history.current.price == 160000.0
    assert history.current.discount == 20
    assert history.current.date == NOW

    # Un identificador de IsThereAnyDeal no necesita la equivalencia de Steam.
    assert all("lookup" not in call["url"] for call in itad_http["calls"])


def test_history_is_none_for_games_the_source_does_not_know(itad_http):
    itad_http["/lookup/id/shop/61/v1"] = _response({"app/999": None})
    repository = history_repository()

    assert repository.get("999") is None
    assert repository.get("UP0700-PPSA04610_00-ELDENRING0000000") is None
    assert repository.get("itad-no-es-un-uuid") is None

    # «No existe» se recuerda: no se vuelve a preguntar.
    repository.get("999")

    assert len(itad_http["calls"]) == 1


def test_history_is_cached_and_survives_a_later_failure(itad_http):
    itad_http["/games/history/v2"] = _response(
        [change("2026-09-01T10:00:00+02:00", "GOG", 50.0)]
    )
    itad_http["/games/prices/v3"] = _response(
        [{"id": ELDEN, "deals": [deal("GOG", 50.0)]}]
    )
    repository = history_repository()

    first = repository.get(f"itad-{ELDEN}")
    repository.get(f"itad-{ELDEN}")

    assert len(itad_http["calls"]) == 2

    # Vence la caché de una hora y la fuente ya no responde.
    repository._histories._entries.clear()
    itad_http["/games/history/v2"] = httpx.ConnectError("fuente caída")

    backup = repository.get(f"itad-{ELDEN}")

    assert backup.points == first.points
    assert backup.cached_at == NOW


def test_history_failure_without_a_previous_answer_is_reported(itad_http):
    itad_http["/games/history/v2"] = httpx.ConnectError("fuente caída")

    histories = history_repository()

    with pytest.raises(ExternalSourceError):
        histories.get(f"itad-{ELDEN}")


def test_use_case_explains_why_there_is_no_history(itad_http):
    assert GetPriceHistory(None).execute("620").reason == "not_configured"

    itad_http["/lookup/id/shop/61/v1"] = _response({})

    answer = GetPriceHistory(history_repository()).execute("620")

    assert answer.history is None
    assert answer.reason == "not_found"


# --- Endpoint GET /games/{id}/price-history ------------------------------------

api = TestClient(main.app)


def test_endpoint_says_history_is_disabled_without_a_key(monkeypatch):
    monkeypatch.setattr(main.get_price_history, "repository", None)

    data = api.get("/games/620/price-history").json()

    assert data["available"] is False
    assert data["reason"] == "not_configured"
    assert data["points"] == []


def test_endpoint_returns_the_history(monkeypatch, itad_http):
    itad_http["/lookup/id/shop/61/v1"] = _response({"app/1245620": ELDEN})
    itad_http["/games/history/v2"] = _response(
        [
            change("2026-09-01T10:00:00+02:00", "GameBillet", 52.0, 12),
            change("2026-03-19T18:00:00+01:00", "Steam", 38.99, 35),
        ]
    )
    itad_http["/games/prices/v3"] = _response(
        [{"id": ELDEN, "deals": [deal("GameBillet", 52.0, 59.99, 12)]}]
    )
    monkeypatch.setattr(main.get_price_history, "repository", history_repository())

    response = api.get("/games/1245620/price-history")
    data = response.json()

    assert response.status_code == 200
    assert data["available"] is True
    assert data["currency"] == "COP"
    assert data["current"] == {
        "date": "2026-09-01T08:00:00+00:00",
        "store": "GameBillet",
        "price": 208000.0,
        "discount": 12,
    }
    assert data["lowest"] == data["current"]
    assert data["steam_best_discount"] == {
        "date": "2026-03-19T17:00:00+00:00",
        "discount": 35,
    }
    assert data["points"] == [data["current"]]
    assert data["cached_at"] is None


def test_endpoint_answers_503_when_the_source_fails(monkeypatch, itad_http):
    itad_http["/games/history/v2"] = httpx.ConnectError("fuente caída")
    monkeypatch.setattr(main.get_price_history, "repository", history_repository())

    response = api.get(f"/games/itad-{ELDEN}/price-history")

    assert response.status_code == 503
    assert response.json()["detail"]["reason"] == "source_unavailable"


def test_endpoint_rejects_an_identifier_with_strange_characters():
    assert api.get("/games/620%20;drop/price-history").status_code == 422
