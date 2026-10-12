import json
import os
import re
import time
import unicodedata
from pathlib import Path
from threading import Lock
from typing import Callable, List, Optional

import httpx

from app.domain.model.hardware_benchmark import HardwareBenchmark
from app.domain.ports.hardware_benchmark_repository import (
    HardwareBenchmarkRepository,
)

DATA_DIRECTORY = Path(__file__).resolve().parent / "data"

# Si la copia no se pudo cargar, se reintenta pasado este tiempo.
RETRY_SECONDS = 300

# Un requisito que habla de portátiles suele decirlo con estas palabras.
_LAPTOP_WORDS = re.compile(r"notebook|laptop|mobile|portatil|max q")

# Marcas y palabras que no distinguen un modelo de otro.
GPU_NOISE_WORDS = r"\b(nvidia|geforce|amd|ati|radeon|intel)\b"
CPU_NOISE_WORDS = r"\b(intel|amd|core|processor|procesador|cpu)\b"

# Tras el modelo de una gráfica, estas palabras indican otra variante.
GPU_VARIANT_WORDS = ("ti", "super", "xt", "xtx")


def load_benchmark_payload(path: Path, url_variable: str) -> dict:
    """
    Carga una copia de puntajes, que es opcional y no se versiona.

    Primero el archivo local (desarrollo, generado con
    `scripts/actualizar_benchmarks.py`); si no existe, la dirección privada
    indicada por la variable de entorno (despliegues). Sin ninguna de las
    dos devuelve un catálogo vacío y el componente se compara por niveles.
    """

    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass

    url = os.getenv(url_variable, "").strip()

    if not url:
        return {}

    try:
        response = httpx.get(url, timeout=5.0, follow_redirects=True)
        response.raise_for_status()

        payload = response.json()
    except (httpx.HTTPError, ValueError):
        return {}

    return payload if isinstance(payload, dict) else {}


