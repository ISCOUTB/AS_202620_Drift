import re
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, List, Optional

import httpx  # noqa: F401  los tests parchean xbox_game_repository.httpx.get

from app.domain.model.game import Game
from app.domain.ports.exchange_rate_provider import ExchangeRateProvider
from app.domain.ports.game_repository import GameRepository
from app.infrastructure.external.resilient_http import (
    ExternalSourceError,
    RetryPolicy,
    TimeBudget,
    get_json,
)
from app.infrastructure.external.single_flight_cache import SingleFlightCache
from app.infrastructure.game_copy import copy_games

SOURCE_NAME = "Xbox"

# Son los endpoints que usa la propia tienda web de Microsoft. No tienen
# contrato publicado ni soporte oficial: pueden cambiar sin aviso, y por
# eso toda respuesta se valida antes de usarla. Un reintento y un plazo
# total igual al de las demás fuentes secundarias.
DEFAULT_POLICY = dict(timeout_seconds=3.0, max_attempts=2)
DEFAULT_TOTAL_DEADLINE_SECONDS = 3.0

# Identificador público con el que la tienda web llama a su buscador.
STORE_WEB_CLIENT_ID = "7F27B536-CF6B-4C65-8638-A0F8CBDFCA65"

MAX_PRODUCTS = 14

# El buscador completo de la tienda es lento a veces: se le da la mitad del
# plazo para que siempre quede tiempo de pedir los precios.
SEARCH_DEADLINE_SECONDS = 1.5

# Tienda de consola y tienda de PC: el mismo catálogo vende para las dos.
CONSOLE_STORE = "Xbox"
PC_STORE = "Microsoft Store"

_PREFERRED_IMAGES = ("Poster", "BoxArt", "BrandedKeyArt")


