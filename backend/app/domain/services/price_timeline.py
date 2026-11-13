from typing import Iterable, List, Optional

from app.domain.model.price_history import PriceChange


def best_price_timeline(changes: Iterable[PriceChange]) -> List[PriceChange]:
    """
    Convierte los cambios de precio de cada tienda en una sola línea: el
    mejor precio que se podía conseguir en cada momento.

    Recorre los cambios del más antiguo al más reciente recordando el último
    precio de cada tienda. Cada vez que el más barato de todos cambia, se
    agrega un punto con la tienda que lo ofrece.

    De una tienda no se sabe nada hasta su primer cambio dentro del periodo,
    así que al comienzo la línea puede quedar por encima del precio real.
    """

    last_by_store = {}
    timeline: List[PriceChange] = []

    for change in sorted(changes, key=lambda item: item.date):
        last_by_store[change.store] = change

        best = min(
            last_by_store.values(),
            key=lambda item: (item.price, item.store),
        )

        previous = timeline[-1] if timeline else None

        if (
            previous is not None
            and previous.price == best.price
            and previous.store == best.store
        ):
            continue

        timeline.append(
            PriceChange(
                date=change.date,
                store=best.store,
                price=best.price,
                discount=best.discount,
            )
        )

    return timeline


def lowest_point(timeline: List[PriceChange]) -> Optional[PriceChange]:
    """El punto más barato; si hay empate, el más reciente."""

    if not timeline:
        return None

    return min(timeline, key=lambda item: (item.price, -item.date.timestamp()))
