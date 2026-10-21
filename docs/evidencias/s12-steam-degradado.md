# Evidencia S12 — p95 y plazo total con Steam degradado

> **Naturaleza de la medición.** Todas las respuestas HTTP son simuladas. Lo que se mide es el comportamiento del código de DRIFT (timeouts, reintentos, backoff, plazo total y concurrencia) frente a un upstream de laboratorio. **No son mediciones de producción** y no dicen nada sobre la latencia real de Steam.
>
> **Estado de la ejecución.** La corrida de este documento la hizo el asistente de IA en un sandbox sin red y sin el paquete `httpx`: se usó un reemplazo mínimo de la biblioteca estándar (ver «Limitaciones»). El equipo debe repetirla con las dependencias del proyecto antes de dar estas cifras por oficiales.

## 1. Pregunta y criterio de aceptación

**Pregunta.** Con Steam lento, intermitente o caído, ¿cumple la búsqueda el plazo total, o los timeouts y reintentos de cada fase pueden acumularse hasta excederlo?

**Criterio fijado antes de ejecutar** (también está en la cabecera de `scripts/s12_latencia_steam.py`). No hay un SLO acordado, así que el objetivo es una **hipótesis de laboratorio** heredada del umbral de E6 ([E6](e6-degradacion-bajo-carga.md)):

| Código | Criterio |
|---|---|
| Plazo | 5,0 s de latencia total de una búsqueda |
| C1 | p95 de la latencia total ≤ 5,0 s en cada escenario |
| C2 | Cumplimiento del plazo (búsquedas ≤ 5,0 s) ≥ 99 % |
| C3 | Ninguna búsqueda termina en excepción: la degradación se resuelve con el respaldo y `unavailable_sources` |
| C4 | En el escenario «normal» no hay búsquedas degradadas |

Los percentiles usan el método del rango más cercano. El p95 se informa con al menos 20 muestras y el p99 con al menos 100.

## 2. Método

- **Qué se ejecuta:** `SearchGames` sobre la misma composición de `main.py` (Steam con respaldo en memoria, CheapShark y PlayStation como fuentes secundarias). CheapShark y PlayStation responden en ~20 ms para que el total refleje a Steam.
- **Escenarios de Steam** (por llamada): *normal* 0,10–0,25 s; *lento* 2,0–3,6 s; *intermitente* 30 % sin respuesta, 10 % HTTP 503 y el resto normal; *no disponible (timeout)* nunca responde; *no disponible (503)* responde 503 de inmediato.
- **Configuraciones comparadas** (mismo código): `s11` = `RetryPolicy()` sin plazo total (comportamiento de S11); `s12` = `RetryPolicy(total_deadline_seconds=4.0)` (valor por defecto de S12).
- **Muestras:** 100 búsquedas por escenario y configuración, con 20 en paralelo, cada una con repositorios nuevos (sin caché: es el camino frío, el peor caso). Semilla 12; reproducible en distribución, no bit a bit (los hilos cambian el orden de los sorteos).
- **Qué se mide por separado:** latencia de cada llamada a Steam (vista desde el adaptador, incluida la espera de un timeout); latencia total de `SearchGames.execute`; solicitudes a Steam; resultados (ok, timeout, 503); reintentos y fallos finales (eventos `external_retry` y `external_request_failed`); búsquedas degradadas y con error; cumplimiento del plazo.
- **Alcance de «total»:** desde `SearchGames.execute` hasta que vuelve la lista; no incluye el servidor HTTP ni el frontend.

Comando (desde la raíz del repositorio, con las dependencias de `backend/requirements.txt`):

```bash
python scripts/s12_latencia_steam.py --samples 100 --concurrency 20 --seed 12
```

Escribe `docs/evidencias/s12-resultados/steam-degradado.json`. Las pruebas deterministas de la regla (reloj virtual, sin dormir) están en `backend/tests/test_s12_plazo_total.py`.

## 3. Resultados (corrida del sandbox, 20 de octubre de 2026)

Datos completos: [`s12-resultados/steam-degradado-sandbox-shim.json`](s12-resultados/steam-degradado-sandbox-shim.json). Tiempos en segundos; n = 100 búsquedas por fila.

| Escenario | Config. | Total p50 | Total p95 | Total p99 | Total máx. | Llamada Steam p50 / p95 | Solic. Steam | Reintentos | Plazo cumplido | Degradadas | Errores | Veredicto |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| normal | s11 | 0,35 | 0,46 | 0,47 | 0,48 | 0,17 / 0,24 | 200 | 0 | 100 % | 0 | 0 | Cumple |
| normal | s12 | 0,35 | 0,46 | 0,47 | 0,48 | 0,17 / 0,24 | 200 | 0 | 100 % | 0 | 0 | Cumple |
| lento | s11 | 6,06 | **10,82** | 11,58 | 11,70 | 2,76 / 3,00 | 247 | 64 | **20 %** | 24 | 0 | **No cumple** |
| lento | s12 | 4,00 | 4,01 | 4,01 | 4,01 | 1,99 / 3,00 | 200 | 38 | 100 % | **100** | 0 | Cumple C1–C3 |
| intermitente | s11 | 3,22 | **6,47** | 6,68 | 6,81 | 0,19 / 3,00 | 264 | 81 | **80 %** | 30 | 0 | **No cumple** |
| intermitente | s12 | 3,17 | 4,00 | 4,02 | 4,03 | 0,19 / 3,00 | 260 | 77 | 100 % | 33 | 0 | Cumple |
| no disponible (timeout) | s11 | 6,13 | **6,24** | 6,25 | 6,25 | 3,00 / 3,00 | 200 | 100 | **0 %** | 100 | 0 | **No cumple** |
| no disponible (timeout) | s12 | 4,00 | 4,01 | 4,01 | 4,01 | 1,00 / 3,00 | 200 | 100 | 100 % | 100 | 0 | Cumple |
| no disponible (503) | s11 | 0,17 | 0,27 | 0,28 | 0,29 | 0,02 / 0,02 | 200 | 100 | 100 % | 100 | 0 | Cumple |
| no disponible (503) | s12 | 0,18 | 0,27 | 0,29 | 0,29 | 0,02 / 0,02 | 200 | 100 | 100 % | 100 | 0 | Cumple |

