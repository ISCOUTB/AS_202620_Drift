import logging
import re
from collections import OrderedDict
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Callable, Optional, cast

from app.domain.model.price_history import PriceChange, PriceHistory
from app.domain.ports.exchange_rate_provider import ExchangeRateProvider
from app.domain.ports.price_history_repository import PriceHistoryRepository
from app.domain.services.price_timeline import best_price_timeline, lowest_point
from app.infrastructure.external.isthereanydeal.itad_client import (
    SOURCE_NAME,
    ItadClient,
)
from app.infrastructure.external.isthereanydeal.itad_game_repository import (
    EXCLUDED_SHOPS,
    ID_PREFIX,
    current_offers,
    money_in_cop,
)
from app.infrastructure.external.resilient_http import ExternalSourceError
from app.infrastructure.external.single_flight_cache import SingleFlightCache
from app.infrastructure.observability import log_event

logger = logging.getLogger("drift")

HISTORY_DAYS = 365

# El historial cambia pocas veces al día: una hora de caché ahorra cuota.
HISTORY_TTL_SECONDS = 60 * 60
# La equivalencia entre el juego de Steam y el de IsThereAnyDeal no cambia.
LOOKUP_TTL_SECONDS = 24 * 60 * 60

MAX_REMEMBERED = 200

# Tres llamadas encadenadas (equivalencia, cambios y precios de hoy).
HISTORY_DEADLINE_SECONDS = 6.0

# Identificador de Steam dentro de IsThereAnyDeal.
STEAM_SHOP_ID = 61

_ITAD_ID = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)

