import html
import math
import re
import unicodedata
from typing import Optional

import httpx

from app.domain.model.game_requirements import GameRequirements
from app.domain.ports.game_requirements_repository import (
    GameRequirementsRepository,
)
from app.domain.services.cpu_classifier import classify_cpu
from app.domain.services.gpu_classifier import classify_gpu
from app.infrastructure.external.single_flight_cache import SingleFlightCache

# Etiquetas con las que Steam nombra cada requisito, en español e inglés.
_LABELS = {
    "os": {"so", "os"},
    "processor": {"procesador", "processor"},
    "memory": {"memoria", "memory"},
    "graphics": {"graficos", "graphics", "tarjeta grafica", "video card", "video"},
    "storage": {
        "almacenamiento",
        "storage",
        "disco duro",
        "hard drive",
        "hard disk space",
    },
}

# Repeticiones acotadas: la búsqueda no puede retroceder sin límite.
_SIZE = re.compile(r"(\d{1,6}(?:[.,]\d{1,3})?)\s{0,3}(gb|mb)", re.IGNORECASE)

# Los identificadores de Steam son enteros positivos de hasta 8 cifras.
_MAX_APP_ID = 99_999_999


def _plain(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(html.unescape(text).split())


def _label_key(label: str) -> Optional[str]:
    normalized = unicodedata.normalize("NFKD", label)

    normalized = "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )

    normalized = normalized.replace("*", "").replace(":", "").strip().casefold()

    for key, names in _LABELS.items():
        if normalized in names:
            return key

    return None


def parse_requirement_block(block: Optional[str]) -> dict:
    """Convierte el HTML de Steam en {'memory': '8 GB de RAM', ...}."""

    details = {}

    for item in re.split(r"<li[^>]*>", block or "")[1:]:
        match = re.match(r"\s*<strong>(.*?)</strong>(.*)", item, re.DOTALL)

        if not match:
            continue

        key = _label_key(_plain(match.group(1)))
        value = _plain(match.group(2))

        if key and value and key not in details:
            details[key] = value

    return details


def _size_in_gb(text: Optional[str]) -> Optional[int]:
    match = _SIZE.search(text or "")

    if not match:
        return None

    amount = float(match.group(1).replace(",", "."))

    if match.group(2).casefold() == "mb":
        amount /= 1024

    return max(1, math.ceil(amount))


class SteamGameRequirementsRepository(GameRequirementsRepository):
    """Adaptador que obtiene de Steam los requisitos de PC de un juego."""

    _url = "https://store.steampowered.com/api/appdetails"

    def __init__(self):
        # Los requisitos publicados casi nunca cambian.
        self._cache = SingleFlightCache(ttl_seconds=24 * 60 * 60)

    def get_by_game_id(self, game_id: int) -> Optional[GameRequirements]:
        if not 0 < game_id <= _MAX_APP_ID:
            return None

        try:
            return self._cache.get_or_load(
                game_id,
                lambda: self._fetch(game_id),
            )
        except (httpx.HTTPError, ValueError):
            # Sin respuesta de Steam no hay requisitos que comparar.
            return None

    def _fetch(self, game_id: int) -> Optional[GameRequirements]:
        response = httpx.get(
            self._url,
            params={
                "appids": game_id,
                "cc": "co",
                "l": "spanish",
            },
            timeout=5.0,
        )

        response.raise_for_status()

        payload = response.json() or {}
        game_data = (payload.get(str(game_id)) or {}).get("data") or {}
        requirements = game_data.get("pc_requirements")

        if not isinstance(requirements, dict):
            return None

        minimum = parse_requirement_block(requirements.get("minimum"))
        recommended = parse_requirement_block(requirements.get("recommended"))

        minimum_ram_gb = _size_in_gb(minimum.get("memory"))

        if minimum_ram_gb is None:
            return None

        return GameRequirements(
            game_id=game_id,
            minimum_ram_gb=minimum_ram_gb,
            recommended_ram_gb=(
                _size_in_gb(recommended.get("memory")) or minimum_ram_gb
            ),
            minimum_gpu_score=classify_gpu(minimum.get("graphics")),
            recommended_gpu_score=classify_gpu(recommended.get("graphics")),
            minimum_storage_gb=_size_in_gb(minimum.get("storage")),
            recommended_storage_gb=_size_in_gb(recommended.get("storage")),
            minimum_details=minimum,
            recommended_details=recommended,
            source="Steam",
            minimum_cpu_score=classify_cpu(minimum.get("processor")),
            recommended_cpu_score=classify_cpu(recommended.get("processor")),
        )
