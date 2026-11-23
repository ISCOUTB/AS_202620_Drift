"""Dice qué commit de master está desplegado, comparando la huella del código.

    python scripts/verificar_despliegue.py
    python scripts/verificar_despliegue.py https://drift.iscoutb.dev/api/health
"""

import json
import subprocess
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "backend"))

from app.infrastructure.code_fingerprint import fingerprint_of  # noqa: E402

URL_POR_DEFECTO = "https://drift.iscoutb.dev/api/health"
COMMITS_A_REVISAR = 40
PREFIJO = "backend/app/"


def git(*argumentos: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(RAIZ), *argumentos],
        check=True,
        capture_output=True,
    ).stdout


def huella_del_commit(commit: str) -> str:
    rutas = git("ls-tree", "-r", "--name-only", "-z", commit, "--", PREFIJO)
    archivos = [
        (ruta[len(PREFIJO):], git("show", f"{commit}:{ruta}"))
        for ruta in rutas.decode("utf-8").split("\0")
        if ruta.endswith(".py")
    ]

    return fingerprint_of(archivos)


def main() -> int:
    url = sys.argv[1] if len(sys.argv) > 1 else URL_POR_DEFECTO

    with urllib.request.urlopen(url, timeout=30) as respuesta:
        desplegada = json.load(respuesta).get("code_fingerprint")

    if not desplegada:
        print("El despliegue todavía no publica la huella del código.")
        return 1

    commits = git(
        "log", "--first-parent", f"-{COMMITS_A_REVISAR}", "--format=%h", "origin/master"
    ).decode().split()

    for commit in commits:
        if huella_del_commit(commit) == desplegada:
            print(f"Desplegado: {commit} (huella {desplegada})")
            return 0

    print(f"La huella {desplegada} no coincide con los últimos {len(commits)} commits.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