class JsonHardwareBenchmarkRepository(HardwareBenchmarkRepository):
    """
    Catálogo de puntajes de un tipo de componente a partir de una copia JSON.

    La copia se carga en el primer uso. DRIFT nunca consulta la fuente
    original de los puntajes al atender una petición.
    """

    def __init__(
        self,
        loader: Optional[Callable[[], dict]] = None,
        payload: Optional[dict] = None,
        noise_words: str = GPU_NOISE_WORDS,
        variant_words: tuple = GPU_VARIANT_WORDS,
    ):
        self._loader = loader or dict
        self._noise_words = noise_words
        self._lock = Lock()
        self._next_attempt_at = 0.0
        self._loaded = False

        # Un modelo no coincide si va pegado a más letras o cifras, ni si le
        # sigue una palabra que lo convierte en otra variante.
        self._ahead = r"(?![a-z0-9])"

        if variant_words:
            self._ahead += (
                r"(?!\s*(?:" + "|".join(variant_words) + r")(?![a-z0-9]))"
            )

        self._source = {}
        self._items = []
        self._by_name = {}
        self._desktop = {}
        self._laptop = {}
        self._patterns = {}

        # `payload` permite usar un catálogo ya cargado, sin archivo ni red.
        if payload is not None:
            self._index(payload)
            self._loaded = True

    def _model_key(self, text: str) -> str:
        """Reduce un nombre a 'gtx 1060 3gb' o 'i5 12400f', sin marcas."""

        text = unicodedata.normalize("NFKD", text)

        text = "".join(
            character
            for character in text
            if not unicodedata.combining(character)
        ).casefold()

        text = re.sub(r"\([^)]*\)", " ", text)
        text = re.sub(r"[®™©]", " ", text)
        text = re.sub(self._noise_words, " ", text)
        text = re.sub(r"[^a-z0-9]+", " ", text)
        text = re.sub(r"(\d{1,4})\s{0,3}gb\b", r"\1gb", text)

        return " ".join(text.split())

    def _text_key(self, text: str) -> str:
        # En el texto libre los paréntesis traen datos útiles ("(6 GB)").
        return self._model_key(text.replace("(", " ").replace(")", " "))

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return

        with self._lock:
            if self._loaded or time.monotonic() < self._next_attempt_at:
                return

            payload = self._loader()

            if payload.get("items"):
                self._index(payload)
                self._loaded = True
            else:
                self._next_attempt_at = time.monotonic() + RETRY_SECONDS

    def _index(self, payload: dict) -> None:
        self._source = {
            "source": payload.get("source"),
            "benchmark": payload.get("benchmark"),
            "retrieved_at": payload.get("retrieved_at"),
        }

        self._items = [
            HardwareBenchmark(
                name=item["name"],
                score=int(item["score"]),
                laptop=bool(item.get("laptop")),
            )
            for item in payload.get("items", [])
        ]

        self._by_name = {item.name.casefold(): item for item in self._items}

        # Modelo -> variantes de escritorio y de portátil. Solo los nombres
        # con algún número identifican un modelo dentro de un texto libre.
        self._desktop = {}
        self._laptop = {}

        for item in self._items:
            key = self._model_key(item.name)

            if not any(character.isdigit() for character in key):
                continue

            target = self._laptop if item.laptop else self._desktop
            target.setdefault(key, item)

        self._patterns = {
            key: re.compile(
                r"(?<![a-z0-9])"
                + re.escape(key).replace(r"\ ", r"\s+")
                + self._ahead
            )
            for key in set(self._desktop) | set(self._laptop)
        }

    def list_all(self) -> List[HardwareBenchmark]:
        self._ensure_loaded()

        return list(self._items)

    def get_by_name(self, name: Optional[str]) -> Optional[HardwareBenchmark]:
        if not name:
            return None

        self._ensure_loaded()

        return self._by_name.get(name.strip().casefold())

    def find_in_text(self, text: Optional[str]) -> List[HardwareBenchmark]:
        if not text:
            return []

        self._ensure_loaded()

        normalized = self._text_key(text)
        prefers_laptop = bool(_LAPTOP_WORDS.search(normalized))

        spans = [
            (match.start(), match.end(), key)
            for key, pattern in self._patterns.items()
            for match in pattern.finditer(normalized)
        ]

        found = []

        for start, end, key in spans:
            # "gtx 1060" dentro de "gtx 1060 3gb": gana el nombre más específico.
            is_part_of_longer = any(
                other_start <= start
                and end <= other_end
                and (other_end - other_start) > (end - start)
                for other_start, other_end, _ in spans
            )

            if is_part_of_longer:
                continue

            first, second = (
                (self._laptop, self._desktop)
                if prefers_laptop
                else (self._desktop, self._laptop)
            )

            item = first.get(key) or second.get(key)

            if item and item not in found:
                found.append(item)

        return found

    def describe_source(self) -> dict:
        self._ensure_loaded()

        return dict(self._source)


def gpu_benchmark_repository() -> JsonHardwareBenchmarkRepository:
    """Catálogo de tarjetas gráficas. La dirección privada es un secreto."""

    return JsonHardwareBenchmarkRepository(
        loader=lambda: load_benchmark_payload(
            DATA_DIRECTORY / "gpu_benchmarks.json",
            "DRIFT_GPU_BENCHMARKS_URL",
        ),
        noise_words=GPU_NOISE_WORDS,
        variant_words=GPU_VARIANT_WORDS,
    )


def cpu_benchmark_repository() -> JsonHardwareBenchmarkRepository:
    """Catálogo de procesadores. La dirección privada es un secreto."""

    return JsonHardwareBenchmarkRepository(
        loader=lambda: load_benchmark_payload(
            DATA_DIRECTORY / "cpu_benchmarks.json",
            "DRIFT_CPU_BENCHMARKS_URL",
        ),
        noise_words=CPU_NOISE_WORDS,
        variant_words=(),
    )
