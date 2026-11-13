from typing import List, Optional

from app.domain.model.game import Game
from app.domain.ports.exchange_rate_provider import ExchangeRateProvider
from app.domain.ports.game_repository import GameRepository
from app.domain.ports.showcase import PcStoreDirectory
from app.infrastructure.external.isthereanydeal.itad_client import (
    SOURCE_NAME,
    ItadClient,
)
from app.infrastructure.external.resilient_http import ExternalSourceError
from app.infrastructure.external.single_flight_cache import SingleFlightCache
from app.infrastructure.game_copy import copy_games

MAX_GAMES = 8

# Tiendas que DRIFT ya consulta directamente y en pesos colombianos.
EXCLUDED_SHOPS = {"Steam", "Microsoft Store"}

# Prefijo del identificador de un juego que no viene de Steam.
ID_PREFIX = "itad-"


STORES_TTL_SECONDS = 24 * 60 * 60


class ItadGameRepository(GameRepository, PcStoreDirectory):
    """
    Adaptador de IsThereAnyDeal: precios de las tiendas de juegos de PC.

    Reemplaza a CheapShark cuando hay una llave configurada. Hace dos
    llamadas por búsqueda: una para encontrar los juegos por nombre y otra
    para pedir los precios de todos a la vez.

    IsThereAnyDeal no tiene precios regionales para Colombia: los entrega
    en dólares, y aquí se convierten a pesos para poder compararlos.
    """

    def __init__(
        self,
        client: ItadClient,
        exchange_rates: ExchangeRateProvider,
    ):
        self._client = client
        self._exchange_rates = exchange_rates
        self._cache = SingleFlightCache(ttl_seconds=60)
        self._stores = SingleFlightCache(ttl_seconds=STORES_TTL_SECONDS)

    def pc_stores(self) -> List[str]:
        """Tiendas de PC con ofertas activas para Colombia, sin las directas."""

        return list(self._stores.get_or_load("CO", self._load_stores))

    def _load_stores(self) -> List[str]:
        shops = self._client.get("/service/shops/v1", {"country": "CO"})

        if not isinstance(shops, list):
            raise ExternalSourceError(SOURCE_NAME, "invalid_response")

        return [
            shop["title"]
            for shop in shops
            if isinstance(shop, dict)
            and isinstance(shop.get("title"), str)
            and shop["title"] not in EXCLUDED_SHOPS
        ]

    def search(self, query: str) -> List[Game]:
        cache_key = query.strip().lower()

        if not cache_key:
            return []

        games = self._cache.get_or_load(
            cache_key,
            lambda: self._search_itad(query.strip()),
        )

        return copy_games(games)

    def _search_itad(self, query: str) -> List[Game]:
        budget = self._client.new_budget()

        found = self._client.get(
            "/games/search/v1",
            {"title": query, "results": MAX_GAMES},
            budget,
        )

        # Una lista vacía es «sin resultados» (dato legítimo); otra forma es
        # una respuesta inválida y no debe guardarse como vacía.
        if not isinstance(found, list):
            raise ExternalSourceError(SOURCE_NAME, "invalid_response")

        titles = {}

        for item in found:
            if (
                isinstance(item, dict)
                and isinstance(item.get("id"), str)
                and isinstance(item.get("title"), str)
            ):
                titles.setdefault(item["id"], item)

        if not titles:
            return []

        priced = self._client.post(
            "/games/prices/v3",
            list(titles),
            # Sin cupones: el precio mostrado es el que paga cualquiera.
            {"country": "CO", "vouchers": "false"},
            budget,
        )

        if not isinstance(priced, list):
            raise ExternalSourceError(SOURCE_NAME, "invalid_response")

        usd_to_cop = self._exchange_rates.usd_to_cop()
        games_by_id = {}

        for entry in priced:
            if not isinstance(entry, dict) or entry.get("id") not in titles:
                continue

            game = self._to_game(titles[entry["id"]], entry, usd_to_cop)

            if game is not None:
                games_by_id[entry["id"]] = game

        # Se conserva el orden de relevancia de la búsqueda.
        return [
            games_by_id[game_id] for game_id in titles if game_id in games_by_id
        ]

    def _to_game(self, title: dict, entry: dict, usd_to_cop: float) -> Optional[Game]:
        game = Game(
            id=f"{ID_PREFIX}{title['id']}",
            name=title["title"],
            prices={},
            image=_image(title),
        )

        for deal in _deals(entry):
            offer = _offer(deal, usd_to_cop)

            if offer is None:
                continue

            store, price, discount, link = offer
            current = game.prices.get(store)

            if current is not None and price >= current:
                continue

            game.prices[store] = price

            if link:
                game.links[store] = link
            else:
                game.links.pop(store, None)

            if discount:
                game.discounts[store] = discount
            else:
                game.discounts.pop(store, None)

        return game if game.prices else None


def _deals(entry) -> list:
    deals = entry.get("deals") if isinstance(entry, dict) else None

    return deals if isinstance(deals, list) else []


def current_offers(entry, usd_to_cop: float) -> dict:
    """
    Precio vigente de cada tienda: `{tienda: (precio en COP, descuento)}`.

    Lo usa también el historial, para saber qué tiendas venden hoy el juego.
    """

    offers = {}

    for deal in _deals(entry):
        offer = _offer(deal, usd_to_cop)

        if offer is None:
            continue

        store, price, discount, _ = offer

        if store not in offers or price < offers[store][0]:
            offers[store] = (price, discount)

    return offers


def _offer(deal, usd_to_cop: float):
    """(tienda, precio en COP, descuento, enlace) o `None` si no sirve."""

    if not isinstance(deal, dict):
        return None

    shop = deal.get("shop")
    store = shop.get("name") if isinstance(shop, dict) else None
    price = deal.get("price")

    if not isinstance(store, str) or not store or store in EXCLUDED_SHOPS:
        return None

    amount = money_in_cop(price, usd_to_cop)

    if amount is None:
        return None

    discount = deal.get("cut")

    if (
        isinstance(discount, bool)
        or not isinstance(discount, int)
        or not 0 < discount <= 100
    ):
        discount = 0

    link = deal.get("url")

    return (
        store,
        amount,
        discount,
        link if isinstance(link, str) and link.startswith("https://") else None,
    )


def money_in_cop(price, usd_to_cop: float) -> Optional[float]:
    """Convierte un importe de IsThereAnyDeal a pesos; `None` si no se puede."""

    if not isinstance(price, dict):
        return None

    amount = price.get("amount")

    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        return None

    if amount < 0:
        return None

    currency = price.get("currency")

    if currency == "COP":
        return round(float(amount), 2)

    if currency == "USD":
        return round(float(amount) * usd_to_cop, 2)

    # Otra moneda no se puede comparar con las demás tiendas.
    return None


def _image(title: dict) -> Optional[str]:
    assets = title.get("assets")

    if not isinstance(assets, dict):
        return None

    for name in ("banner400", "banner600", "banner300", "boxart"):
        if isinstance(assets.get(name), str):
            return assets[name]

    return None
