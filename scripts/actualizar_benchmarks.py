"""Actualiza las copias locales de puntajes de tarjetas gráficas y procesadores.

Lee UNA vez cada lista pública de UL Benchmarks («Best GPUs», 3DMark Steel
Nomad, y «Best CPUs», 3DMark CPU Profile) y guarda nombre y puntaje en
backend/app/infrastructure/persistence/data/.

DRIFT nunca consulta ese sitio al atender una búsqueda: usa las copias. Los
datos son de UL Solutions y se usan con fines académicos, no comerciales,
citando la fuente y la fecha de consulta.

Los archivos generados están en .gitignore: NO se suben al repositorio. En
local el backend los lee directamente. Para los despliegues, copia su
contenido a un lugar privado (por ejemplo un gist secreto) y pon sus
direcciones «raw» en las variables DRIFT_GPU_BENCHMARKS_URL y
DRIFT_CPU_BENCHMARKS_URL del servidor.

Uso (desde la raíz del repositorio):
    python scripts/actualizar_benchmarks.py
    python scripts/actualizar_benchmarks.py gpus-guardada.html cpus-guardada.html
"""

import html
import json
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path

DATA = (
    Path(__file__).resolve().parents[1]
    / "backend" / "app" / "infrastructure" / "persistence" / "data"
)

LISTS = (
    {
        "kind": "gpu",
        "url": "https://benchmarks.ul.com/compare/best-gpus",
        "benchmark": "3DMark Steel Nomad, puntaje gráfico (mediana de resultados de usuarios)",
        "output": DATA / "gpu_benchmarks.json",
    },
    {
        "kind": "cpu",
        "url": "https://benchmarks.ul.com/compare/best-cpus",
        "benchmark": "3DMark CPU Profile (mediana de resultados de usuarios)",
        "output": DATA / "cpu_benchmarks.json",
    },
)


def read_page(url, saved_page):
    if saved_page:
        return Path(saved_page).read_text(encoding="utf-8", errors="replace")

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "DRIFT/1.0 (proyecto academico AS_202620 UTB)"},
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def parse(page, kind):
    row_pattern = re.compile(
        r"/hardware/" + kind + r"/[^']*'>(?P<name>[^<]+)</a>"
        r".*?class='bar-score'>\s*(?P<score>\d+)\s*<",
        re.DOTALL,
    )

    items = {}

    # Cada fila de la tabla es un componente; los Mac usan otra ruta y se omiten.
    for row in page.split("<tr>")[1:]:
        match = row_pattern.search(row)

        if not match:
            continue

        name = " ".join(html.unescape(match.group("name")).split())
        score = int(match.group("score"))

        if score > 0:
            items[name] = {
                "name": name,
                "score": score,
                "laptop": "notebook" in name.casefold(),
            }

    return sorted(items.values(), key=lambda item: -item["score"])


def main():
    saved_pages = sys.argv[1:]

    for index, hardware_list in enumerate(LISTS):
        saved_page = saved_pages[index] if index < len(saved_pages) else None
        items = parse(read_page(hardware_list["url"], saved_page), hardware_list["kind"])

        if len(items) < 50:
            raise SystemExit(
                f"Solo se reconocieron {len(items)} filas en "
                f"{hardware_list['url']}: la página cambió de formato."
            )

        hardware_list["output"].parent.mkdir(parents=True, exist_ok=True)

        hardware_list["output"].write_text(
            json.dumps(
                {
                    "source": "UL Benchmarks (UL Solutions)",
                    "url": hardware_list["url"],
                    "benchmark": hardware_list["benchmark"],
                    "retrieved_at": date.today().isoformat(),
                    "license_note": (
                        "Datos de UL Solutions. Copia para uso académico y no "
                        "comercial del proyecto DRIFT."
                    ),
                    "items": items,
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        print(f"{len(items)} filas guardadas en {hardware_list['output']}")


if __name__ == "__main__":
    main()
