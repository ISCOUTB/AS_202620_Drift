"""
Fichas de juegos de la tienda de Steam: imágenes, descripción, etiquetas,
fecha, reseñas y precio en Colombia, para muchos juegos en una sola llamada.

Usa `IStoreBrowseService/GetItems`, el servicio público con el que la propia
tienda arma sus listas. Las rutas de las imágenes salen de aquí: en los juegos
recientes Steam las guarda en carpetas con un código (por ejemplo
`.../apps/3513350/075494dc.../library_capsule.jpg`), y la ruta armada solo con
el identificador del juego da 404.
"""

import json
import logging
import time
from datetime import datetime, timezone
from threading import Lock
from typing import Callable, Dict, Iterable, List, Optional

import httpx  # noqa: F401  los tests parchean steam_store_items.httpx.get

from app.domain.ports.showcase import ExploreGame
from app.infrastructure.external.resilient_http import (
    ExternalSourceError,
    RetryPolicy,
    TimeBudget,
    get_json,
)
from app.infrastructure.observability import log_event

logger = logging.getLogger("drift")

SOURCE_NAME = "Steam"

ITEMS_URL = "https://api.steampowered.com/IStoreBrowseService/GetItems/v1"
TAGS_URL = "https://api.steampowered.com/IStoreService/GetTagList/v1"
ASSETS = "https://shared.akamai.steamstatic.com/store_item_assets/"

# Steam acepta hasta 50 juegos por llamada.
BATCH_SIZE = 50
ITEM_SECONDS = 60 * 60
TAG_LIST_SECONDS = 24 * 60 * 60
MAX_TAGS = 5
MAX_DEVELOPERS = 2
MAX_DESCRIPTION = 400


class SteamStoreItems:

    def __init__(
        self,
        policy: Optional[RetryPolicy] = None,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ):
        self._policy = policy or RetryPolicy(
            timeout_seconds=3.0,
            max_attempts=2,
            total_deadline_seconds=4.0,
        )
        self._sleep = sleep
        self._clock = clock
        self._items: Dict[str, tuple] = {}
        self._tag_names: Dict[int, str] = {}
        self._tags_loaded_at: Optional[float] = None
        self._lock = Lock()

    def details(self, app_ids: Iterable[str]) -> Dict[str, ExploreGame]:
        """
        Ficha de cada juego que Steam conoce, por identificador. Los que
        Steam no devuelve no aparecen. Si Steam no responde, eleva
        `ExternalSourceError`; lo ya guardado se entrega igual.
        """

        wanted = list(dict.fromkeys(str(app_id) for app_id in app_ids))
        now = self._clock()
        found: Dict[str, ExploreGame] = {}
        missing: List[str] = []

        with self._lock:
            for app_id in wanted:
                cached = self._items.get(app_id)

                if cached and now - cached[0] < ITEM_SECONDS:
                    found[app_id] = cached[1]
                else:
                    missing.append(app_id)

        if not missing:
            return found

        tag_names = self._tag_list()

        for start in range(0, len(missing), BATCH_SIZE):
            batch = missing[start:start + BATCH_SIZE]

            for game in self._fetch(batch, tag_names):
                found[game.id] = game

                with self._lock:
                    self._items[game.id] = (now, game)

        return found

    def _fetch(self, app_ids: List[str], tag_names: Dict[int, str]) -> List[ExploreGame]:
        request = {
            "ids": [{"appid": int(app_id)} for app_id in app_ids if app_id.isdecimal()],
            "context": {"country_code": "CO", "language": "spanish"},
            "data_request": {
                "include_assets": True,
                "include_basic_info": True,
                "include_tag_count": 12,
                "include_release": True,
                "include_reviews": True,
                "include_all_purchase_options": True,
            },
        }

        answer = get_json(
            ITEMS_URL,
            {"input_json": json.dumps(request)},
            source=SOURCE_NAME,
            policy=self._policy,
            sleep=self._sleep,
            budget=TimeBudget.from_policy(self._policy),
        )

        response = answer.get("response") if isinstance(answer, dict) else None
        items = response.get("store_items") if isinstance(response, dict) else None

        if not isinstance(items, list):
            raise ExternalSourceError(SOURCE_NAME, "invalid_response")

        games = []

        for item in items:
            game = _to_game(item, tag_names)

            if game is not None:
                games.append(game)

        return games

    def _tag_list(self) -> Dict[int, str]:
        """Nombres de las etiquetas en español; sin ellos, las fichas van sin etiquetas."""

        with self._lock:
            fresh = (
                self._tags_loaded_at is not None
                and self._clock() - self._tags_loaded_at < TAG_LIST_SECONDS
            )

            if fresh:
                return dict(self._tag_names)

        try:
            answer = get_json(
                TAGS_URL,
                {"language": "spanish"},
                source=SOURCE_NAME,
                policy=self._policy,
                sleep=self._sleep,
                budget=TimeBudget.from_policy(self._policy),
            )
            tags = answer["response"]["tags"]
            names = {
                int(tag["tagid"]): str(tag["name"])
                for tag in tags
                if isinstance(tag, dict) and tag.get("tagid") and tag.get("name")
            }
        except (ExternalSourceError, KeyError, TypeError, ValueError) as error:
            log_event(
                logger,
                "steam_tag_list_unavailable",
                reason=getattr(error, "reason", type(error).__name__),
            )

            with self._lock:
                return dict(self._tag_names)

        with self._lock:
            self._tag_names = names
            self._tags_loaded_at = self._clock()

            return dict(names)