Con n = 100 el p99 es la muestra número 99 y el máximo es la 100: son una indicación, no una estimación estable de la cola.

Resultados por escenario de Steam, por resultado de cada llamada (s11 / s12): lento, 159 ok y 88 timeouts / 62 ok y 138 timeouts; intermitente, 153 ok, 75 timeouts y 36 con 503 / 150 ok, 74 timeouts y 36 con 503; no disponible (timeout), 200 timeouts en ambas.

## 4. Lectura de los resultados

1. **La acumulación existe y es medible.** Con Steam sin responder, S11 tarda 6,24 s en el p95 (dos timeouts de 3 s más el backoff) y **ninguna** búsqueda cumple 5 s. Cada llamada respeta su timeout; lo que falla es la suma. Un timeout configurado no demuestra por sí mismo que la operación cumpla el plazo.
2. **El plazo total lo corrige.** Con el presupuesto compartido de 4 s, el máximo observado en todos los escenarios es 4,03 s y el cumplimiento sube al 100 %, sin ninguna excepción (C3).
3. **El plazo total tiene un costo, que la medición muestra y que no se debe ocultar.** En el escenario *lento* (cada llamada de 2,0 a 3,6 s, y la búsqueda necesita dos llamadas en secuencia), S11 entregaba datos reales de Steam en el 76 % de las búsquedas, aunque con un p95 de 10,8 s. Con 4 s, **el 100 % de las búsquedas se degrada**: el respaldo responde a tiempo, pero ninguna usa los datos de Steam. Ningún plazo ≤ 5 s puede servir a Steam si cada llamada tarda más de 2,5 s. Es una disyuntiva entre latencia y disponibilidad de la fuente principal, no un error.
4. **El valor de 4 s es una hipótesis, no una conclusión.** Se eligió para dejar margen bajo 5 s cuando además se espera a las fuentes secundarias. Si el producto prefiere datos de Steam más completos a una respuesta rápida, el plazo se sube con `DRIFT_STEAM_TOTAL_DEADLINE_SECONDS` (o se desactiva con `off`), aceptando que el p95 supere 5 s con Steam lento. La decisión corresponde al equipo y al profesor; la evidencia solo muestra su costo.
5. **Reintentos.** Con 503 inmediato, el reintento no cuesta tiempo (p95 0,27 s) y el respaldo responde en ambas configuraciones. Con timeouts, el presupuesto recorta el segundo intento (1,0 s de mediana por llamada con Steam caído) en lugar de agotarlo.
6. **Una limitación que sigue sin resolverse:** cuando el respaldo en memoria no contiene el juego, la respuesta degradada sale vacía y **sin aviso** (arc42 §11.8). Esta medición usa «Minecraft», que sí está en el respaldo, para poder contar las búsquedas degradadas.

## 5. Limitaciones

- **Reemplazo de `httpx`.** Esta corrida usó un reemplazo mínimo de la biblioteca estándar para las excepciones y los objetos de respuesta (`environment.httpx = desconocida` en el JSON). El código de DRIFT es el del repositorio, pero no se ejecutó contra `httpx 0.28.1`. Hay que repetirla en un entorno con las dependencias reales.
- **Upstream simulado.** Las latencias y las proporciones de fallo son supuestos de laboratorio (arriba); no se midió Steam.
- **Timeout por operación de red.** `httpx` aplica su timeout a cada operación (conexión, lectura…), no a la llamada completa; el presupuesto acota el timeout nominal de cada intento, pero no puede cortar una respuesta que llega gota a gota. Este caso no está medido.
- **Camino frío.** Sin caché; con caché caliente la latencia sería menor, pero una caché no protege la primera consulta tras vencer el TTL.
- **Sin servidor HTTP.** «Total» no incluye FastAPI, el proxy ni el frontend.
- **Muestras.** n = 100 por celda: el p99 es indicativo.
- **Reproducibilidad.** En distribución, no bit a bit.

## 6. Relación con las condiciones de revisión de ADR-0009

ADR-0009 pide revisar la decisión si «la latencia del reintento incumple el p95 del escenario con fuentes degradadas». En el laboratorio, esa condición **se cumple** para la configuración de S11 (p95 de 6,24 s con Steam sin responder frente al umbral de 5 s). La respuesta fue la medida más pequeña, un plazo total compartido en el adaptador, que lleva el p95 a 4,01 s. No se evaluó ni se implementó un circuit breaker ni la extracción del servicio: con el plazo, el costo observado es acotado (dos solicitudes por búsqueda hacia una fuente caída, 200 en total para 100 búsquedas) y ADR-0009 no se modifica. Queda a criterio del equipo si este dato basta para reabrir esa decisión.

## 7. Pendiente

- Repetir la corrida con las dependencias del proyecto y reemplazar el JSON del sandbox por el oficial (`steam-degradado.json`).
- Decidir con el equipo el plazo total y si la disyuntiva del escenario *lento* es aceptable.
