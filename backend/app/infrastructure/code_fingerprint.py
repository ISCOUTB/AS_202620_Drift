import hashlib
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Tuple

FINGERPRINT_LENGTH = 16


def fingerprint_of(files: Iterable[Tuple[str, bytes]]) -> str:
    """
    Huella del código a partir de `(ruta relativa a app/, contenido)`.

    Ignora los finales de línea para que el mismo commit dé la misma huella
    en Windows y en el contenedor Linux.
    """

    digest = hashlib.sha256()

    for path, content in sorted(files):
        digest.update(path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(content.replace(b"\r\n", b"\n"))
        digest.update(b"\0")

    return digest.hexdigest()[:FINGERPRINT_LENGTH]


@lru_cache(maxsize=1)
def code_fingerprint() -> str:
    """Huella de los archivos `.py` de la aplicación que está corriendo."""

    root = Path(__file__).resolve().parents[1]

    return fingerprint_of(
        (path.relative_to(root).as_posix(), path.read_bytes())
        for path in root.rglob("*.py")
    )
