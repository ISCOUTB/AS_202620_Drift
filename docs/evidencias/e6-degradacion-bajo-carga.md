# Evidencia E6 — Degradación de una fuente bajo carga

**Fecha:** 2026-10-11
**Herramienta:** k6 v2.2.0, Python 3.14, un worker de `uvicorn`
**Endpoint evaluado:** `GET /games/search?q=<consulta distinta por usuario>`
**Escenario:** [E6](../escenarios.md#escenario-6) · **Decisión:** [ADR-0008](../adr/0008-persistencia-ejecucion-y-degradacion-de-fuentes.md)

## Punto débil identificado

En el despliegue del laboratorio, 4 de 11 búsquedas de prueba tardaron 5,4 s y llegaron sin los precios de CheapShark, sin ningún aviso. Al revisar el código se confirmaron tres causas:

1. `CombinedGameRepository` esperaba a la fuente secundaria sin plazo propio y descartaba sus errores en silencio.
2. Los adaptadores de Steam y CheapShark mantenían un lock durante la llamada HTTP, así que las búsquedas con caché fría se atendían una por una.
3. Solo Steam figuraba en `unavailable_sources`.

## Hipótesis

Con 50 usuarios concurrentes haciendo búsquedas distintas, caché fría y CheapShark tardando más de 5 s en cerca del 35 % de las consultas, si la búsqueda (a) deja de retener el lock durante la E/S, (b) espera a cada fuente secundaria como máximo 3 s y (c) registra la fuente faltante en `unavailable_sources`, entonces:

- el p95 de la búsqueda será ≤ 5 s,
- las solicitudes fallidas serán < 1 %, y
- no habrá respuestas degradadas sin aviso.

## Montaje

| Elemento | Valor |
|---|---|
| Carga | 50 usuarios virtuales, 1 búsqueda cada uno, todas distintas (`e6 juego 01` … `e6 juego 50`) |
| Caché | Fría: cada corrida arranca procesos nuevos |
| Backend | 1 worker de `uvicorn`, en `127.0.0.1:8100` |
| Fuentes | Simuladas por `scripts/stub_upstream.py`: Steam 0,15 s por llamada, CheapShark 0,25 s, PlayStation 0,25 s, tasa de cambio 0,10 s |
| Degradación | CheapShark tarda 6 s en 18 de las 50 consultas (36 %). El conjunto lento depende solo del número de la consulta: es el mismo en todas las corridas |
| Versión "antes" | commit `ab591de` (punta de `master` antes del cambio) |
| Versión "después" | el cambio descrito en ADR-0008, decisión 2 |
| Variable independiente | Versión del backend |
| Variables dependientes | p95 de `http_req_duration`, solicitudes fallidas, respuestas degradadas y degradadas sin aviso |
| Umbral | p95 ≤ 5 s, fallidas < 1 %, degradadas sin aviso = 0 |

Una respuesta se cuenta como **degradada** si ningún juego trae el precio de GOG, que el upstream simulado siempre ofrece a través de CheapShark. Es **sin aviso** si además no todos los juegos listan `CheapShark` en `unavailable_sources`.

## Procedimiento

Desde la raíz del repositorio, con k6 instalado:

```bash
# Versión anterior al cambio, en una carpeta aparte
git worktree add ../drift-antes ab591de

python scripts/e6_corrida.py ../drift-antes/backend antes-1
python scripts/e6_corrida.py backend despues-1
# ... repetir hasta antes-3 y despues-3

python scripts/resumen_e6.py
```

`scripts/e6_corrida.py` levanta el upstream simulado y el backend indicado, espera a que respondan, lanza `scripts/k6_e6_degradacion.js` y los detiene. `scripts/e6_backend.py` redirige las llamadas `httpx.get` de los adaptadores hacia el upstream simulado sin modificar el código medido, por lo que la misma envoltura sirve para ambas versiones. Las corridas se intercalaron (antes, después, antes, …).

## Resultados medidos

Los archivos originales de k6 están en [`e6-resultados/`](e6-resultados/). Tiempos en segundos.

| Versión | Corrida | Solicitudes | Fallidas | p50 | p95 | Máximo | Degradadas | Sin aviso | Cumple umbral |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Antes | 1 | 50 | 0 % | 52,09 | 93,54 | 98,94 | 18 | 18 | No |
| Antes | 2 | 50 | 0 % | 59,28 | 98,34 | 99,00 | 18 | 18 | No |
| Antes | 3 | 50 | 0 % | 49,74 | 86,69 | 98,97 | 18 | 18 | No |
| Después | 1 | 50 | 0 % | 0,70 | 3,62 | 3,64 | 18 | 0 | Sí |
| Después | 2 | 50 | 0 % | 0,82 | 3,51 | 3,65 | 18 | 0 | Sí |
| Después | 3 | 50 | 0 % | 0,68 | 3,61 | 3,64 | 18 | 0 | Sí |

| Métrica (mediana de 3 corridas) | Antes | Después |
|---|---:|---:|
| p50 | 52,09 s | 0,70 s |
| p95 | 93,54 s | 3,61 s |
| Respuestas degradadas por corrida | 18 | 18 |
| Degradadas sin aviso por corrida | 18 | 0 |
| Solicitudes fallidas (total de las 3 corridas) | 0 | 0 |

## Contraste con el umbral

- **Antes:** no cumple el umbral. El p95 mediano fue de 93,54 s frente a un máximo de 5 s, y hubo 18 respuestas degradadas sin aviso por corrida.
- **Después:** cumple el umbral en las tres corridas. El p95 mediano fue de 3,61 s y no hubo respuestas degradadas sin aviso.

La hipótesis se sostiene para las condiciones medidas. El p95 posterior queda cerca de 3,6 s porque las búsquedas afectadas esperan el plazo completo de 3 s antes de responder; es el costo aceptado de darle a la fuente la oportunidad de contestar.

## Factores de confusión controlados

- **Variación de los servicios reales:** se eliminó con un upstream simulado de latencias fijas.
- **Qué consultas son lentas:** es determinista, igual en las seis corridas.
- **Caché caliente:** cada corrida arranca procesos nuevos y cada usuario hace una consulta distinta.
- **Orden de ejecución:** las corridas de ambas versiones se intercalaron.
- **Costo de crear un cliente HTTP por llamada:** en el equipo de medición `httpx.get` tarda cerca de 0,5 s de CPU por llamada al crear su contexto TLS. Ese costo taparía el efecto medido, así que la envoltura usa una conexión HTTP simple, igual para ambas versiones.

## Límites de validez

- Las fuentes son simuladas: las latencias fijas no reproducen la variabilidad real de Steam, CheapShark ni PlayStation.
- Se midió en un solo equipo local (Windows, Python 3.14), con k6, el backend y el upstream compitiendo por la misma CPU. No se midió en el servidor del laboratorio (0,5 CPU y 192 MB por contenedor).
- El 36 % de consultas lentas es un supuesto apoyado en 4 de 11 búsquedas observadas una sola vez en el despliegue; no se volvió a muestrear.
- El costo del cliente HTTP por llamada quedó fuera del experimento. En producción ese costo existe y puede elevar los tiempos; está registrado como deuda en arc42 §11.7.
- Son 50 solicitudes por corrida y 3 corridas por versión: el p95 de cada corrida descansa en pocas muestras.
- No se probó degradación sostenida (acumulación de hilos abandonados) ni la caída simultánea de varias fuentes bajo carga.

## Observabilidad del escenario

- **Métrica:** `GET /metrics` expone `source_degradation`, con `drift_source_unavailable_total`: búsquedas totales, búsquedas degradadas y conteo por fuente.
- **Logs estructurados (JSON):** evento `source_unavailable` con `source`, `reason` (`timeout` o `error`) y `waited_ms`; `search_completed` incluye `unavailable_sources`.
- **Pruebas:** `backend/tests/test_source_degradation.py` (7 pruebas).

## Estado del despliegue

`https://drift.iscoutb.dev` se comprobó el 2026-10-12T04:35Z: portada 200, `/api/health` 200, búsqueda de `portal 2` 200 en 0,89 s con 5 juegos y precios, y compatibilidad 200. En ese momento el despliegue ejecutaba la versión **anterior** al cambio (su `/api/metrics` no incluía `source_degradation`). El cambio se despliega al integrarlo en `master`.
