"""
Adaptador de la tienda de Xbox.

Ninguna prueba usa la red: `httpx.get` se reemplaza por respuestas con la
misma forma que entregan el buscador y el catálogo de la tienda.
"""

import httpx
import pytest

from app.domain.ports.exchange_rate_provider import ExchangeRateProvider
from app.infrastructure.external.resilient_http import (
    ExternalSourceError,
    RetryPolicy,
)
from app.infrastructure.external.xbox import xbox_game_repository
from app.infrastructure.external.xbox.xbox_game_repository import (
    XboxGameRepository,
)

POLICY = RetryPolicy(timeout_seconds=3.0, max_attempts=2, backoff_base_seconds=0.0)


class FixedRate(ExchangeRateProvider):
    def usd_to_cop(self) -> float:
        return 4000.0


def _response(payload, status_code=200):
    return httpx.Response(
        status_code,
        json=payload,
        request=httpx.Request("GET", "https://example.test"),
    )


def suggestion(product_id, title, product_type="Games"):
    return {
        "Source": "Juego",
        "Title": title,
        "Metas": [
            {"Key": "BigCatalogId", "Value": product_id},
            {"Key": "ProductType", "Value": product_type},
        ],
    }


def suggestions(*items):
    return {"Query": "x", "ResultSets": [{"Suggests": list(items)}]}


def availability(
    actions,
    list_price,
    msrp=None,
    currency="COP",
    platforms=("Windows.Xbox",),
):
    return {
        "Actions": list(actions),
        "Conditions": {
            "ClientConditions": {
                "AllowedPlatforms": [
                    {"PlatformName": name} for name in platforms
                ]
            }
        },
        "OrderManagementData": {
            "Price": {
                "ListPrice": list_price,
                "MSRP": list_price if msrp is None else msrp,
                "CurrencyCode": currency,
            }
        },
    }


BUY = ("Details", "Purchase", "Browse")
LICENSE = ("License", "Browse", "Details")


def product(product_id, title, availabilities, kind="Game", images=None):
    return {
        "ProductId": product_id,
        "ProductKind": kind,
        "LocalizedProperties": [
            {
                "ProductTitle": title,
                "Images": images
                if images is not None
                else [
                    {"ImagePurpose": "Screenshot", "Uri": "//img.test/shot.jpg"},
                    {"ImagePurpose": "Poster", "Uri": "//img.test/poster.jpg"},
                ],
            }
        ],
        "DisplaySkuAvailabilities": [{"Availabilities": list(availabilities)}],
    }


@pytest.fixture
def xbox_http(monkeypatch):
    """Rutas simuladas del buscador (`autosuggest`) y del catálogo (`products`)."""

    routes = {}
    calls = []

    def fake_get(url, params=None, **kwargs):
        calls.append({"url": url, "params": params})

        for key, outcome in routes.items():
            if key in url:
                if isinstance(outcome, Exception):
                    raise outcome

                return outcome

        raise httpx.ConnectError(f"ruta no simulada: {url}")

    monkeypatch.setattr(xbox_game_repository.httpx, "get", fake_get)

    routes["calls"] = calls

    return routes


def repository():
    return XboxGameRepository(FixedRate(), policy=POLICY, sleep=lambda _: None)


def test_search_returns_the_price_in_pesos_with_its_purchase_link(xbox_http):
    xbox_http["autosuggest"] = _response(
        suggestions(suggestion("9P3J32CTXLRZ", "ELDEN RING"))
    )
    xbox_http["products"] = _response(
        {
            "Products": [
                product(
                    "9P3J32CTXLRZ",
                    "ELDEN RING",
                    [
                        availability(BUY, 201900.0),
                        # Licencias y canjes: no son precios de compra.
                        availability(LICENSE, 0.0, currency="USD"),
                        availability(("Details", "Redeem"), 0.0),
                    ],
                )
            ]
        }
    )

    games = repository().search("elden ring")

    assert len(games) == 1
    assert games[0].id == "9P3J32CTXLRZ"
    assert games[0].name == "ELDEN RING"
    assert games[0].prices == {"Xbox": 201900.0}
    assert games[0].links == {
        "Xbox": "https://www.xbox.com/es-CO/games/store/_/9P3J32CTXLRZ"
    }
    assert games[0].image == "https://img.test/poster.jpg"
    assert games[0].discounts == {}
    assert games[0].platforms == ["Xbox"]

    catalog_call = xbox_http["calls"][-1]

    assert catalog_call["params"]["market"] == "CO"
    assert catalog_call["params"]["bigIds"] == "9P3J32CTXLRZ"


def test_a_sale_reports_the_sale_price_and_its_discount(xbox_http):
    xbox_http["autosuggest"] = _response(suggestions(suggestion("9AAA", "Juego")))
    xbox_http["products"] = _response(
        {
            "Products": [
                product("9AAA", "Juego", [availability(BUY, 60000.0, msrp=200000.0)])
            ]
        }
    )

    game = repository().search("juego")[0]

    assert game.prices == {"Xbox": 60000.0}
    assert game.discounts == {"Xbox": 70}


