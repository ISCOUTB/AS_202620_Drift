"""Ejecuta una corrida de la medición S14 del escenario E1 con caché fría.

Levanta el upstream simulado sin degradación y el backend de DRIFT (un worker),
espera a que respondan, lanza k6 y los detiene. Cada corrida arranca procesos
nuevos, así que ninguna aprovecha la caché de la anterior.

Uso (desde la raíz del repositorio, con k6 y backend/requirements.txt):
    python scripts/s14_corrida.py <nombre>

Ejemplo (las cinco corridas de la evidencia):
    for i in 1 2 3 4 5; do python scripts/s14_corrida.py corrida-$i; done

El resumen queda en docs/evidencias/s14-resultados/<nombre>.json y los datos
del entorno en docs/evidencias/s14-resultados/<nombre>-entorno.json.
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "docs" / "evidencias" / "s14-resultados"

STUB_PORT = 9200
BACKEND_PORT = 8200


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


def command_output(command):
    try:
        return subprocess.run(
            command, capture_output=True, text=True, cwd=ROOT, check=False
        ).stdout.strip()
    except OSError:
        return "desconocido"


def environment_record(name):
    import httpx  # se registra la versión real usada por el backend

    return {
        "corrida": name,
        "fecha_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "entorno": "local: backend y upstream simulado en 127.0.0.1 (no desplegado)",
        # «-dirty»: se midió con cambios sin commit sobre ese commit.
        "commit": command_output(["git", "describe", "--always", "--dirty"]),
        "sistema": platform.platform(),
        "cpus": os.cpu_count(),
        "python": platform.python_version(),
        "httpx": httpx.__version__,
        "k6": command_output([find_k6(), "version"]).splitlines()[0:1],
        "uvicorn_workers": 1,
        "limite_de_tasa": "desactivado (DRIFT_RATE_LIMIT_PER_MINUTE=0)",
        "fuentes": "simuladas por scripts/stub_upstream.py con STUB_SIN_DEGRADACION=1",
    }


def main():
    name = sys.argv[1]
    iterations = os.getenv("ITERACIONES", "4")

    RESULTS.mkdir(parents=True, exist_ok=True)

    # Los 50 usuarios virtuales salen de una sola IP: el límite de tasa
    # (ADR-0012) se desactiva para medir la búsqueda y no respuestas 429.
    environment = dict(
        os.environ,
        E6_STUB_URL=f"http://127.0.0.1:{STUB_PORT}",
        DRIFT_RATE_LIMIT_PER_MINUTE="0",
        STUB_SIN_DEGRADACION="1",
    )

    stub = subprocess.Popen(
        [sys.executable, str(ROOT / "scripts" / "stub_upstream.py")],
        env=dict(environment, E6_STUB_PORT=str(STUB_PORT)),
    )

    backend = subprocess.Popen(
        [
            sys.executable,
            str(ROOT / "scripts" / "e6_backend.py"),
            str(ROOT / "backend"),
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
                "-e", f"ITERACIONES={iterations}",
                str(ROOT / "scripts" / "k6_s14_e1.js"),
            ],
            cwd=ROOT,
        )

        (RESULTS / f"{name}-entorno.json").write_text(
            json.dumps(environment_record(name), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
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