class XboxGameRepository(GameRepository):
    """
    Adaptador de la tienda de Xbox para Colombia.

    Primero encuentra los productos y después pide sus precios en pesos al
    catálogo. Para encontrarlos consulta a la vez los dos buscadores de la
    tienda, porque cada uno falla en casos distintos:

    - las sugerencias devuelven muy pocos resultados y, en una saga con
      muchos complementos, solo complementos (buscar «persona» no traía
      Persona 5 Royal);
    - la búsqueda completa trae los juegos base, pero rellena con títulos
      que no tienen que ver cuando no encuentra suficientes, así que de
      ella solo se aceptan los que contienen todas las palabras buscadas.

    Basta con que uno de los dos responda.
    """

    _suggest_url = "https://www.microsoft.com/msstoreapiprod/api/autosuggest"
    _search_url = "https://storeedgefd.dsx.mp.microsoft.com/v9.0/search"
    _catalog_url = "https://displaycatalog.mp.microsoft.com/v7.0/products"
    _product_url = "https://www.xbox.com/es-CO/games/store/_/"

    _headers = {"Accept": "application/json"}

    def __init__(
        self,
        exchange_rates: ExchangeRateProvider,
        policy: Optional[RetryPolicy] = None,
        sleep: Callable[[float], None] = time.sleep,
    ):
        # Variables DRIFT_XBOX_*.
        self._policy = policy or RetryPolicy.from_env(
            "DRIFT_XBOX",
            default_total_deadline_seconds=DEFAULT_TOTAL_DEADLINE_SECONDS,
            **DEFAULT_POLICY,
        )
        self._search_policy = RetryPolicy(
            timeout_seconds=SEARCH_DEADLINE_SECONDS,
            max_attempts=1,
        )
        self._sleep = sleep
        self._exchange_rates = exchange_rates
        self._cache = SingleFlightCache(ttl_seconds=60)

    def search(self, query: str) -> List[Game]:
        cache_key = query.strip().lower()

        if not cache_key:
            return []

        games = self._cache.get_or_load(
            cache_key,
            lambda: self._search_xbox(query.strip()),
        )

        return copy_games(games)

    def _search_xbox(self, query: str) -> List[Game]:
        # Un solo plazo para las dos llamadas.
        budget = TimeBudget.from_policy(self._policy)

        product_ids = self._find_product_ids(query, budget)

        if not product_ids:
            return []

        catalog = self._get_json(
            self._catalog_url,
            {
                "bigIds": ",".join(product_ids),
                "market": "CO",
                "languages": "es-co",
            },
            budget,
        )

        if not isinstance(catalog, dict) or not isinstance(
            catalog.get("Products"), list
        ):
            raise ExternalSourceError(SOURCE_NAME, "invalid_response")

        games_by_id = {}

        for product in catalog["Products"]:
            game = self._to_game(product)

            if game is not None:
                games_by_id.setdefault(game.id, game)

        # Se conserva el orden de relevancia del buscador.
        return [
            games_by_id[product_id]
            for product_id in product_ids
            if product_id in games_by_id
        ]

    def _find_product_ids(self, query: str, budget: TimeBudget) -> List[str]:
        with ThreadPoolExecutor(max_workers=2) as executor:
            searches = [
                executor.submit(self._searched_ids, query),
                executor.submit(self._suggested_ids, query, budget),
            ]

        found = []
        failures = []

        for search in searches:
            try:
                found.append(search.result())
            except ExternalSourceError as error:
                failures.append(error)

        # Con que un buscador responda hay resultado; si fallan los dos, la
        # fuente no está disponible.
        if not found:
            raise failures[-1]

        product_ids = []

        # Primero la búsqueda completa: trae los juegos base antes que los
        # complementos.
        for ids in found:
            for product_id in ids:
                if product_id not in product_ids:
                    product_ids.append(product_id)

        return product_ids[:MAX_PRODUCTS]

    def _searched_ids(self, query: str) -> List[str]:
        """Búsqueda completa de la tienda, solo con los títulos que coinciden."""

        answer = get_json(
            self._search_url,
            {
                "query": query,
                "market": "CO",
                "locale": "es-CO",
                "deviceFamily": "Windows.Xbox",
                "mediaType": "games",
            },
            source=SOURCE_NAME,
            policy=self._search_policy,
            sleep=self._sleep,
            headers=self._headers,
            budget=TimeBudget(SEARCH_DEADLINE_SECONDS),
        )

        payload = answer.get("Payload") if isinstance(answer, dict) else None
        results = payload.get("SearchResults") if isinstance(payload, dict) else None

        if not isinstance(results, list):
            raise ExternalSourceError(SOURCE_NAME, "invalid_response")

        wanted = _words(query)
        product_ids = []

        for result in results:
            if not isinstance(result, dict):
                continue

            product_id = result.get("ProductId")
            title = result.get("Title")

            if (
                isinstance(product_id, str)
                and product_id.isalnum()
                and isinstance(title, str)
                and wanted
                and wanted <= _words(title)
                and product_id.upper() not in product_ids
            ):
                product_ids.append(product_id.upper())

        return product_ids

    def _suggested_ids(self, query: str, budget: TimeBudget) -> List[str]:
        suggestions = self._get_json(
            self._suggest_url,
            {
                "market": "es-co",
                "clientId": STORE_WEB_CLIENT_ID,
                "sources": "DCatAll-Products",
                "filter": "+ClientType:StoreWeb",
                "counts": "15",
                "query": query,
            },
            budget,
        )

        if not isinstance(suggestions, dict) or not isinstance(
            suggestions.get("ResultSets"), list
        ):
            raise ExternalSourceError(SOURCE_NAME, "invalid_response")

        product_ids = []

        for result_set in suggestions["ResultSets"]:
            if not isinstance(result_set, dict):
                continue

            for suggestion in result_set.get("Suggests") or []:
                product_id = _game_product_id(suggestion)

                if product_id and product_id not in product_ids:
                    product_ids.append(product_id)

        return product_ids

    def _to_game(self, product) -> Optional[Game]:
        """`None` si no es un juego o no se puede comprar en Colombia."""

        if not isinstance(product, dict) or product.get("ProductKind") != "Game":
            return None

        product_id = product.get("ProductId")
        localized = _first(product.get("LocalizedProperties"))
        title = localized.get("ProductTitle")

        if not isinstance(product_id, str) or not isinstance(title, str):
            return None

        offer = self._best_offer(product)

        if offer is None:
            return None

        store, price, discount = offer

        return Game(
            id=product_id,
            name=title,
            prices={store: price},
            image=_image(localized),
            links={store: f"{self._product_url}{product_id}"},
            discounts={store: discount} if discount else {},
        )

    def _best_offer(self, product: dict):
        """
        La oferta de compra más barata: (tienda, precio en COP, descuento).

        Un producto trae muchas «disponibilidades»: licencias, canjes de
        código, regalos. Solo cuentan las que se pueden comprar.
        """

        best = None

        for sku in product.get("DisplaySkuAvailabilities") or []:
            if not isinstance(sku, dict):
                continue

            for availability in sku.get("Availabilities") or []:
                offer = self._offer(availability)

                if offer is None:
                    continue

                # Igual que al combinar tiendas: se prefiere el menor precio
                # real y el cero (gratis) solo si no hay otro.
                if (
                    best is None
                    or best[1] <= 0 < offer[1]
                    or 0 < offer[1] < best[1]
                ):
                    best = offer

        return best

    def _offer(self, availability):
        if not isinstance(availability, dict):
            return None

        if "Purchase" not in (availability.get("Actions") or []):
            return None

        order = availability.get("OrderManagementData")
        price = order.get("Price") if isinstance(order, dict) else None

        if not isinstance(price, dict):
            return None

        list_price = _number(price.get("ListPrice"))
        full_price = _number(price.get("MSRP"))
        rate = self._rate_to_cop(price.get("CurrencyCode"))

        if list_price is None or rate is None:
            return None

        discount = 0

        if full_price and 0 < list_price < full_price:
            discount = round((1 - list_price / full_price) * 100)

        return (
            _store(availability),
            round(list_price * rate, 2),
            discount,
        )

    def _rate_to_cop(self, currency) -> Optional[float]:
        if currency == "COP":
            return 1.0

        if currency == "USD":
            return self._exchange_rates.usd_to_cop()

        # Otra moneda no se puede comparar con las demás tiendas.
        return None

    def _get_json(self, url: str, params: dict, budget: TimeBudget):
        return get_json(
            url,
            params,
            source=SOURCE_NAME,
            policy=self._policy,
            sleep=self._sleep,
            headers=self._headers,
            budget=budget,
        )


