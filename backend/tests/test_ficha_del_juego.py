"""
Página de cada juego: la ficha de Steam con sinopsis, tráilers y capturas
(`GET /games/{id}/details`).

Ninguna prueba usa la red.
"""

import httpx
import pytest
from fastapi.testclient import TestClient

from app import main
from app.application.usecases.get_game_details import GetGameDetails
from app.infrastructure.external.resilient_http import RetryPolicy
from app.infrastructure.external.steam import steam_game_details_source
from app.infrastructure.external.steam.steam_game_details_source import (
    SteamGameDetailsSource,
    parse_game_details,
    steam_media_url,
)

POLICY = RetryPolicy(timeout_seconds=3.0, max_attempts=1)
CDN = "https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/2909400"
VIDEO = "https://video.akamai.steamstatic.com/store_trailers/2909400/1/abc"

client = TestClient(main.app)


def _response(payload, status=200):
    return httpx.Response(
        status,
        json=payload,
        request=httpx.Request("GET", "https://example.test"),
    )


def movie(name="Tráiler de lanzamiento", **changes):
    data = {
        "id": 1,
        "name": name,
        "thumbnail": f"{CDN}/movie_600x337.jpg?t=1",
        "dash_av1": f"{VIDEO}/dash_av1.mpd?t=1",
        "dash_h264": f"{VIDEO}/dash_h264.mpd?t=1",
        "hls_h264": f"{VIDEO}/hls_264_master.m3u8?t=1",
        "highlight": True,
    }
    data.update(changes)
    return data


def app_data(**changes):
    data = {
        "type": "game",
        "name": "FINAL FANTASY VII REBIRTH",
        "steam_appid": 2909400,
        "short_description": "El viaje a lo desconocido contin&uacute;a&#8230; <b>Cloud</b> y sus amigos.",
        "header_image": f"{CDN}/header.jpg?t=1",
        "background_raw": f"{CDN}/page_bg_raw.jpg?t=1",
        "developers": ["Square Enix"],
        "publishers": ["Square Enix", "Square Enix"],
        "genres": [
            {"id": "1", "description": "Acción"},
            {"id": "25", "description": "Aventura"},
        ],
        "release_date": {"coming_soon": False, "date": "23 ENE 2025"},
        "movies": [movie()],
        "screenshots": [
            {
                "id": 0,
                "path_thumbnail": f"{CDN}/ss_1.600x338.jpg?t=1",
                "path_full": f"{CDN}/ss_1.1920x1080.jpg?t=1",
            }
        ],
    }
    data.update(changes)
    return data


def steam_answer(data=None, success=True, app_id="2909400"):
    entry = {"success": success}

    if data is not None:
        entry["data"] = data

    return {app_id: entry}


@pytest.fixture
def steam(monkeypatch):
    """Simula appdetails de Steam y cuenta las llamadas."""

    calls = []
    answer = {"value": _response(steam_answer(app_data()))}

    def fake_get(url, params=None, **kwargs):
        calls.append(params)
        value = answer["value"]

        if isinstance(value, Exception):
            raise value

        return value

    monkeypatch.setattr(steam_game_details_source.httpx, "get", fake_get)

    source = SteamGameDetailsSource(POLICY)
    monkeypatch.setattr(main, "get_game_details", GetGameDetails(source))

    return answer, calls


def test_the_details_bring_the_synopsis_trailers_and_screenshots(steam):
    response = client.get("/games/2909400/details")

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == "2909400"
    assert body["name"] == "FINAL FANTASY VII REBIRTH"
    # Sin etiquetas HTML y con las entidades resueltas.
    assert body["description"] == "El viaje a lo desconocido continúa… Cloud y sus amigos."
    assert body["header_image"].endswith("header.jpg?t=1")
    assert body["background_image"].endswith("page_bg_raw.jpg?t=1")
    assert body["release_date"] == "23 ENE 2025"
    assert body["coming_soon"] is False
    assert body["developers"] == ["Square Enix"]
    # Repetidos una sola vez.
    assert body["publishers"] == ["Square Enix"]
    assert body["genres"] == ["Acción", "Aventura"]
    assert body["trailers"] == [
        {
            "name": "Tráiler de lanzamiento",
            "thumbnail": f"{CDN}/movie_600x337.jpg?t=1",
            "hls": f"{VIDEO}/hls_264_master.m3u8?t=1",
            "dash": f"{VIDEO}/dash_h264.mpd?t=1",
        }
    ]
    assert body["screenshots"] == [
        {
            "thumbnail": f"{CDN}/ss_1.600x338.jpg?t=1",
            "full": f"{CDN}/ss_1.1920x1080.jpg?t=1",
        }
    ]
    assert body["source"] == "Steam"


