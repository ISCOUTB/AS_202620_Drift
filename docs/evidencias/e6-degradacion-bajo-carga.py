"""Lee docs/evidencias/e6-resultados/*.json e imprime las filas de la tabla de E6.
Uso (desde la raíz del repo):  python scripts/resumen_e6.py
Umbral (escenario E6): p95 <= 5000 ms, fallos < 1 %, degradadas sin aviso = 0."""

import json
from pathlib import Path
 
carpeta = Path("docs/evidencias/e6-resultados")
for version, prefijo in (("Antes", "antes"), ("Después", "despues")):
    for i in (1, 2, 3):
        ruta = carpeta / f"{prefijo}-{i}.json"
        if not ruta.exists():
            print(f"| {version} | {i} | FALTA {ruta.name} | | | | |")
            continue
        d = json.loads(ruta.read_text(encoding="utf-8"))
        pct = 100 * d["fallidas"] / d["solicitudes"] if d["solicitudes"] else 0
        cumple = d["p95_ms"] <= 5000 and pct < 1 and d["degradadas_sin_aviso"] == 0
        print(
            f"| {version} | {i} | {d['p95_ms']:.0f} | {pct:.2f} | "
            f"{d['degradadas']:.0f} | {d['degradadas_sin_aviso']:.0f} | {'Sí' if cumple else 'No'} |"
        )
 
