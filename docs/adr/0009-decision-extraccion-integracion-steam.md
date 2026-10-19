# ADR-0009: Decisión de extracción de la integración con Steam

- **Estado:** Aceptado
- **Fecha:** 2026-10-18
- **Decisores:** Equipo de desarrollo de DRIFT
- **Relacionado con:** [ADR-0002](0002-adoptar-nextjs-fastapi-arquitectura-hexagonal.md), [ADR-0003](0003-reajuste-contextos-dominio.md), [ADR-0006](0006-despliegue-serverless-api-busqueda.md) y [ADR-0008](0008-persistencia-ejecucion-y-degradacion-de-fuentes.md)
- **No sustituye a ningún ADR:** la decisión no contradice a los anteriores.

## Contexto

La búsqueda `GET /games/search` recorre `SearchGames` → `CombinedGameRepository` → `ResilientGameRepository` → `SteamGameRepository`. Steam es la fuente principal; CheapShark y PlayStation son secundarias. `InMemoryGameRepository` actúa como respaldo cuando Steam falla.

Hechos verificados en el repositorio (octubre de 2026):

- El backend es una aplicación FastAPI con capas `domain`, `application` e `infrastructure`. `test_architecture.py` comprueba que el dominio y la aplicación no importan `httpx`, `fastapi` ni infraestructura.
- La integración con Steam vive en `backend/app/infrastructure/external/steam/` y se consume mediante el puerto `GameRepository`. Hay un segundo consumidor de la API de Steam, `SteamGameRequirementsRepository`, para la estimación de compatibilidad.
- En el laboratorio el backend corre como un único contenedor `api` (192 MB, 0,5 CPU) sin base de datos ni volúmenes (arc42 §7, ADR-0008).
- Los escenarios exigen soportar 50 usuarios concurrentes con p95 ≤ 3 s (ADR-0006) y E6 usa un umbral de p95 ≤ 5 s con una fuente degradada.
- No hay métricas persistentes por fuente ni registros de incidentes reales de Steam. E6 se midió con fuentes simuladas.

Hexagonal describe la dirección de las dependencias entre dominio y adaptadores. Que el backend se despliegue como una sola unidad es un hecho distinto, y este ADR no lo clasifica como «monolito modular».

## Problema

Decidir si la integración con Steam debe extraerse a un servicio independiente para tolerar sus fallos parciales, o si debe permanecer en el backend con mitigaciones de resiliencia. Los modos de fallo analizados están en [arc42 §11.8](../arc42/arc42-11-riesgos-y-deuda-tecnica.md).

## Alternativas evaluadas

**Alternativa A: extraer la integración con Steam a un microservicio.**

- Aislamiento: un fallo o bloqueo de Steam no ocuparía hilos del backend principal.
- Escalado independiente: posible, pero no hay evidencia de que Steam requiera escalar distinto del resto.
- Despliegue: un artefacto y un pipeline más; en el laboratorio, otro contenedor dentro de un presupuesto de memoria ya ajustado.
- Complejidad de operación: nuevo servicio que monitorear, versionar y asegurar.
- Nueva comunicación de red: un salto HTTP adicional con sus propios timeouts y fallos, que sumaría latencia al p95 y crearía otro modo de fallo parcial.
- Disponibilidad: el microservicio sería otra dependencia que puede caer; el respaldo local seguiría siendo necesario.
- Mantenimiento: contrato entre servicios, caché compartida o duplicada, y decidir qué hacer con el segundo consumidor (requisitos de compatibilidad).

**Alternativa B: mantener la integración dentro del backend actual.**

- Arquitectura hexagonal: el puerto `GameRepository` ya aísla a Steam del dominio y de los casos de uso.
- Simplicidad operativa: un solo proceso, sin red adicional ni coordinación entre servicios.
- Manejo de fallos: timeout, reintentos acotados, validación y respaldo se resuelven dentro del adaptador y de `ResilientGameRepository`.
- Extracción posterior: es posible sin tocar el dominio, porque bastaría un adaptador que implemente `GameRepository` llamando al servicio nuevo.
- Riesgo: un Steam lento comparte hilos y memoria con el resto de la API.

## Criterios de decisión

| Criterio | A: extraer | B: mantener |
|---|---|---|
| Evidencia de un problema que el aislamiento resuelva | No existe: no hay métricas ni incidentes reales | No aplica |
| Costo de memoria y operación frente al presupuesto del laboratorio | Mayor | Menor |
| Latencia añadida a la búsqueda (p95 ≤ 3 s) | Un salto de red más | Ninguna |
| Nuevos modos de fallo | Sí (red entre servicios) | No |
| Reversibilidad | Costosa de deshacer | Extraer luego es posible por el puerto |
| Aislamiento de fallos | Mayor | Medio; mitigado con timeout y respaldo |

La valoración es cualitativa; no proviene de mediciones.

## Decisión

**Alternativa B: mantener la integración con Steam dentro del backend actual.** No se declara que la extracción sea innecesaria para siempre, solo que hoy no hay evidencia que la justifique.

Decisión complementaria sobre resiliencia, implementada en el adaptador y no en el dominio:

