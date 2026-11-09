"""Corridas de la medición S14 del escenario E1 contra el despliegue.

Intercala los dos modos de scripts/k6_s14_e1_busqueda.js y espera entre corridas
para que venzan la caché de búsqueda (60 s) y la ventana del límite de tasa
(60 s), y para no acumular llamadas a Steam. Se detiene si la mitad de una
corrida falla: seguir solo aumentaría la carga sobre un servicio con problemas.

    python scripts/s14_e1_corridas.py
"""

import json
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "scripts" / "k6_s14_e1_busqueda.js"
RESULTADOS = RAIZ / "docs" / "evidencias" / "s14-resultados"

REPETICIONES = 3
MODOS = ("distintas", "misma")
ESPERA_SEGUNDOS = 300
USUARIOS = 50


def correr(modo: str, repeticion: int) -> dict:
    salida = RESULTADOS / f"{modo}-{repeticion}.json"
    # k6 termina con código 99 si no se cumple el umbral: es un resultado, no un fallo.
    subprocess.run(
        ["k6", "run", "--quiet", "-e", f"MODO={modo}", "-e", f"SALIDA={salida}", str(SCRIPT)],
        check=False,
    )
    return json.loads(salida.read_text(encoding="utf-8"))


def main() -> int:
    RESULTADOS.mkdir(parents=True, exist_ok=True)
    corridas = [(modo, rep) for rep in range(1, REPETICIONES + 1) for modo in MODOS]

    for indice, (modo, repeticion) in enumerate(corridas):
        if indice:
            time.sleep(ESPERA_SEGUNDOS)

        resultado = correr(modo, repeticion)

        if resultado["estado_200"] < USUARIOS / 2:
            print(f"Detenido: {modo}-{repeticion} tuvo {resultado['estado_200']} respuestas 200.")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
