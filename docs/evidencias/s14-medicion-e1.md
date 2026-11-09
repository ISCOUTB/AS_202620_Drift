# Evidencia S14 — Medición local de E1 con fuentes simuladas

> **Esta medición complementa a la [medición en el despliegue](s14-e1-medicion.md), que es la evidencia vigente de E1.** Aquí se mide el costo propio de la búsqueda, no el sistema desplegado. Las cifras y el procedimiento no cambiaron; se corrigió lo que decía sobre el despliegue, el límite de tasa y la línea base.

**Fecha de la medición:** 2026-11-09 (UTC), 8 de noviembre de 2026 en hora de Colombia
**Commit medido:** `be72a2f` (punta de `master` al empezar S14; los scripts de esta medición no cambian el código del backend)
**Herramienta:** k6 v1.3.0, Python 3.13, `httpx` 0.28.1, un worker de `uvicorn`
**Endpoint evaluado:** `GET /games/search?q=<consulta distinta por solicitud>`

## 1. Escenario medido y umbral

Se mide **E1 (rendimiento de la búsqueda)** tal como está declarado en [arc42 §10.2](../arc42/arc42_10_Requisitos_Calidad.md) y en [`escenarios.md`](../escenarios.md#escenario-1):

| Elemento | Valor declarado en §10 |
|---|---|
| Fuente | Jugador |
| Estímulo | Realiza una búsqueda de un videojuego |
| Artefacto | Servicio de Búsqueda y Comparación |
| Entorno | Hasta 50 usuarios concurrentes, operación normal |
| Medida | **≤ 3 s en el percentil 95** |

El umbral **no cambió** desde que se declaró E1. Se usa el mismo valor y se fija en el script (`thresholds` de `scripts/k6_s14_e1.js`) antes de ejecutar. Como criterio complementario se toma el que ya usaba la línea base de E1: menos del 1 % de solicitudes fallidas.

**Por qué E1 y no otro escenario.** La única medición previa de E1 ([línea base](e1-linea-base.md), septiembre) fue una corrida única, sin entorno declarado y con una sola consulta repetida (`Minecraft`), que la caché de 60 s favorece. Desde entonces la búsqueda cambió (degradación controlada en E6, cliente resiliente en S11–S12, limitador y autenticación en S13), así que había que volver a medirla.

## 2. Procedimiento

| Elemento | Valor |
|---|---|
| Carga | 50 usuarios virtuales concurrentes (executor `per-vu-iterations`), 4 búsquedas cada uno: **200 solicitudes por corrida** |
| Consultas | Todas distintas (`s14 juego VVII`: usuario `VV`, iteración `II`), así que ninguna aprovecha la caché de otra |
| Caché | Fría: cada corrida arranca procesos nuevos de backend y upstream |
| Repeticiones | **5 corridas** seguidas, con las mismas condiciones |
| Fuentes externas | Simuladas por `scripts/stub_upstream.py` con `STUB_SIN_DEGRADACION=1` (operación normal, ninguna fuente lenta): Steam 0,15 s por llamada, CheapShark 0,25 s, PlayStation 0,25 s, tasa de cambio 0,10 s |
| Backend | `backend/` del commit medido, 1 worker de `uvicorn` en `127.0.0.1:8200`, lanzado por `scripts/e6_backend.py` |
| Límite de tasa | Desactivado (`DRIFT_RATE_LIMIT_PER_MINUTE=0`): los 50 usuarios salen de una sola IP y con el límite se mediría el 429 de ADR-0012, no la búsqueda |
| Validación de cada respuesta | HTTP 200 y lista no vacía de juegos (checks de k6) |
| Variables medidas | p50, p90, p95 y máximo de `http_req_duration`; solicitudes fallidas |

Antes de las corridas se comprobó a mano que la respuesta trae precios de las cuatro fuentes (`Steam`, `GOG`, `Epic Games Store`, `PlayStation`) y `unavailable_sources` vacío. Es decir, se mide la ruta normal y no el respaldo.

### Cómo reproducirla

Desde la raíz del repositorio, con k6 instalado y las dependencias de `backend/requirements.txt`:

```bash
for i in 1 2 3 4 5; do python scripts/s14_corrida.py corrida-$i; done
```

`scripts/s14_corrida.py` levanta el upstream simulado sin degradación y el backend, espera a que respondan, lanza `scripts/k6_s14_e1.js` y los detiene. Cada corrida deja dos archivos en [`s14-resultados/`](s14-resultados/): el resumen de k6 (`corrida-N.json`) y el entorno (`corrida-N-entorno.json`, con commit, CPU, versiones y configuración).

Este script no sirve para medir el despliegue con sus valores por defecto: sus 200 búsquedas superan el límite de 60 por minuto y se mediría el 429. El despliegue se midió con [`scripts/s14_e1_corridas.py`](../../scripts/s14_e1_corridas.py), como explica [su evidencia](s14-e1-medicion.md).

## 3. Entorno de la medición

**La medición es local, no del sistema desplegado.** El backend y las fuentes simuladas corrieron en la misma máquina (Linux x86_64, 2 CPU) y se comunicaron por `127.0.0.1`. La máquina donde corrió no tenía acceso de red a los despliegues ni a las APIs reales. Esa limitación era solo de esa máquina: el despliegue se [midió desde otro equipo](s14-e1-medicion.md).

Qué cambia eso en el significado del número:

- **Mide el costo propio de DRIFT** (FastAPI, caso de uso, combinación de fuentes, conversión de moneda, hilos por fuente) **con latencias externas fijas y conocidas**. No mide la latencia real de Steam, CheapShark ni PlayStation, ni su variabilidad.
- **No incluye la red entre el usuario y el servidor** ni el proxy del despliegue (Traefik, Azure App Service o el arranque en frío de Vercel).
- **No incluye el costo TLS por cliente.** `scripts/e6_backend.py` reemplaza `httpx.get` por una conexión HTTP simple para que el experimento no toque servicios reales. Así queda fuera la deuda abierta de §11.7: cada llamada `httpx.get` crea un cliente y su contexto TLS.
- **No incluye los límites de recursos del despliegue.** Aquí hubo 2 CPU compartidas con k6. En el laboratorio, cada contenedor tiene 0,5 CPU y 192 MB ([`deploy/compose.lab.yaml`](../../deploy/compose.lab.yaml)).
- **Sin el límite de tasa.** En producción, los usuarios detrás de una misma IP reciben 429 si entre todos superan 60 búsquedas por minuto, como pasaría con las 200 de esta carga. Esa es una decisión de ADR-0012, no una falla de rendimiento.

Por eso el resultado responde a «¿la arquitectura de la búsqueda introduce demoras propias que rompan E1 con 50 usuarios?», y no a «¿el sistema desplegado cumple E1 hoy?».

## 4. Resultados

Archivos originales de k6 en [`s14-resultados/`](s14-resultados/). Tiempos en milisegundos.

| Corrida | Solicitudes | Fallidas | p50 | p90 | p95 | Máximo | Cumple p95 ≤ 3000 ms |
|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 200 | 0 | 399 | 556 | 624 | 797 | Sí |
| 2 | 200 | 0 | 402 | 587 | 632 | 797 | Sí |
| 3 | 200 | 0 | 416 | 607 | 628 | 786 | Sí |
| 4 | 200 | 0 | 399 | 586 | 639 | 809 | Sí |
| 5 | 200 | 0 | 413 | 594 | 682 | 799 | Sí |
| **Mediana de 5** | **1000 en total** | **0 (0 %)** | **402** | **587** | **632** | **797** | |

La dispersión del p95 entre corridas es baja: de 624 a 682 ms.

## 5. Contraste con el umbral y conclusión

| Medida | Umbral (§10) | Obtenido (mediana de 5) | Resultado |
|---|---|---|---|
| p95 de la búsqueda | ≤ 3000 ms | 632 ms | Cumple, con 2,4 s de margen |
| Solicitudes fallidas | < 1 % | 0 % (0 de 1000) | Cumple |

**Conclusión de esta medición: cumple solo bajo estas condiciones locales.** En las 5 corridas, con 50 usuarios concurrentes, caché fría y fuentes que responden en 0,10–0,25 s por llamada, el p95 queda en 0,62–0,68 s. Así que la arquitectura de la búsqueda no consume el presupuesto de 3 s.

**Condiciones de validez.** El resultado vale para un worker, en local, con fuentes simuladas a latencia fija y sin el costo TLS por cliente. **No demuestra** que el sistema desplegado cumpla E1, y de hecho no lo cumple: [en el despliegue](s14-e1-medicion.md), con búsquedas distintas, el p95 fue de 9,05 s. Este margen no se traslada al sistema desplegado, y todavía no se ha medido cuánto pesa cada diferencia entre los dos entornos. Con fuentes lentas, el comportamiento lo cubren E6 (p95 de 3,61 s) y S12 (plazo total de 4 s), que también quedan por encima de 3 s.

**Comparación con la línea base.** En septiembre se midió p95 = 1,24 s con una consulta repetida. Su documento no declara el entorno; su script ([`k6_baseline.js`](../../scripts/k6_baseline.js)) apunta al backend de Vercel. Esa cifra y la de S14 no son comparables, porque cambian entorno, fuentes y consultas. Las dos quedan por debajo del umbral.

## 6. Lo que queda pendiente

| Pendiente | Por qué importa | Estado |
|---|---|---|
| Medir el entorno desplegado con el límite de tasa activo y menos de 60 solicitudes por minuto por IP | Es lo único que responde si el sistema desplegado cumple E1 | Hecho: [medición en el despliegue](s14-e1-medicion.md), con otro script |
| Medir con el cliente `httpx` real, sin reemplazar el transporte | El costo TLS por cliente (§11.7) se excluyó | Hecho en parte: la medición en el despliegue lo usa, pero no aísla su costo. Ligado a la deuda del cliente HTTP compartido |