def test_only_games_that_can_be_bought_are_returned(xbox_http):
    xbox_http["autosuggest"] = _response(
        suggestions(
            suggestion("9GAME", "Juego base"),
            suggestion("9DLC", "Paquete de autos"),
            suggestion("9APP", "Guía", product_type="Apps"),
            suggestion("9NOBUY", "Sin venta"),
        )
    )
    xbox_http["products"] = _response(
        {
            "Products": [
                product("9GAME", "Juego base", [availability(BUY, 99900.0)]),
                product(
                    "9DLC",
                    "Paquete de autos",
                    [availability(BUY, 19900.0)],
                    kind="Durable",
                ),
                product("9NOBUY", "Sin venta", [availability(LICENSE, 0.0)]),
            ]
        }
    )

    games = repository().search("juego")

    assert [game.id for game in games] == ["9GAME"]

    # Lo que el buscador marca como aplicación ni siquiera se pide al catálogo.
    assert "9APP" not in xbox_http["calls"][-1]["params"]["bigIds"]


def test_a_free_game_keeps_a_price_of_zero(xbox_http):
    xbox_http["autosuggest"] = _response(suggestions(suggestion("9FREE", "Gratis")))
    xbox_http["products"] = _response(
        {"Products": [product("9FREE", "Gratis", [availability(BUY, 0.0)])]}
    )

    assert repository().search("gratis")[0].prices == {"Xbox": 0.0}


def test_a_price_in_dollars_is_converted_and_other_currencies_are_skipped(
    xbox_http,
):
    xbox_http["autosuggest"] = _response(
        suggestions(suggestion("9USD", "En dólares"), suggestion("9EUR", "En euros"))
    )
    xbox_http["products"] = _response(
        {
            "Products": [
                product("9USD", "En dólares", [availability(BUY, 10.0, currency="USD")]),
                product("9EUR", "En euros", [availability(BUY, 10.0, currency="EUR")]),
            ]
        }
    )

    games = repository().search("moneda")

    assert [game.id for game in games] == ["9USD"]
    assert games[0].prices == {"Xbox": 40000.0}


def test_a_game_sold_only_for_windows_belongs_to_the_pc_store(xbox_http):
    xbox_http["autosuggest"] = _response(suggestions(suggestion("9PC", "Solo PC")))
    xbox_http["products"] = _response(
        {
            "Products": [
                product(
                    "9PC",
                    "Solo PC",
                    [availability(BUY, 50000.0, platforms=("Windows.Desktop",))],
                )
            ]
        }
    )

    game = repository().search("solo pc")[0]

    assert game.prices == {"Microsoft Store": 50000.0}
    assert game.platforms == ["PC"]


def test_no_suggestions_is_a_legitimate_empty_result_without_asking_for_prices(
    xbox_http,
):
    xbox_http["autosuggest"] = _response(suggestions())

    assert repository().search("zzzzqqq") == []

    # Los dos buscadores, y ninguna llamada al catálogo de precios.
    assert len(xbox_http["calls"]) == 2
    assert all("products" not in call["url"] for call in xbox_http["calls"])


@pytest.mark.parametrize(
    "payload",
    [{}, [], {"ResultSets": "no es una lista"}],
)
def test_an_unexpected_search_answer_is_a_failure_not_an_empty_result(
    xbox_http, payload
):
    xbox_http["autosuggest"] = _response(payload)

    with pytest.raises(ExternalSourceError) as error:
        repository().search("elden ring")

    assert error.value.reason == "invalid_response"


def test_an_unexpected_catalog_answer_is_a_failure(xbox_http):
    xbox_http["autosuggest"] = _response(suggestions(suggestion("9AAA", "Juego")))
    xbox_http["products"] = _response({"Products": None})

    with pytest.raises(ExternalSourceError) as error:
        repository().search("juego")

    assert error.value.reason == "invalid_response"


def test_a_store_failure_is_reported_and_not_cached(xbox_http):
    xbox_http["autosuggest"] = httpx.ConnectError("tienda caída")
    xbox = repository()

    with pytest.raises(ExternalSourceError):
        xbox.search("elden ring")

    xbox_http["autosuggest"] = _response(suggestions(suggestion("9AAA", "Juego")))
    xbox_http["products"] = _response(
        {"Products": [product("9AAA", "Juego", [availability(BUY, 1000.0)])]}
    )

    assert [game.id for game in xbox.search("elden ring")] == ["9AAA"]


