"""
Precio de hoy de varios juegos a la vez, para las alertas de favoritos
(ADR-0021).

Solo consulta tiendas de PC:

- **Steam**, en pesos de Colombia, una llamada por juego (sin llave), en
  paralelo.
- **Las demás tiendas de PC**, por IsThereAnyDeal: una llamada para traducir
  los identificadores de Steam y otra para los precios de todos los juegos
  juntos. Sin la llave de IsThereAnyDeal solo se consulta Steam.

Los juegos que solo existen en una tienda de consola no se consultan.
Cada precio se conserva una hora.
"""

import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from typing import Callable, Dict, Iterable, List, Optional, Set

from app.domain.ports.current_price_source import CurrentPriceSource
from app.domain.ports.exchange_rate_provider import ExchangeRateProvider
from app.domain.services.price_alerts import CurrentPrice
from app.infrastructure.external.isthereanydeal.itad_client import (
    SOURCE_NAME as ITAD_SOURCE,
    ItadClient,
)
from app.infrastructure.external.isthereanydeal.itad_game_repository import (
    ID_PREFIX,
    current_offers,
)
from app.infrastructure.external.isthereanydeal.itad_price_history_repository import (
    STEAM_SHOP_ID,
)
from app.infrastructure.external.resilient_http import ExternalSourceError
from app.infrastructure.observability import log_event

logger = logging.getLogger("drift")

TTL_SECONDS = 60 * 60
# Plazo de las dos llamadas a IsThereAnyDeal juntas.
ITAD_DEADLINE_SECONDS = 5.0
STEAM_WORKERS = 6
MAX_REMEMBERED = 2000

_ITAD_ID = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)


def _cheapest(offers: Dict[str, float]) -> Optional[CurrentPrice]:
    if not offers:
        return None

    # Orden fijo: con el mismo precio gana siempre la misma tienda.
    store = min(sorted(offers), key=lambda name: offers[name])

    return CurrentPrice(store=store, price=offers[store])