def _to_game(item, tag_names: Dict[int, str]) -> Optional[ExploreGame]:
    if not isinstance(item, dict) or item.get("success") != 1:
        return None

    app_id = item.get("appid") or item.get("id")
    name = item.get("name")

    if not isinstance(app_id, int) or not isinstance(name, str) or not name.strip():
        return None

    assets = item.get("assets") if isinstance(item.get("assets"), dict) else {}
    info = item.get("basic_info") if isinstance(item.get("basic_info"), dict) else {}
    reviews = item.get("reviews") if isinstance(item.get("reviews"), dict) else {}
    summary = reviews.get("summary_filtered") if isinstance(reviews.get("summary_filtered"), dict) else {}
    price, original, discount = _price(item.get("best_purchase_option"))

    return ExploreGame(
        id=str(app_id),
        name=name.strip()[:120],
        image=_asset(assets, "library_capsule"),
        hero=_asset(assets, "library_hero"),
        header=_asset(assets, "header"),
        capsule=_asset(assets, "main_capsule"),
        description=_text(info.get("short_description"), MAX_DESCRIPTION),
        tags=_tags(item.get("tags"), tag_names),
        release_date=_release(item.get("release")),
        developers=tuple(
            developer["name"].strip()
            for developer in (info.get("developers") or [])[:MAX_DEVELOPERS]
            if isinstance(developer, dict) and isinstance(developer.get("name"), str)
        ),
        review=_text(summary.get("review_score_label"), 60),
        review_percent=(
            summary["percent_positive"]
            if isinstance(summary.get("percent_positive"), int)
            else None
        ),
        price=price,
        original_price=original,
        discount=discount,
        is_free=item.get("is_free") is True,
    )


def _asset(assets: dict, key: str) -> Optional[str]:
    """URL completa de una imagen: la ruta lleva el código de la carpeta."""

    file = assets.get(key)
    template = assets.get("asset_url_format")

    if not isinstance(file, str) or not isinstance(template, str):
        return None

    if "${FILENAME}" not in template or not template.startswith("steam/"):
        return None

    return ASSETS + template.replace("${FILENAME}", file)


def _text(value, limit: int) -> Optional[str]:
    if not isinstance(value, str) or not value.strip():
        return None

    return value.strip()[:limit]


def _tags(tags, tag_names: Dict[int, str]) -> tuple:
    if not isinstance(tags, list):
        return ()

    ordered = sorted(
        (tag for tag in tags if isinstance(tag, dict) and isinstance(tag.get("tagid"), int)),
        key=lambda tag: -(tag.get("weight") or 0),
    )

    names = [tag_names[tag["tagid"]] for tag in ordered if tag["tagid"] in tag_names]

    return tuple(names[:MAX_TAGS])


def _release(release):
    if not isinstance(release, dict):
        return None

    timestamp = release.get("steam_release_date")

    if not isinstance(timestamp, int) or timestamp <= 0:
        return None

    return datetime.fromtimestamp(timestamp, tz=timezone.utc).date()


def _cents(value) -> Optional[float]:
    try:
        cents = int(value)
    except (TypeError, ValueError):
        return None

    return cents / 100 if cents >= 0 else None


def _price(option):
    """(precio, precio sin descuento, descuento %) en pesos; None si no se vende."""

    if not isinstance(option, dict):
        return None, None, 0

    price = _cents(option.get("final_price_in_cents"))
    original = _cents(option.get("original_price_in_cents"))
    discount = option.get("discount_pct")

    if not isinstance(discount, int) or not 0 < discount <= 100 or original is None:
        return price, None, 0

    return price, original, discount
