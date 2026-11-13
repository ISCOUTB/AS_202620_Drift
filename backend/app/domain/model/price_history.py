from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass(frozen=True)
class PriceChange:
    """Una tienda cambió el precio de un juego en un momento dado."""

    date: datetime
    store: str
    price: float
    discount: int = 0


@dataclass(frozen=True)
class PriceHistory:
    """
    Cómo se movió el mejor precio de un juego entre las tiendas de PC.

    `points` trae un punto cada vez que cambió el mejor precio disponible,
    del más antiguo al más reciente, solo con las tiendas que hoy venden el
    juego. `lowest` es el precio más bajo que registró cualquier tienda en
    el periodo. `steam_best_discount` es el mayor descuento que tuvo Steam:
    su precio en dólares no aplica a Colombia, pero el porcentaje sí.
    `cached_at` solo tiene valor cuando la fuente no respondió y se entrega
    el último historial que se había obtenido.
    """

    game_id: str
    since: datetime
    points: List[PriceChange]
    lowest: Optional[PriceChange]
    cached_at: Optional[datetime] = None
    steam_best_discount: Optional[PriceChange] = None

    @property
    def current(self) -> Optional[PriceChange]:
        return self.points[-1] if self.points else None