1. Timeout explícito de 3 s por defecto (`DRIFT_STEAM_TIMEOUT_SECONDS`). Es un valor inicial de laboratorio, no un umbral óptimo demostrado. `httpx` lo aplica por fase, no como plazo total.
2. Hasta 2 intentos totales (`DRIFT_STEAM_MAX_ATTEMPTS`), solo ante timeout, error de conexión, HTTP 429 y 5xx. No se reintenta ningún otro 4xx ni un cuerpo inválido. Backoff exponencial con jitter completo y `Retry-After` en segundos; si pide más de 2 s se falla rápido. El reintento vive solo en el adaptador, no en capas superiores.
3. Validación de la estructura de las respuestas y error controlado `ExternalSourceError`, que `ResilientGameRepository` convierte en respaldo con aviso en `unavailable_sources`.
4. **Circuit breaker: se pospone.** Con un único proceso, tráfico de laboratorio, un respaldo local y sin evidencia de caídas sostenidas, el costo de un estado compartido, umbrales y pruebas no se justifica. No se simula con una bandera. Se incorporaría si hay evidencia de lo descrito en «Condiciones para revisar».
5. **Saga y outbox: no aplican** porque no existe una operación de negocio con transacciones distribuidas ni publicación de eventos. El análisis de idempotencia está en [arc42 §8.12](../arc42/arc42_8_conceptos_transversales.md).

## Consecuencias

Positivas:

- Sin nuevo servicio, red ni pipeline; se conserva la compatibilidad del contrato `GET /games/search` y de las pruebas existentes.
- Una caída de Steam deja de convertirse en error 500 cuando la respuesta es inválida: se degrada con aviso.
- La salida a un servicio sigue abierta mediante el puerto.

Negativas:

- Steam y el resto de la API comparten recursos del mismo proceso.
- Cada búsqueda con Steam caído paga el intento y su reintento. En el peor caso, cada fase puede tardar cerca de 6,25 s con los valores por defecto, por encima del umbral de E6 (p95 ≤ 5 s). No está medido.
- Si Steam cae y el respaldo no contiene el juego, la respuesta es una lista vacía sin aviso (arc42 §11.8, S11-F13).

## Riesgos

- El jitter y los valores por defecto no se calibraron con tráfico real.
- El resto de adaptadores aún no usa el cliente resiliente (S11-F11).
- Sin circuit breaker, una caída sostenida repite el costo del reintento en cada búsqueda (S11-F09).

## Plan de validación

1. Ejecutar `python -m pytest tests -q` en `backend/` y `backend/tests/test_steam_resilience.py` con las dependencias de `requirements.txt`.
2. Repetir la corrida de E6 con `scripts/stub_upstream.py` configurado para que Steam falle o tarde, y medir el p95 frente al umbral.
3. Revisar los registros `external_retry` y `external_request_failed` en el despliegue para estimar la frecuencia real de fallos.
4. Comprobar que arc42 §11.8, este ADR y el código siguen coherentes.

Estado de la validación al aceptar este ADR:

- Paso 1, cumplido: con el commit `a7c0ea4` y la fila S11-F14 añadida después, la suite del backend pasa completa (152 pruebas, 41 de ellas en `test_steam_resilience.py`), y las 6 pruebas de contrato pasan contra la API levantada en local. El CI de `a7c0ea4` terminó en verde.
- Paso 2, pendiente: la latencia del reintento con Steam degradado no se ha medido (S11-F12).
- Paso 3, pendiente: no hay todavía registros del despliegue revisados.
- Paso 4, cumplido: arc42 §11.8, §8.12 y este ADR describen el mismo código.

## Condiciones para revisar la decisión

Revisar esta decisión, y evaluar tanto la extracción como un circuit breaker, si ocurre alguno de estos casos. Los umbrales concretos deben fijarse con el equipo tras medir:

- Los registros muestran fallos de Steam sostenidos que degradan una fracción relevante de las búsquedas.
- La latencia del reintento incumple el p95 del escenario con fuentes degradadas.
- Steam exige escalar o desplegarse con un ciclo distinto al del resto del backend.
- Aparece un segundo equipo o un requisito de aislamiento de seguridad o de cuotas de la API.
- DRIFT incorpora escrituras que necesiten persistencia (ver arc42 §8.12).

## Trazabilidad

| Eslabón | Dónde |
|---|---|
| Aspecto y requisito | E5, disponibilidad, en [docs/aspectos.md](../aspectos.md) |
| Modos de fallo | [arc42 §11.8](../arc42/arc42-11-riesgos-y-deuda-tecnica.md), filas S11-F01 a S11-F14 |
| Idempotencia, saga y outbox | [arc42 §8.12](../arc42/arc42_8_conceptos_transversales.md) |
| Elementos C4 | Contenedor API en [C4 nivel 2](../c4/contenedores.md); componentes `SteamGameRepository` y `ResilientGameRepository` en [C4 nivel 3](../c4/componentes.md) |
| Código | `backend/app/infrastructure/external/resilient_http.py`, `backend/app/infrastructure/external/steam/steam_game_repository.py` y `backend/app/infrastructure/persistence/resilient_game_repository.py` |
| Pruebas | `backend/tests/test_steam_resilience.py` y `backend/tests/test_search_games.py::test_search_uses_fallback_when_steam_is_unavailable` |
| Implementación | PR #28 (`feat/s11-resiliencia-extraccion`), commit `c9cd338`, fusionado en `a7c0ea4` |