def test_repeated_searches_reuse_the_first_answer(xbox_http):
    xbox_http["autosuggest"] = _response(suggestions(suggestion("9AAA", "Juego")))
    xbox_http["products"] = _response(
        {"Products": [product("9AAA", "Juego", [availability(BUY, 1000.0)])]}
    )
    xbox = repository()

    first = xbox.search("Juego")
    first[0].prices["Xbox"] = 1.0
    second = xbox.search("  juego ")

    # Dos buscadores y el catálogo, una sola vez para las dos búsquedas.
    assert len(xbox_http["calls"]) == 3
    assert second[0].prices == {"Xbox": 1000.0}


def test_malformed_products_are_skipped_without_failing(xbox_http):
    xbox_http["autosuggest"] = _response(
        suggestions(
            suggestion("9OK", "Bueno"),
            suggestion("9BAD", "Malo"),
            "no es un objeto",
            {"Metas": "tampoco"},
        )
    )
    xbox_http["products"] = _response(
        {
            "Products": [
                "no es un producto",
                {"ProductId": "9BAD", "ProductKind": "Game"},
                product(
                    "9OK",
                    "Bueno",
                    [
                        "no es una disponibilidad",
                        {"Actions": ["Purchase"]},
                        availability(BUY, True),
                        availability(BUY, 5000.0),
                    ],
                    images=[],
                ),
            ]
        }
    )

    games = repository().search("bueno")

    assert [game.id for game in games] == ["9OK"]
    assert games[0].prices == {"Xbox": 5000.0}
    assert games[0].image is None


# --- Los dos buscadores de la tienda ------------------------------------------


def store_search(*results):
    return {
        "Payload": {
            "SearchResults": [
                {"ProductId": product_id, "Title": title}
                for product_id, title in results
            ]
        }
    }


def catalog_ids(xbox_http):
    call = next(call for call in xbox_http["calls"] if "products" in call["url"])

    return call["params"]["bigIds"].split(",")


def test_base_games_hidden_behind_add_ons_are_found_by_the_full_search(xbox_http):
    # Lo que pasaba con «persona»: las sugerencias solo traían complementos.
    xbox_http["autosuggest"] = _response(
        suggestions(suggestion("9DLC", "Persona 3 Reload: Pase de expansión"))
    )
    xbox_http["v9.0/search"] = _response(
        store_search(
            ("9P5R", "Persona 5 Royal"),
            ("9P3R", "Edición digital premium de Persona 3 Reload"),
            # Relleno de la tienda cuando no encuentra suficientes.
            ("9OBLIVION", "The Elder Scrolls IV: Oblivion Remastered"),
            ("9FORTNITE", "Fortnite"),
        )
    )
    xbox_http["products"] = _response(
        {
            "Products": [
                product("9P5R", "Persona 5 Royal", [availability(BUY, 235999.0)]),
                product(
                    "9P3R",
                    "Edición digital premium de Persona 3 Reload",
                    [availability(BUY, 329000.0)],
                ),
                product(
                    "9DLC",
                    "Persona 3 Reload: Pase de expansión",
                    [availability(BUY, 136999.0)],
                    kind="Durable",
                ),
            ]
        }
    )

    games = repository().search("persona")

    # Los juegos base primero; el relleno ni siquiera se pide al catálogo.
    assert [game.name for game in games] == [
        "Persona 5 Royal",
        "Edición digital premium de Persona 3 Reload",
    ]
    assert catalog_ids(xbox_http) == ["9P5R", "9P3R", "9DLC"]


def test_the_full_search_must_contain_every_word_ignoring_accents_and_case(
    xbox_http,
):
    xbox_http["autosuggest"] = _response(suggestions())
    xbox_http["v9.0/search"] = _response(
        store_search(
            ("9A", "POKÉMON Edición Estándar"),
            ("9B", "Pokemon Quest"),
            ("9C", "Edición Estándar de otro juego"),
        )
    )
    xbox_http["products"] = _response(
        {
            "Products": [
                product("9A", "POKÉMON Edición Estándar", [availability(BUY, 1.0)])
            ]
        }
    )

    repository().search("pokemon edicion")

    assert catalog_ids(xbox_http) == ["9A"]


def test_one_search_failing_does_not_hide_the_results_of_the_other(xbox_http):
    xbox_http["autosuggest"] = httpx.ConnectError("sugerencias caídas")
    xbox_http["v9.0/search"] = _response(store_search(("9P5R", "Persona 5 Royal")))
    xbox_http["products"] = _response(
        {
            "Products": [
                product("9P5R", "Persona 5 Royal", [availability(BUY, 235999.0)])
            ]
        }
    )

    assert [game.id for game in repository().search("persona 5")] == ["9P5R"]

    # Y al revés: una respuesta rara de la búsqueda completa no tumba la otra.
    xbox_http["autosuggest"] = _response(
        suggestions(suggestion("9P5R", "Persona 5 Royal"))
    )
    xbox_http["v9.0/search"] = _response({"Payload": "otra forma"})

    assert [game.id for game in repository().search("persona 5 royal")] == ["9P5R"]