def test_steam_is_asked_in_spanish_with_colombian_prices(steam):
    _, calls = steam

    client.get("/games/2909400/details")

    assert calls == [{"appids": "2909400", "cc": "co", "l": "spanish"}]


def test_the_same_game_is_asked_to_steam_only_once(steam):
    _, calls = steam

    client.get("/games/2909400/details")
    client.get("/games/2909400/details")

    assert len(calls) == 1


def test_a_game_without_steam_id_has_no_details_and_steam_is_not_called(steam):
    _, calls = steam

    response = client.get("/games/itad-018d937f-11e9/details")

    assert response.status_code == 404
    assert response.json()["detail"]["reason"] == "not_found"
    assert calls == []


def test_a_game_unknown_to_steam_is_not_found(steam):
    answer, _ = steam
    answer["value"] = _response(steam_answer(success=False))

    response = client.get("/games/2909400/details")

    assert response.status_code == 404


def test_steam_down_is_reported_as_unavailable_not_as_missing(steam):
    answer, _ = steam
    answer["value"] = httpx.ConnectError("sin red")

    response = client.get("/games/2909400/details")

    assert response.status_code == 503
    assert response.json()["detail"] == {
        "source": "Steam",
        "reason": "source_unavailable",
    }


def test_a_failure_is_not_cached(steam):
    answer, calls = steam
    answer["value"] = httpx.ConnectError("sin red")

    assert client.get("/games/2909400/details").status_code == 503

    answer["value"] = _response(steam_answer(app_data()))

    assert client.get("/games/2909400/details").status_code == 200
    assert len(calls) == 2


def test_an_unexpected_answer_is_a_failure(steam):
    answer, _ = steam
    answer["value"] = _response(["no", "es", "un", "objeto"])

    assert client.get("/games/2909400/details").status_code == 503


def test_a_trailer_without_hls_stream_is_skipped():
    details = parse_game_details(
        "1",
        app_data(movies=[movie(hls_h264=None), movie(name="Segundo", dash_h264=None)]),
    )

    assert [trailer.name for trailer in details.trailers] == ["Segundo"]
    assert details.trailers[0].dash is None


@pytest.mark.parametrize(
    "url",
    [
        "http://shared.akamai.steamstatic.com/a.jpg",
        "https://evil.example.com/a.jpg",
        "https://steamstatic.com.evil.example/a.jpg",
        "javascript:alert(1)",
        "https://shared.akamai.steamstatic.com/" + "a" * 700,
        None,
        42,
    ],
)
def test_only_https_media_from_the_steam_cdn_is_accepted(url):
    assert steam_media_url(url) is None


def test_media_from_other_sites_never_reaches_the_page():
    details = parse_game_details(
        "1",
        app_data(
            header_image="https://evil.example.com/header.jpg",
            movies=[movie(hls_h264="https://evil.example.com/x.m3u8")],
            screenshots=[{"path_thumbnail": "https://evil.example.com/a.jpg", "path_full": "x"}],
        ),
    )

    assert details.header_image is None
    assert details.trailers == ()
    assert details.screenshots == ()


def test_lists_are_capped():
    details = parse_game_details(
        "1",
        app_data(
            movies=[movie(name=f"T{index}") for index in range(20)],
            screenshots=[
                {
                    "path_thumbnail": f"{CDN}/ss_{index}.jpg",
                    "path_full": f"{CDN}/ss_{index}_full.jpg",
                }
                for index in range(30)
            ],
        ),
    )

    assert len(details.trailers) == steam_game_details_source.MAX_TRAILERS
    assert len(details.screenshots) == steam_game_details_source.MAX_SCREENSHOTS


def test_a_long_synopsis_is_shortened():
    details = parse_game_details("1", app_data(short_description="palabra " * 300))

    assert len(details.description) <= steam_game_details_source.MAX_DESCRIPTION
    assert details.description.endswith("…")


def test_data_without_a_name_is_not_a_game():
    assert parse_game_details("1", app_data(name="")) is None
    assert parse_game_details("1", None) is None


def test_the_details_route_is_rate_limited():
    request = type("R", (), {})()
    request.method = "GET"
    request.url = type("U", (), {"path": "/games/2909400/details"})()

    assert main._calls_external_sources(request)