_UNKNOWN = object()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ItadPriceHistoryRepository(PriceHistoryRepository):
    """
    Historial de precios de IsThereAnyDeal para los últimos 12 meses.

    DRIFT no guarda el historial: lo pide cuando alguien abre un juego. Los
    importes llegan en dólares y se convierten a pesos con la tasa de hoy,
    así que los valores antiguos son aproximados.

    Si la fuente falla, entrega el último historial que obtuvo para ese
    juego, marcado con la fecha en que lo consiguió.
    """

    def __init__(
        self,
        client: ItadClient,
        exchange_rates: ExchangeRateProvider,
        now: Callable[[], datetime] = _utc_now,
        steam_prices: Optional[Callable[[str], Optional[tuple]]] = None,
    ):
        self._client = client
        self._exchange_rates = exchange_rates
        self._now = now
        # Entrega (precio normal, precio de hoy, descuento) de Steam en pesos.
        # Con eso la serie de Steam entra al historial en moneda local.
        self._steam_prices = steam_prices
        self._histories = SingleFlightCache(ttl_seconds=HISTORY_TTL_SECONDS)
        self._lookups = SingleFlightCache(ttl_seconds=LOOKUP_TTL_SECONDS)
        self._remembered: "OrderedDict[str, tuple]" = OrderedDict()
        self._lock = Lock()

    def get(self, game_id: str) -> Optional[PriceHistory]:
        try:
            history = self._histories.get_or_load(
                game_id,
                lambda: self._load(game_id),
            )
        except ExternalSourceError as error:
            remembered = self._recall(game_id)

            if remembered is None:
                raise

            log_event(
                logger,
                "source_served_from_backup",
                source=SOURCE_NAME,
                cause=error.reason,
                operation="price_history",
            )

            return remembered

        if history is not None:
            self._remember(game_id, history)

        return history

    def _load(self, game_id: str) -> Optional[PriceHistory]:
        budget = self._client.new_budget(HISTORY_DEADLINE_SECONDS)
        itad_id = self._itad_id(game_id, budget)

        if itad_id is None:
            return None

        since = self._now() - timedelta(days=HISTORY_DAYS)

        log = self._client.get(
            "/games/history/v2",
            {
                "id": itad_id,
                "country": "CO",
                "since": since.strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            budget,
        )

        if not isinstance(log, list):
            raise ExternalSourceError(SOURCE_NAME, "invalid_response")

        priced = self._client.post(
            "/games/prices/v3",
            [itad_id],
            {"country": "CO", "vouchers": "false"},
            budget,
        )

        if not isinstance(priced, list):
            raise ExternalSourceError(SOURCE_NAME, "invalid_response")

        usd_to_cop = self._exchange_rates.usd_to_cop()
        steam = self._steam_in_colombia(game_id, itad_id, budget)

        changes = [
            change
            for change in (
                _change(entry, usd_to_cop, steam[0] if steam else None)
                for entry in log
            )
            if change is not None
        ]

        return PriceHistory(
            game_id=game_id,
            since=since,
            points=self._timeline(changes, priced, usd_to_cop, steam),
            lowest=lowest_point(changes),
            steam_best_discount=_steam_best_discount(log),
        )

    def _steam_in_colombia(self, game_id: str, itad_id: str, budget):
        """
        Precio de Steam en pesos para este juego, o `None`.

        IsThereAnyDeal solo conoce el precio de Steam en dólares, que no es
        el que se paga en Colombia. Steam aplica el mismo porcentaje de
        descuento en todas las regiones, así que el precio de cada fecha se
        reconstruye con el precio normal de hoy en Colombia y el descuento
        que tuvo ese día.
        """

        if self._steam_prices is None:
            return None

        steam_id = game_id if game_id.isdecimal() else None

        if steam_id is None:
            try:
                known = self._client.post(
                    f"/lookup/shop/{STEAM_SHOP_ID}/id/v1",
                    [itad_id],
                    None,
                    budget,
                )
            except ExternalSourceError:
                return None

            entries = known.get(itad_id) if isinstance(known, dict) else None

            steam_id = next(
                (
                    entry[4:]
                    for entry in entries or []
                    if isinstance(entry, str)
                    and entry.startswith("app/")
                    and entry[4:].isdecimal()
                ),
                None,
            )

        return self._steam_prices(steam_id) if steam_id else None

    def _timeline(self, changes, priced, usd_to_cop: float, steam=None):
        """
        La línea del mejor precio, terminada en el precio de hoy.

        El registro de cambios no dice cuándo una tienda dejó de vender el
        juego. Para que una oferta que ya no existe no figure como el mejor
        precio actual, la línea usa solo las tiendas que lo venden hoy y
        cierra con el mejor precio vigente.
        """

        entry = priced[0] if priced and isinstance(priced[0], dict) else {}
        offers = current_offers(entry, usd_to_cop)

        if steam is not None:
            offers["Steam"] = (steam[1], steam[2])

        if not offers:
            return best_price_timeline(changes)

        timeline = best_price_timeline(
            change for change in changes if change.store in offers
        )

        store, (price, discount) = min(
            offers.items(),
            key=lambda item: (item[1][0], item[0]),
        )
        last = timeline[-1] if timeline else None

        if last is None or last.price != price or last.store != store:
            timeline.append(
                PriceChange(
                    date=self._now(),
                    store=store,
                    price=price,
                    discount=discount,
                )
            )

        return timeline

    def _itad_id(self, game_id: str, budget) -> Optional[str]:
        if game_id.startswith(ID_PREFIX):
            itad_id = game_id[len(ID_PREFIX):]

            return itad_id if _ITAD_ID.match(itad_id) else None

        # Solo los juegos de Steam (identificador numérico) tienen una
        # equivalencia; los de consola no están en IsThereAnyDeal.
        if not game_id.isdecimal():
            return None

        found = self._lookups.get_or_load(
            game_id,
            lambda: self._lookup_steam(game_id, budget),
        )

        return None if found is _UNKNOWN else found

    def _lookup_steam(self, steam_id: str, budget):
        key = f"app/{steam_id}"

        found = self._client.post(
            f"/lookup/id/shop/{STEAM_SHOP_ID}/v1",
            [key],
            None,
            budget,
        )

        if not isinstance(found, dict):
            raise ExternalSourceError(SOURCE_NAME, "invalid_response")

        itad_id = found.get(key)

        if isinstance(itad_id, str) and _ITAD_ID.match(itad_id):
            return itad_id

        # «No existe» también se recuerda, para no preguntar en cada visita.
        return _UNKNOWN

    def _remember(self, game_id: str, history: PriceHistory) -> None:
        with self._lock:
            self._remembered[game_id] = (history, self._now())
            self._remembered.move_to_end(game_id)

            while len(self._remembered) > MAX_REMEMBERED:
                self._remembered.popitem(last=False)

    def _recall(self, game_id: str) -> Optional[PriceHistory]:
        with self._lock:
            remembered = self._remembered.get(game_id)

        if remembered is None:
            return None

        history, obtained_at = remembered

        return cast(PriceHistory, replace(history, cached_at=obtained_at))


def _change(
    entry,
    usd_to_cop: float,
    steam_regular: Optional[float] = None,
) -> Optional[PriceChange]:
    """Un cambio de precio utilizable, o `None` si la entrada no sirve."""

    if not isinstance(entry, dict):
        return None

    shop = entry.get("shop")
    deal = entry.get("deal")
    store = shop.get("name") if isinstance(shop, dict) else None

    if not isinstance(store, str) or not store or not isinstance(deal, dict):
        return None

    if store == "Steam":
        return _steam_change(entry, deal, steam_regular)

    if store in EXCLUDED_SHOPS:
        return None

    price = money_in_cop(deal.get("price"), usd_to_cop)
    date = _date(entry.get("timestamp"))

    if price is None or date is None:
        return None

    discount = deal.get("cut")

    if (
        isinstance(discount, bool)
        or not isinstance(discount, int)
        or not 0 < discount <= 100
    ):
        discount = 0

    return PriceChange(date=date, store=store, price=price, discount=discount)


def _steam_change(entry, deal, steam_regular) -> Optional[PriceChange]:
    """El precio de Steam ese día, en pesos: precio normal menos su descuento."""

    date = _date(entry.get("timestamp"))
    discount = deal.get("cut")

    if steam_regular is None or date is None:
        return None

    if (
        isinstance(discount, bool)
        or not isinstance(discount, int)
        or not 0 <= discount <= 100
    ):
        return None

    return PriceChange(
        date=date,
        store="Steam",
        price=round(steam_regular * (100 - discount) / 100, 2),
        discount=discount,
    )


def _steam_best_discount(log) -> Optional[PriceChange]:
    """El mayor descuento de Steam en el periodo; si se repite, el más reciente."""

    best = None

    for entry in log:
        if not isinstance(entry, dict):
            continue

        shop = entry.get("shop")
        deal = entry.get("deal")

        if (
            not isinstance(shop, dict)
            or shop.get("name") != "Steam"
            or not isinstance(deal, dict)
        ):
            continue

        discount = deal.get("cut")
        date = _date(entry.get("timestamp"))

        if (
            date is None
            or isinstance(discount, bool)
            or not isinstance(discount, int)
            or not 0 < discount <= 100
        ):
            continue

        if best is None or (discount, date) > (best.discount, best.date):
            # El importe en dólares de Steam no aplica a Colombia: no se usa.
            best = PriceChange(date=date, store="Steam", price=0.0, discount=discount)

    return best


def _date(value) -> Optional[datetime]:
    if not isinstance(value, str):
        return None

    try:
        date = datetime.fromisoformat(value)
    except ValueError:
        return None

    if date.tzinfo is None:
        return None

    return date.astimezone(timezone.utc)