def _words(text: str) -> set:
    """Palabras de un texto sin tildes, mayúsculas ni signos."""

    text = unicodedata.normalize("NFKD", text)
    text = "".join(
        character for character in text if not unicodedata.combining(character)
    ).casefold()

    return set(re.sub(r"[^a-z0-9]+", " ", text).split())


def _game_product_id(suggestion) -> Optional[str]:
    if not isinstance(suggestion, dict):
        return None

    metas = {
        meta.get("Key"): meta.get("Value")
        for meta in suggestion.get("Metas") or []
        if isinstance(meta, dict)
    }

    product_id = metas.get("BigCatalogId")

    if metas.get("ProductType") != "Games" or not isinstance(product_id, str):
        return None

    # El identificador viaja en la URL del catálogo: solo letras y números.
    return product_id.upper() if product_id.isalnum() else None


def _store(availability: dict) -> str:
    conditions = availability.get("Conditions")
    client = (
        conditions.get("ClientConditions")
        if isinstance(conditions, dict)
        else None
    )
    allowed = client.get("AllowedPlatforms") if isinstance(client, dict) else None

    names = {
        platform.get("PlatformName")
        for platform in allowed or []
        if isinstance(platform, dict)
    }

    if "Windows.Desktop" in names and "Windows.Xbox" not in names:
        return PC_STORE

    return CONSOLE_STORE


def _image(localized: dict) -> Optional[str]:
    images = [
        image
        for image in localized.get("Images") or []
        if isinstance(image, dict) and isinstance(image.get("Uri"), str)
    ]

    for purpose in _PREFERRED_IMAGES:
        for image in images:
            if image.get("ImagePurpose") == purpose:
                return _absolute(image["Uri"])

    return _absolute(images[0]["Uri"]) if images else None


def _absolute(uri: str) -> str:
    return f"https:{uri}" if uri.startswith("//") else uri


def _first(items) -> dict:
    if isinstance(items, list) and items and isinstance(items[0], dict):
        return items[0]

    return {}


def _number(value) -> Optional[float]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None

    return float(value) if value >= 0 else None
