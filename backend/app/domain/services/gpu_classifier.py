"""Clasificación aproximada de tarjetas gráficas en cinco niveles.

Los fabricantes publican la gráfica requerida como texto libre
("GeForce GTX 1060 6GB / Radeon RX 480"). Para compararla con la del usuario
se reduce cada modelo reconocido a un nivel:

    1 = integrada o muy antigua     4 = alta
    2 = básica                      5 = muy alta
    3 = media

Es una estimación por familias de modelos, no un benchmark.
"""

import re
import unicodedata
from typing import Optional

GPU_LEVEL_NAMES = {
    1: "integrada o muy básica",
    2: "básica",
    3: "media",
    4: "alta",
    5: "muy alta",
}

# `(?!\d)` evita que un modelo coincida con el prefijo de otro
# ("RX 560" dentro de "RX 5600").
_PATTERNS = {
    5: (
        r"rtx\s*(20[78]0|30[789]0|40[789]0|50[6789]0)(?!\d)",
        r"gtx\s*1080\s*ti",
        r"rx\s*(6[789]\d0|7[789]\d0|90[67]0)(?!\d)",
        r"titan",
    ),
    4: (
        r"rtx\s*(2060|3050|3060|4050|4060)(?!\d)",
        r"gtx\s*(1070|1080|1660)(?!\d)(?!\s*ti)",
        r"gtx\s*1070\s*ti",
        r"gtx\s*1660\s*ti",
        r"gtx\s*980\s*ti",
        r"rx\s*(5600|5700|6600|6650|7600)(?!\d)",
        r"vega\s*(56|64)(?!\d)",
        r"arc\s*(a580|a7[57]0|b5[78]0)(?!\d)",
    ),
    3: (
        r"gtx\s*(1060|1650|970|780|770)(?!\d)",
        r"gtx\s*1050\s*ti",
        r"gtx\s*980(?!\d)(?!\s*ti)",
        r"rx\s*(470|480|570|580|590|5500|6400|6500)(?!\d)",
        r"r9\s*(280|285|290|380|390)(?!\d)",
        r"r9\s*fury",
        r"arc\s*a3[18]0(?!\d)",
    ),
    2: (
        r"gtx\s*(960|950|760|680|670|660)(?!\d)",
        r"gtx\s*(1050|750)(?!\d)(?!\s*ti)",
        r"gtx\s*(750|650)\s*ti",
        r"gt\s*1030(?!\d)",
        r"rx\s*(460|550|560)(?!\d)",
        r"r7\s*(360|370)(?!\d)",
        r"r9\s*270(?!\d)",
        r"hd\s*7[89]\d0(?!\d)",
        r"\bmx\s*\d{3}(?!\d)",
    ),
    1: (
        r"intel\s*(u?hd|iris)",
        r"(u?hd|iris)\s*(graphics|graficos)",
        r"hd\s*intel",
        r"integrad",
        r"integrated",
        r"\bgt\s*\d{3}(?!\d)",
        r"geforce\s*[6789]\d{3}(?!\d)",
        r"gtx\s*(4[5-9]0|5[5-9]0)(?!\d)",
        r"gtx\s*650(?!\d)(?!\s*ti)",
        r"radeon\s*hd\s*[2-6]\d{3}(?!\d)",
        r"radeon\s*x\d{3,4}(?!\d)",
    ),
}


# Puntaje de benchmark a partir del cual empieza cada nivel. Solo se usa
# para tarjetas que las reglas por familia no reconocen (modelos nuevos).
_SCORE_FLOORS = ((3000, 5), (1040, 4), (500, 3), (200, 2))


def level_from_score(score: int) -> int:
    for floor, level in _SCORE_FLOORS:
        if score >= floor:
            return level

    return 1


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)

    text = "".join(
        character
        for character in text
        if not unicodedata.combining(character)
    )

    return re.sub(r"[®™©]", " ", text).casefold()


def classify_gpu(text: Optional[str]) -> Optional[int]:
    """
    Nivel de la gráfica descrita en `text`, o None si no se reconoce.

    Cuando el texto enumera varias alternativas ("GTX 1060 o RX 580 o
    Arc A380") cualquiera de ellas cumple el requisito, así que se toma
    el nivel más bajo reconocido.
    """

    if not text:
        return None

    normalized = _normalize(text)

    levels = [
        level
        for level, patterns in _PATTERNS.items()
        if any(re.search(pattern, normalized) for pattern in patterns)
    ]

    return min(levels) if levels else None
