import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, List, Optional

from app.domain.model.account import Favorite, User
from app.domain.ports.account_repository import AccountRepository
from app.domain.ports.current_price_source import CurrentPriceSource
from app.domain.services.price_alerts import CurrentPrice, PriceAlert, price_alert

logger = logging.getLogger("drift")

# Solo los más recientes se consultan en cada visita, para cuidar la cuota.
MAX_CHECKED = 30


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class FavoriteStatus:
    favorite: Favorite
    # `None` si no se pudo consultar (fuente caída o juego solo de consola).
    current: Optional[CurrentPrice]
    alert: Optional[PriceAlert]


@dataclass(frozen=True)
class FavoriteAlerts:
    checked_at: datetime
    statuses: List[FavoriteStatus]

    @property
    def alerts(self) -> int:
        return sum(1 for status in self.statuses if status.alert is not None)


class CheckFavoriteAlerts:
    """
    Revisa el precio de hoy de los favoritos de una persona y dice cuáles
    llegaron a su precio objetivo o bajaron (ADR-0021).

    Se ejecuta cuando la persona entra a DRIFT: no hay un proceso en segundo
    plano ni correos.
    """

    def __init__(
        self,
        accounts: AccountRepository,
        prices: CurrentPriceSource,
        now: Callable[[], datetime] = _utc_now,
    ):
        self._accounts = accounts
        self._prices = prices
        self._now = now

    def execute(self, user: User) -> FavoriteAlerts:
        favorites = self._accounts.list_favorites(user.id)
        to_check = [favorite.game_id for favorite in favorites[:MAX_CHECKED]]

        try:
            current = self._prices.best_prices(to_check) if to_check else {}
        except Exception:  # noqa: BLE001  las alertas nunca rompen la página
            logger.warning("No se pudieron consultar los precios de los favoritos")
            current = {}

        statuses = []

        for favorite in favorites:
            price = current.get(favorite.game_id)

            statuses.append(
                FavoriteStatus(
                    favorite=favorite,
                    current=price,
                    alert=price_alert(favorite.price, favorite.target_price, price),
                )
            )

        return FavoriteAlerts(checked_at=self._now(), statuses=statuses)
