"""
Alertas de precio de los favoritos (ADR-0021).

Un favorito avisa cuando:

1. Tiene un precio objetivo y el precio de hoy llegó a él o bajó más, o
2. no tiene objetivo y el precio de hoy está al menos `MIN_DROP` por debajo
   del que tenía al guardarlo.

El margen evita avisos falsos: los precios de las tiendas de PC distintas
de Steam vienen en dólares y se convierten con la tasa del día, así que
cambian unos pesos cada día sin que la tienda haya cambiado nada.
"""

from dataclasses import dataclass
from typing import Optional

TARGET_REACHED = "target_reached"
PRICE_DROPPED = "price_dropped"

# Baja mínima, frente al precio guardado, para avisar sin precio objetivo.
MIN_DROP = 0.05


@dataclass(frozen=True)
class CurrentPrice:
    """El mejor precio de hoy de un juego y la tienda que lo tiene."""

    store: str
    price: float


@dataclass(frozen=True)
class PriceAlert:
    reason: str
    # Cuánto menos cuesta hoy frente al precio guardado; `None` si el
    # favorito se guardó sin precio.
    saved_difference: Optional[float]


def price_alert(
    saved_price: Optional[float],
    target_price: Optional[float],
    current: Optional[CurrentPrice],
) -> Optional[PriceAlert]:
    if current is None:
        return None

    difference = (
        round(saved_price - current.price, 2) if saved_price is not None else None
    )

    if target_price is not None and current.price <= target_price:
        return PriceAlert(TARGET_REACHED, difference)

    if (
        target_price is None
        and saved_price is not None
        and saved_price > 0
        and current.price <= saved_price * (1 - MIN_DROP)
    ):
        return PriceAlert(PRICE_DROPPED, difference)

    return None