class StoreCurrentPriceSource(CurrentPriceSource):
    def __init__(
        self,
        steam_prices: Callable[[str], Optional[tuple]],
        itad_client: Optional[ItadClient] = None,
        exchange_rates: Optional[ExchangeRateProvider] = None,
        clock: Callable[[], float] = time.monotonic,
    ):
        # Entrega (precio normal, precio de hoy, descuento) de Steam en pesos.
        self._steam_prices = steam_prices
        self._itad = itad_client if exchange_rates is not None else None
        self._exchange_rates = exchange_rates
        self._clock = clock
        # Identificador -> (cuándo, mejor precio o None si no tiene precio).
        self._cache: Dict[str, tuple] = {}
        self._lock = Lock()

    def best_prices(self, game_ids: Iterable[str]) -> Dict[str, CurrentPrice]:
        wanted = [
            game_id
            for game_id in dict.fromkeys(game_ids)
            if isinstance(game_id, str) and _can_check(game_id)
        ]

        now = self._clock()
        result: Dict[str, CurrentPrice] = {}
        missing: List[str] = []

        with self._lock:
            for game_id in wanted:
                entry = self._cache.get(game_id)

                if entry and now - entry[0] < TTL_SECONDS:
                    if entry[1] is not None:
                        result[game_id] = entry[1]
                else:
                    missing.append(game_id)

        if not missing:
            return result

        offers, answered = self._load(missing)

        with self._lock:
            for game_id in missing:
                best = _cheapest(offers.get(game_id, {}))

                if best is not None:
                    result[game_id] = best

                # «Sin precio» solo se recuerda si alguna fuente respondió;
                # si todas fallaron, la próxima visita vuelve a intentar.
                if game_id in answered:
                    self._cache[game_id] = (now, best)

            self._forget_oldest()

        return result

    def _load(self, game_ids: List[str]):
        offers: Dict[str, Dict[str, float]] = {game_id: {} for game_id in game_ids}
        answered: Set[str] = set()

        self._load_steam(game_ids, offers, answered)

        if self._itad is not None:
            self._load_itad(game_ids, offers, answered)

        return offers, answered

    def _load_steam(self, game_ids, offers, answered) -> None:
        steam_ids = [game_id for game_id in game_ids if game_id.isdecimal()]

        if not steam_ids:
            return

        with ThreadPoolExecutor(
            max_workers=min(STEAM_WORKERS, len(steam_ids))
        ) as pool:
            prices = list(pool.map(self._steam_price, steam_ids))

        for game_id, price in zip(steam_ids, prices):
            if price is not None:
                offers[game_id]["Steam"] = price
                answered.add(game_id)

    def _steam_price(self, app_id: str) -> Optional[float]:
        try:
            found = self._steam_prices(app_id)
        except Exception:  # noqa: BLE001  una fuente caída no rompe la lista
            return None

        return float(found[1]) if found else None

    def _load_itad(self, game_ids, offers, answered) -> None:
        budget = self._itad.new_budget(ITAD_DEADLINE_SECONDS)

        try:
            itad_ids = self._itad_ids(game_ids, budget)

            if not itad_ids:
                return

            priced = self._itad.post(
                "/games/prices/v3",
                sorted(set(itad_ids.values())),
                {"country": "CO", "vouchers": "false"},
                budget,
            )

            if not isinstance(priced, list):
                raise ExternalSourceError(ITAD_SOURCE, "invalid_response")

            usd_to_cop = self._exchange_rates.usd_to_cop()
            by_itad_id = {
                entry["id"]: current_offers(entry, usd_to_cop)
                for entry in priced
                if isinstance(entry, dict) and isinstance(entry.get("id"), str)
            }
        except Exception as error:  # noqa: BLE001
            log_event(
                logger,
                "current_prices_partial",
                source=ITAD_SOURCE,
                cause=getattr(error, "reason", type(error).__name__),
            )
            return

        for game_id, itad_id in itad_ids.items():
            answered.add(game_id)

            for store, (price, _discount) in by_itad_id.get(itad_id, {}).items():
                current = offers[game_id].get(store)

                if current is None or price < current:
                    offers[game_id][store] = price

    def _itad_ids(self, game_ids, budget) -> Dict[str, str]:
        """Identificador de IsThereAnyDeal de cada juego que se puede consultar."""

        found = _known_itad_ids(game_ids)
        keys = {
            f"app/{game_id}": game_id
            for game_id in game_ids
            if not game_id.startswith(ID_PREFIX) and game_id.isdecimal()
        }

        if keys:
            found.update(self._steam_to_itad(keys, budget))

        return found

    def _steam_to_itad(self, keys: Dict[str, str], budget) -> Dict[str, str]:
        """Pregunta a IsThereAnyDeal qué juego suyo es cada juego de Steam."""

        answer = self._itad.post(
            f"/lookup/id/shop/{STEAM_SHOP_ID}/v1",
            list(keys),
            None,
            budget,
        )

        if not isinstance(answer, dict):
            raise ExternalSourceError(ITAD_SOURCE, "invalid_response")

        return {
            game_id: answer[key]
            for key, game_id in keys.items()
            if isinstance(answer.get(key), str) and _ITAD_ID.match(answer[key])
        }

    def _forget_oldest(self) -> None:
        if len(self._cache) <= MAX_REMEMBERED:
            return

        for game_id, _ in sorted(
            self._cache.items(), key=lambda item: item[1][0]
        )[: len(self._cache) - MAX_REMEMBERED]:
            del self._cache[game_id]


def _known_itad_ids(game_ids) -> Dict[str, str]:
    """Los juegos que ya traen su identificador de IsThereAnyDeal."""

    return {
        game_id: game_id[len(ID_PREFIX):]
        for game_id in game_ids
        if game_id.startswith(ID_PREFIX) and _ITAD_ID.match(game_id[len(ID_PREFIX):])
    }


def _can_check(game_id: str) -> bool:
    """Solo los juegos de Steam o de IsThereAnyDeal tienen tiendas de PC."""

    return game_id.isdecimal() or game_id.startswith(ID_PREFIX)
