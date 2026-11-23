import html
import re
from typing import List, Optional
from urllib.parse import urlsplit

import httpx  # noqa: F401  los tests parchean steam_game_details_source.httpx.get

from app.domain.model.game_details import GameDetails, Screenshot, Trailer
from app.domain.ports.game_details_source import GameDetailsSource
from app.infrastructure.external.resilient_http import (
    ExternalSourceError,
    RetryPolicy,
    get_json,
)
from app.infrastructure.external.single_flight_cache import SingleFlightCache

SOURCE_NAME = "Steam"
DETAILS_URL = "https://store.steampowered.com/api/appdetails"

# La ficha se pide al abrir la página de un juego: una sola llamada, con el
# mismo timeout que la búsqueda. Variables DRIFT_STEAM_DETAILS_*.
DEFAULT_POLICY = dict(timeout_seconds=3.0, max_attempts=1)

# La ficha cambia poco; una hora evita repetir la consulta a Steam cuando
# varias personas abren el mismo juego.
CACHE_SECONDS = 60 * 60

MAX_TRAILERS = 8
MAX_SCREENSHOTS = 12
MAX_DESCRIPTION = 700
MAX_NAME = 160
MAX_LIST = 6

# Los identificadores de Steam son enteros positivos de hasta 8 cifras.
_MAX_APP_ID = 99_999_999

# Solo se entregan direcciones HTTPS de la CDN de Steam: la página las usa
# como imagen o video y no debe cargar nada de otro sitio.
_STEAM_CDN = ".steamstatic.com"


def steam_media_url(value) -> Optional[str]:
    if not isinstance(value, str) or len(value) > 600:
        return None

    parts = urlsplit(value)

    if parts.scheme != "https" or not parts.hostname:
        return None

    if not parts.hostname.endswith(_STEAM_CDN):
        return None

    return value


def _plain(value, limit: int) -> Optional[str]:
    if not isinstance(value, str):
        return None

    text = re.sub(r"<[^>]{0,400}>", " ", value)
    text = " ".join(html.unescape(text).split())

    if not text:
        return None

    if len(text) <= limit:
        return text

    return text[: limit - 1].rstrip() + "…"


def _names(items, key: Optional[str] = None) -> tuple:
    if not isinstance(items, list):
        return ()

    names = []

    for item in items:
        value = item.get(key) if key and isinstance(item, dict) else item
        name = _plain(value, 80)

        if name and name not in names:
            names.append(name)

    return tuple(names[:MAX_LIST])


def _trailers(movies) -> tuple:
    if not isinstance(movies, list):
        return ()

    trailers: List[Trailer] = []

    for movie in movies:
        if not isinstance(movie, dict):
            continue

        hls = steam_media_url(movie.get("hls_h264"))
        thumbnail = steam_media_url(movie.get("thumbnail"))

        # Sin transmisión HLS o sin miniatura no hay nada que reproducir.
        if not hls or not thumbnail:
            continue

        trailers.append(
            Trailer(
                name=_plain(movie.get("name"), 120) or "Tráiler",
                thumbnail=thumbnail,
                hls=hls,
                dash=steam_media_url(movie.get("dash_h264")),
            )
        )

        if len(trailers) == MAX_TRAILERS:
            break

    return tuple(trailers)


def _screenshots(shots) -> tuple:
    if not isinstance(shots, list):
        return ()

    screenshots: List[Screenshot] = []

    for shot in shots:
        if not isinstance(shot, dict):
            continue

        thumbnail = steam_media_url(shot.get("path_thumbnail"))
        full = steam_media_url(shot.get("path_full"))

        if thumbnail and full:
            screenshots.append(Screenshot(thumbnail=thumbnail, full=full))

        if len(screenshots) == MAX_SCREENSHOTS:
            break

    return tuple(screenshots)


def _release(release):
    if not isinstance(release, dict):
        return None, False

    return _plain(release.get("date"), 40), release.get("coming_soon") is True


def parse_game_details(game_id: str, data) -> Optional[GameDetails]:
    """Convierte el `data` de appdetails en una ficha; `None` si no sirve."""

    if not isinstance(data, dict):
        return None

    name = _plain(data.get("name"), MAX_NAME)

    if not name:
        return None

    release_date, coming_soon = _release(data.get("release_date"))

    return GameDetails(
        game_id=game_id,
        name=name,
        description=_plain(data.get("short_description"), MAX_DESCRIPTION),
        header_image=steam_media_url(data.get("header_image")),
        background_image=steam_media_url(data.get("background_raw"))
        or steam_media_url(data.get("background")),
        release_date=release_date,
        coming_soon=coming_soon,
        developers=_names(data.get("developers")),
        publishers=_names(data.get("publishers")),
        genres=_names(data.get("genres"), "description"),
        trailers=_trailers(data.get("movies")),
        screenshots=_screenshots(data.get("screenshots")),
    )


class SteamGameDetailsSource(GameDetailsSource):
    """Adaptador que obtiene de Steam la ficha de un juego (appdetails)."""

    def __init__(self, policy: Optional[RetryPolicy] = None):
        self._policy = policy or RetryPolicy.from_env(
            "DRIFT_STEAM_DETAILS",
            **DEFAULT_POLICY,
        )
        self._cache = SingleFlightCache(ttl_seconds=CACHE_SECONDS)

    def get(self, game_id: str) -> Optional[GameDetails]:
        if not game_id.isdecimal() or not 0 < int(game_id) <= _MAX_APP_ID:
            return None

        app_id = str(int(game_id))

        # Los errores no se guardan en la caché: la siguiente visita reintenta.
        return self._cache.get_or_load(app_id, lambda: self._fetch(app_id))

    def _fetch(self, app_id: str) -> Optional[GameDetails]:
        payload = get_json(
            DETAILS_URL,
            {"appids": app_id, "cc": "co", "l": "spanish"},
            source=SOURCE_NAME,
            policy=self._policy,
        )

        # Steam responde `null` a veces para un juego que no existe.
        if payload is None:
            return None

        if not isinstance(payload, dict):
            raise ExternalSourceError(SOURCE_NAME, "invalid_response")

        entry = payload.get(app_id)

        if not isinstance(entry, dict) or entry.get("success") is not True:
            return None

        return parse_game_details(app_id, entry.get("data"))
