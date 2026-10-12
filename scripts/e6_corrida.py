"""Ejecuta una corrida completa del experimento E6 con caché fría.

Levanta el upstream simulado y el backend indicado (un worker), espera a que
respondan, lanza k6 y los detiene. Cada corrida arranca procesos nuevos, así
que ninguna aprovecha la caché de la anterior.

Uso (desde la raíz del repositorio):
    python scripts/e6_corrida.py <carpeta backend> <nombre>

Ejemplos:
    python scripts/e6_corrida.py ../drift-antes/backend antes-1
    python scripts/e6_corrida.py backend despues-1

El resumen queda en docs/evidencias/e6-resultados/<nombre>.json.
"""

import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "docs" / "evidencias" / "e6-resultados"

STUB_PORT = 9100
BACKEND_PORT = 8100


def wait_until_up(url, seconds=30):
    deadline = time.monotonic() + seconds

    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(url, timeout=2)
            return
        except OSError:
            time.sleep(0.3)

    raise SystemExit(f"No respondió a tiempo: {url}")


def find_k6():
    return (
        shutil.which("k6")
        or shutil.which("k6.exe")
        or r"C:\Program Files\k6\k6.exe"
    )


def main():
    backend_dir = Path(sys.argv[1]).resolve()
    name = sys.argv[2]

    RESULTS.mkdir(parents=True, exist_ok=True)

    environment = dict(os.environ, E6_STUB_URL=f"http://127.0.0.1:{STUB_PORT}")

    stub = subprocess.Popen(
        [sys.executable, str(ROOT / "scripts" / "stub_upstream.py")],
        env=dict(environment, E6_STUB_PORT=str(STUB_PORT)),
    )

    backend = subprocess.Popen(
        [
            sys.executable,
            str(ROOT / "scripts" / "e6_backend.py"),
            str(backend_dir),
            str(BACKEND_PORT),
        ],
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        wait_until_up(f"http://127.0.0.1:{STUB_PORT}/health")
        wait_until_up(f"http://127.0.0.1:{BACKEND_PORT}/health")

        output = RESULTS / f"{name}.json"

        completed = subprocess.run(
            [
                find_k6(),
                "run",
                "--quiet",
                "-e", f"BASE_URL=http://127.0.0.1:{BACKEND_PORT}",
                "-e", f"SALIDA={output.as_posix()}",
                str(ROOT / "scripts" / "k6_e6_degradacion.js"),
            ],
            cwd=ROOT,
        )

        # k6 devuelve 99 cuando no se cumple un umbral: es un resultado válido.
        print(f"{name}: k6 terminó con código {completed.returncode}")
    finally:
        for process in (backend, stub):
            process.terminate()

        for process in (backend, stub):
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()


if __name__ == "__main__":
    main()
