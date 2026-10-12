# E6 — Degradación de una fuente bajo carga

**Estado: medido el <<COMPLETAR fecha>>.** Seis corridas de k6 ejecutadas con el simulador de upstream (3 antes, 3 después).

## Escenario e hipótesis

Ver [Escenario 6](../escenarios.md#escenario-6) y [ADR-0008](../adr/0008-persistencia-ejecucion-y-degradacion-de-fuentes.md).

- **Hipótesis.** Si el lock solo protege la caché y no la llamada HTTP, la fuente secundaria tiene un plazo de 3 s y la que no responde se lista en `unavailable_sources`, entonces con 50 usuarios y CheapShark lenta en el 35 % de las consultas: p95 ≤ 5 s, solicitudes fallidas < 1 % y 0 respuestas degradadas sin aviso.
- **Se refuta si** cualquier indicador queda fuera de umbral en alguna de las 3 corridas «después».
- **Si el «antes» ya cumple,** la hipótesis queda refutada: el problema no se reproduce con estos parámetros.

## Versiones comparadas

| Versión | Commit | Contenido |
|---|---|---|
| Antes | `02895ab` | Solo URLs configurables por variable de entorno, simulador y script k6 (sin cambio de comportamiento). |
| Después | `00798a1` | Lock fuera del I/O, plazo por fuente y aviso en `unavailable_sources`. |

`git diff --stat 02895ab 00798a1` muestra los archivos de código tocados.

## Montaje reproducible

Desde la raíz del repositorio, en tres terminales. Para cada versión: `git checkout <commit>`.

```bash
# 1. Upstream simulado (300 ms por llamada; CheapShark tarda 6 s en ~35 % de las consultas)
python scripts/stub_upstream.py 9000

# 2. Backend, 1 worker (reiniciarlo entre corridas)
cd backend
DRIFT_STEAM_BASE_URL=http://127.0.0.1:9000 \
DRIFT_CHEAPSHARK_BASE_URL=http://127.0.0.1:9000/cheapshark \
DRIFT_EXCHANGE_URL=http://127.0.0.1:9000/v6/latest/USD \
DRIFT_PLAYSTATION_BASE_URL=http://127.0.0.1:9000 \
python -m uvicorn app.main:app --port 8000 --workers 1

# 3. Carga (50 usuarios, 60 s, consulta única por iteración)
k6 run -e BASE_URL=http://127.0.0.1:8000 -e LABEL=antes-1 scripts/k6_e6_degradacion.js
```

Etiquetas: `antes-1..3` y `despues-1..3`. Cada corrida escribe `docs/evidencias/e6-resultados/<etiqueta>.json`.

Definiciones: **degradada** = respuesta sin tiendas de CheapShark (sin «GOG»); **sin aviso** = degradada y sin «CheapShark» en `unavailable_sources`; **fallida** = HTTP distinto de 200.

## Resultados (completar con los JSON)

| Versión | Corrida | p95 (ms) | Fallos (%) | Degradadas | Sin aviso | ¿Cumple? |
|---|---|---:|---:|---:|---:|---|
| Antes | 1 | <<p95>> | <<fallos %>> | <<degradadas>> | <<sin aviso>> | <<Sí/No>> |
| Antes | 2 | <<p95>> | <<fallos %>> | <<degradadas>> | <<sin aviso>> | <<Sí/No>> |
| Antes | 3 | <<p95>> | <<fallos %>> | <<degradadas>> | <<sin aviso>> | <<Sí/No>> |
| Después | 1 | <<p95>> | <<fallos %>> | <<degradadas>> | <<sin aviso>> | <<Sí/No>> |
| Después | 2 | <<p95>> | <<fallos %>> | <<degradadas>> | <<sin aviso>> | <<Sí/No>> |
| Después | 3 | <<p95>> | <<fallos %>> | <<degradadas>> | <<sin aviso>> | <<Sí/No>> |

Máquina y versiones (k6, Python): <<COMPLETAR: máquina, SO, versión de k6 y de Python>>.

## No regresión

- Pruebas nuevas (`backend/tests/test_source_degradation.py`): <<COMPLETAR resultado de pytest>>. Cubren plazo vencido, error de fuente, fuente sana, no filtrado del aviso al catálogo, lock fuera del I/O y una sola llamada en vuelo por clave.
- Suite completa (`python -m pytest tests -q`, incluidas las 18 previas): <<COMPLETAR N passed / fallos>>.
- Se ajustó `test_search_uses_fallback_when_steam_is_unavailable`: de igualdad con `["Steam"]` a inclusión de «Steam», porque su parche global de `httpx.get` también hace fallar a CheapShark y a PlayStation, que ahora se avisan.
- Contrato schemathesis y Quality Gate: <<COMPLETAR enlace al run de CI y estado del Quality Gate>>.

## Límites

Upstream simulado, no Steam real; el 35 % es un supuesto (4 de 11 búsquedas, no reproducidas); generador de carga y servidor en la misma máquina; ejecución local, no el laboratorio (0,5 CPU, 192 MB). Steam, la tasa de cambio y PlayStation nunca son lentos en el simulador. Con 0 juegos encontrados no hay dónde llevar el aviso (arc42 §11.7).

## Conclusión

<<COMPLETAR: conclusión redactada solo con los datos medidos; indicar si la hipótesis se sostiene o se refuta y qué factores de confusión quedan>>
