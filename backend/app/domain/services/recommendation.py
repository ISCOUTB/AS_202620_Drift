"""
Recomendación de compra (ficha del problema: «recomendar la opción más
conveniente considerando precio, compatibilidad y rendimiento»).

La regla es corta para que se le pueda explicar al usuario (ADR-0019):

1. Por cada dispositivo se toma la tienda más barata de su plataforma.
2. Se descartan los dispositivos donde el juego no se vende o cuyo PC no
   alcanza los requisitos mínimos.
3. Gana la opción más barata, salvo que otra dé mejor experiencia por un
   poco más de dinero (hasta `EXTRA_FOR_BETTER_EXPERIENCE`).

Sin dispositivos no hay compatibilidad que considerar: gana el precio.
"""

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

from app.domain.services.platforms import PC, PLAYSTATION, XBOX, platform_of_store

# Experiencia que se espera del juego en un dispositivo.
RECOMMENDED = "recommended"  # el PC alcanza los requisitos recomendados
MINIMUM = "minimum"          # el PC solo alcanza los mínimos
CONSOLE = "console"          # una consola corre lo que vende su tienda
UNVERIFIED = "unverified"    # PC sin requisitos conocidos para comparar
INSUFFICIENT = "insufficient"  # el PC no alcanza los mínimos

_RANK = {RECOMMENDED: 2, CONSOLE: 2, MINIMUM: 1, UNVERIFIED: 1}

# Cuánto más se acepta pagar por pasar de «mínimo» a «recomendado» o consola.
EXTRA_FOR_BETTER_EXPERIENCE = 0.10

# Motivo por el que una opción quedó de primera.
CHEAPEST = "cheapest"
BETTER_EXPERIENCE = "better_experience"
ONLY_OPTION = "only_option"

# Motivo por el que un dispositivo quedó por fuera.
NOT_SOLD = "not_sold"

PLATFORM_OF_KIND = {"pc": PC, "playstation": PLAYSTATION, "xbox": XBOX}


@dataclass(frozen=True)
class DeviceVerdict:
    """Un dispositivo del usuario y cómo le iría con el juego."""

    device_id: str
    name: str
    kind: str
    experience: str

    @property
    def platform(self) -> str:
        return PLATFORM_OF_KIND[self.kind]


@dataclass(frozen=True)
class Option:
    """Comprar en una tienda, para jugar en un dispositivo."""

    store: str
    price: float
    discount: int
    platform: str
    experience: Optional[str] = None
    device: Optional[DeviceVerdict] = None


@dataclass(frozen=True)
class Excluded:
    device: DeviceVerdict
    reason: str


@dataclass(frozen=True)
class Recommendation:
    # Falso cuando no había dispositivos y solo se miró el precio.
    uses_devices: bool
    best: Optional[Option] = None
    reason: Optional[str] = None
    # Lo que se ahorra frente a la siguiente opción, o lo que cuesta de más
    # la mejor experiencia frente a la más barata.
    price_difference: float = 0
    alternatives: List[Option] = field(default_factory=list)
    excluded: List[Excluded] = field(default_factory=list)


def _cheapest_by_platform(
    prices: Dict[str, float],
    discounts: Dict[str, int],
) -> Dict[str, Option]:
    cheapest: Dict[str, Option] = {}

    # Orden fijo: con el mismo precio gana siempre la misma tienda.
    for store in sorted(prices):
        platform = platform_of_store(store)
        current = cheapest.get(platform)

        if current is None or prices[store] < current.price:
            cheapest[platform] = Option(
                store=store,
                price=prices[store],
                discount=int(discounts.get(store) or 0),
                platform=platform,
            )

    return cheapest


def _by_price(options: Iterable[Option]) -> List[Option]:
    return sorted(
        options,
        key=lambda option: (
            option.price,
            -_RANK.get(option.experience, 0),
            option.experience == UNVERIFIED,
        ),
    )


def recommend(
    prices: Dict[str, float],
    discounts: Optional[Dict[str, int]] = None,
    devices: Optional[Iterable[DeviceVerdict]] = None,
) -> Recommendation:
    by_platform = _cheapest_by_platform(prices, discounts or {})
    devices = list(devices or ())

    if not devices:
        ordered = _by_price(by_platform.values())

        if not ordered:
            return Recommendation(uses_devices=False)

        return Recommendation(
            uses_devices=False,
            best=ordered[0],
            reason=ONLY_OPTION if len(ordered) == 1 else CHEAPEST,
            price_difference=(
                ordered[1].price - ordered[0].price if len(ordered) > 1 else 0
            ),
            alternatives=ordered[1:],
        )

    options: List[Option] = []
    excluded: List[Excluded] = []
    consoles_seen = set()

    for device in devices:
        # Dos consolas iguales son la misma opción de compra.
        if device.kind != "pc":
            if device.kind in consoles_seen:
                continue

            consoles_seen.add(device.kind)

        offer = by_platform.get(device.platform)

        if offer is None:
            excluded.append(Excluded(device, NOT_SOLD))
        elif device.experience == INSUFFICIENT:
            excluded.append(Excluded(device, INSUFFICIENT))
        else:
            options.append(
                Option(
                    store=offer.store,
                    price=offer.price,
                    discount=offer.discount,
                    platform=offer.platform,
                    experience=device.experience,
                    device=device,
                )
            )

    ordered = _by_price(options)

    if not ordered:
        return Recommendation(uses_devices=True, excluded=excluded)

    cheapest = ordered[0]
    best = cheapest
    reason = ONLY_OPTION if len(ordered) == 1 else CHEAPEST

    better = [
        option
        for option in ordered[1:]
        if _RANK[option.experience] > _RANK[cheapest.experience]
        and option.price <= cheapest.price * (1 + EXTRA_FOR_BETTER_EXPERIENCE)
    ]

    if better:
        best = better[0]
        reason = BETTER_EXPERIENCE

    alternatives = [option for option in ordered if option is not best]

    if reason == BETTER_EXPERIENCE:
        difference = best.price - cheapest.price
    elif alternatives:
        difference = alternatives[0].price - best.price
    else:
        difference = 0

    return Recommendation(
        uses_devices=True,
        best=best,
        reason=reason,
        price_difference=difference,
        alternatives=alternatives,
        excluded=excluded,
    )
