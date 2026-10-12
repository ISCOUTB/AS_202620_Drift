"""Clasificación aproximada de procesadores en cinco niveles.

Igual que con las gráficas, el requisito llega como texto libre
("Intel Core i5-8400 / AMD Ryzen 3 3300X"). Cada modelo reconocido se reduce
a un nivel según su gama (i3, i5, i7… / Ryzen 3, 5, 7…) y su generación:

    1 = muy básico o antiguo     4 = alto
    2 = básico                   5 = muy alto
    3 = medio

Es una estimación por familias, no un benchmark. Los textos genéricos
("Dual Core 2.4 GHz") no se clasifican.
"""

import re
import unicodedata
from typing import List, Optional

_INTEL_CORE = re.compile(r"\bi([3579])[\s-]*(\d{4,5})([a-z]{0,2}\d?)")
_INTEL_ULTRA = re.compile(r"ultra\s*([579])")
_RYZEN = re.compile(r"ryzen\s*([3579])\s*(?:pro\s*)?(\d{4})([a-z]{0,2})")
_FX = re.compile(r"\bfx[\s-]*(\d)\d{3}")
_CORE_2 = re.compile(r"core\s*2\s*(duo|quad|extreme)")
_AMD_A_SERIES = re.compile(r"\ba(4|6|8|10|12)[\s-]\d{4}")
_OLD_FAMILY_WORDS = ("pentium", "celeron", "atom", "athlon", "phenom")

# Sufijos de bajo consumo de portátil: rinden por debajo de su gama.
_LOW_POWER_SUFFIXES = ("u", "y", "g1", "g4", "g7")

# Puntaje de benchmark a partir del cual empieza cada nivel. Solo se usa
# para procesadores que las reglas por familia no reconocen.
_SCORE_FLOORS = ((9000, 5), (5000, 4), (3500, 3), (2000, 2))


def cpu_level_from_score(score: int) -> int:
    for floor, level in _SCORE_FLOORS:
        if score >= floor:
            return level

    return 1


def _intel_level(tier: int, generation: int) -> int:
    if generation <= 3:
        levels = {3: 1, 5: 2, 7: 2, 9: 2}
    elif generation <= 7:
        levels = {3: 1, 5: 2, 7: 3, 9: 3}
    elif generation <= 9:
        levels = {3: 2, 5: 3, 7: 4, 9: 4}
    elif generation <= 11:
        levels = {3: 3, 5: 4, 7: 4, 9: 5}
    else:
        levels = {3: 3, 5: 4, 7: 5, 9: 5}

    return levels[tier]


def _ryzen_level(tier: int, series: int) -> int:
    if series <= 2:
        levels = {3: 2, 5: 3, 7: 3, 9: 4}
    elif series <= 4:
        levels = {3: 3, 5: 4, 7: 4, 9: 5}
    else:
        levels = {3: 3, 5: 4, 7: 5, 9: 5}

    return levels[tier]


def _low_power_penalty(level: int, suffix: str) -> int:
    return max(1, level - 1) if suffix in _LOW_POWER_SUFFIXES else level


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)

    text = "".join(
        character
        for character in text
        if not unicodedata.combining(character)
    )

    return re.sub(r"[®™©]", " ", text).casefold()


def _is_old_family(normalized: str) -> bool:
    return bool(
        _CORE_2.search(normalized)
        or _AMD_A_SERIES.search(normalized)
        or any(word in normalized for word in _OLD_FAMILY_WORDS)
    )


def _recognized_levels(normalized: str) -> List[int]:
    levels = []

    for tier, digits, suffix in _INTEL_CORE.findall(normalized):
        # "i5-12400": generación 12; "i5-8400": generación 8. Los modelos de
        # cuatro cifras que empiezan por 1 son de portátil de 10.ª generación
        # en adelante ("i5-1135G7" es de la 11.ª).
        two_digit_generation = len(digits) == 5 or digits[0] == "1"
        generation = int(digits[:2]) if two_digit_generation else int(digits[0])

        levels.append(
            _low_power_penalty(_intel_level(int(tier), generation), suffix)
        )

    for tier in _INTEL_ULTRA.findall(normalized):
        levels.append(4 if tier == "5" else 5)

    for tier, digits, suffix in _RYZEN.findall(normalized):
        levels.append(
            _low_power_penalty(_ryzen_level(int(tier), int(digits[0])), suffix)
        )

    for family in _FX.findall(normalized):
        levels.append(1 if family == "4" else 2)

    if "threadripper" in normalized:
        levels.append(5)

    if _is_old_family(normalized):
        levels.append(1)

    return levels


def classify_cpu(text: Optional[str]) -> Optional[int]:
    """
    Nivel del procesador descrito en `text`, o None si no se reconoce.

    Cuando el texto enumera varias alternativas, cualquiera de ellas cumple
    el requisito, así que se toma el nivel más bajo reconocido.
    """

    if not text:
        return None

    levels = _recognized_levels(_normalize(text))

    return min(levels) if levels else None
