# 11. Riesgos y deuda técnica

## 11.1. Propósito

Esta sección identifica los principales riesgos técnicos y arquitectónicos de DRIFT, así como la deuda técnica que puede afectar su mantenibilidad, confiabilidad y evolución. Para cada riesgo se describe su posible impacto y las acciones necesarias para reducirlo.

Los riesgos descritos se deben revisar periódicamente y actualizar conforme evolucione la implementación del sistema.

## 11.2. Riesgos arquitectónicos y técnicos

| ID | Riesgo | Impacto | Estrategia de mitigación |
|---|---|---|---|
| R-01 | Indisponibilidad o cambios en las fuentes externas de videojuegos. | La búsqueda puede fallar o devolver información incompleta. | Encapsular las integraciones mediante puertos y adaptadores, validar las respuestas y manejar errores y tiempos de espera. |
| R-02 | Diferencias entre la arquitectura documentada y la implementación real. | Dificulta la comprensión, el mantenimiento y la evolución del sistema. | Mantener sincronizados los ADR, los diagramas C4, arc42 y el código fuente. Registrar formalmente los cambios arquitectónicos. |
| R-03 | Pérdida de información si el catálogo depende de almacenamiento en memoria. | Los datos pueden desaparecer al reiniciar el proceso y no compartirse entre instancias. | Verificar el mecanismo de persistencia actual y determinar si los requisitos requieren almacenamiento persistente. |
| R-04 | Cobertura insuficiente de pruebas del flujo principal de búsqueda. | Los errores funcionales pueden llegar a la rama principal sin detectarse. | Probar el endpoint de búsqueda, los casos de uso y la interacción con las fuentes externas mediante dependencias controladas. |
| R-05 | Falta de observabilidad del sistema desplegado. | Dificulta identificar errores y diagnosticar problemas en producción. | Incorporar logs útiles, comprobaciones de salud y métricas adecuadas al alcance del proyecto. |
| R-06 | Regresiones causadas por cambios en frontend, backend o infraestructura. | Puede afectar funcionalidades existentes y generar incompatibilidades. | Ejecutar pruebas automatizadas en CI y revisar los cambios antes de integrarlos. |
| R-07 | Configuración incorrecta o exposición de secretos. | Puede impedir el despliegue o comprometer las credenciales de servicios externos. | Gestionar la configuración mediante variables de entorno, proteger los secretos y evitar versionar credenciales. |

Los niveles de impacto anteriores son valoraciones cualitativas iniciales. Deben revisarse según la evidencia obtenida durante las pruebas y el despliegue.

## 11.3. Deuda técnica

La deuda técnica comprende decisiones o implementaciones que pueden facilitar el desarrollo inicial, pero que incrementan el costo de mantenimiento o limitan la evolución futura del sistema.

| ID | Elemento | Consecuencia potencial | Acción propuesta |
|---|---|---|---|
| DT-01 | Desactualización de los ADR y diagramas respecto al código. | La documentación puede describir decisiones o componentes que no corresponden con la implementación. | Revisar las decisiones arquitectónicas y actualizar la documentación o el código para mantener su coherencia. |
| DT-02 | Uso de almacenamiento en memoria, si continúa siendo el mecanismo principal. | Pérdida de datos entre reinicios y limitaciones para escalar la aplicación. | Definir los requisitos de persistencia y adoptar una solución persistente cuando el alcance lo requiera. |
| DT-03 | Manejo incompleto de errores de las fuentes externas. | Respuestas inestables y dificultades para diagnosticar fallos. | Estandarizar el manejo de errores y agregar pruebas para respuestas inválidas, vacías y fallos de conexión. |
| DT-04 | Cobertura insuficiente del flujo completo de búsqueda. | Las regresiones pueden pasar inadvertidas durante la integración. | Incorporar pruebas del flujo principal al pipeline de integración continua. |
| DT-05 | Evidencias de calidad y operación incompletas. | Dificultad para demostrar el cumplimiento de los requisitos de calidad. | Conservar resultados verificables de pruebas, análisis de calidad y comprobaciones del despliegue. |

Los elementos que dependan de una condición específica deben verificarse contra la versión actual del repositorio antes de considerarse deuda técnica confirmada.

## 11.4. Estrategia de seguimiento

La gestión de riesgos y deuda técnica se realizará mediante las siguientes actividades:

1. **Verificación:** contrastar cada riesgo con el código, las pruebas, la configuración y la infraestructura existentes.
2. **Priorización:** atender primero los riesgos que puedan afectar el funcionamiento de la búsqueda, la coherencia arquitectónica o la seguridad.
3. **Asignación:** asociar cada acción correctiva con una tarea y un responsable del equipo.
4. **Implementación:** realizar los cambios necesarios en el código, las pruebas o la documentación.
5. **Validación:** comprobar los resultados mediante pruebas reproducibles y conservar la evidencia correspondiente.
6. **Actualización:** revisar esta sección cuando cambie una decisión arquitectónica, se cierre una deuda técnica o aparezca un riesgo nuevo.

## 11.5. Relación con otras secciones de arc42

- **Sección 4 — Estrategia de solución:** relaciona los riesgos con los principios arquitectónicos de DRIFT.
- **Sección 5 — Vista de bloques:** identifica los componentes afectados por cada riesgo.
- **Sección 6 — Vista de ejecución:** permite analizar los escenarios de búsqueda y manejo de errores.
- **Sección 7 — Vista de despliegue:** describe los riesgos asociados a configuración, disponibilidad y operación.
- **Sección 8 — Conceptos transversales:** documenta mecanismos compartidos de validación, manejo de errores, logging y pruebas.
- **Sección 9 — Decisiones arquitectónicas:** registra las decisiones que justifican las soluciones adoptadas.
- **Sección 10 — Requisitos de calidad:** relaciona los riesgos con atributos como mantenibilidad, confiabilidad y capacidad de prueba.
- **Sección 12 — Glosario:** define los términos técnicos necesarios para interpretar esta sección.

## 11.6. Estado y mantenimiento de la sección

Esta sección constituye un registro inicial de riesgos y deuda técnica. Las valoraciones y los elementos pendientes de verificación deben ajustarse con base en la implementación real y en las evidencias obtenidas por el equipo.

La sección se considerará actualizada cuando los riesgos estén evaluados, las acciones prioritarias tengan responsables y los elementos cerrados cuenten con evidencia de validación.

## 11.7. Riesgos y deuda confirmados por el experimento E6

Verificados contra el código y las mediciones de [E6](../evidencias/e6-degradacion-bajo-carga.md) (octubre de 2026):

| Riesgo o deuda | Estado | Evidencia o mitigación |
|---|---|---|
| Una fuente lenta retenía la búsqueda y las respuestas sin esa fuente no lo avisaban. | Mitigado | Plazo por fuente de 3 s y aviso en `unavailable_sources` ([ADR-0008](../adr/0008-persistencia-ejecucion-y-degradacion-de-fuentes.md)); `backend/tests/test_source_degradation.py`. |
| Los adaptadores de Steam y CheapShark mantenían un lock durante la llamada HTTP y serializaban las búsquedas con caché fría. | Mitigado | `SingleFlightCache`: el lock protege solo el diccionario. |
| Si la búsqueda no devuelve ningún juego, no hay resultado donde llevar el aviso de la fuente faltante. | Abierto | La respuesta es una lista de juegos; llevar el aviso fuera de ellos cambia el contrato `GET /games/search`. Queda visible en los logs `source_unavailable` y `external_request_failed`; la métrica `drift_source_unavailable_total` no lo cuenta porque se calcula a partir de los resultados devueltos. Ver S11-F13. |
| Cada llamada `httpx.get` crea un cliente y su contexto TLS. En el equipo de medición cuesta cerca de 0,5 s de CPU por cliente. | Abierto | Medido al preparar E6 y excluido del experimento (ver límites de validez). La corrección es un cliente HTTP compartido por adaptador. |
| La fuente primaria (Steam) no tiene plazo propio. | Mitigado en S11 | Timeout explícito (3 s por defecto, configurable) y un reintento acotado en el adaptador; antes dependía del timeout por defecto de `httpx`. Ver §11.8. |
| No hay circuito de corte: la fuente que vence se vuelve a consultar en la siguiente búsqueda. | Aceptado | Descartado en ADR-0008 por añadir dependencias; revisar si la degradación se vuelve sostenida. |
| El hilo de una consulta abandonada sigue vivo hasta su timeout HTTP (5 s). | Aceptado | Acotado por ese timeout; con degradación sostenida puede acumular hilos. |
| Catálogo y cachés en memoria: se pierden al reiniciar y no se comparten entre réplicas. | Aceptado | Decisión 1 de ADR-0008. |

## 11.8. Modos de fallo de la integración con Steam (evidencia S11)

Alcance: la ruta `GET /games/search` → `SearchGames` → `CombinedGameRepository` → `ResilientGameRepository` → `SteamGameRepository` (`backend/app/infrastructure/external/steam/steam_game_repository.py`). El resto de adaptadores (CheapShark, PlayStation, requisitos de Steam) no se modificó y solo se menciona donde un fallo los afecta.

**Cómo leer la tabla.** Ningún modo de fallo está confirmado como ocurrido en producción: el repositorio no contiene registros de incidentes reales, y E6 usó fuentes simuladas. Todos son riesgos potenciales derivados del código. La columna «Exposición» es una valoración cualitativa del equipo, no una medición. Los intentos se cuentan como totales: 2 significa una llamada inicial y un reintento.

Los tres casos de la semana están en estas filas: Steam **no responde** (F01, F04 y F10), **responde tarde** (F02 y F12) y **responde dos veces** (F14). La repetición iniciada por el cliente es otro caso y está en F07.

| ID | Modo de fallo | Causa | Consecuencia para DRIFT | Exposición (cualitativa) | Impacto | Mitigación | Estado | Evidencia |
|---|---|---|---|---|---|---|---|---|
| S11-F01 | Steam no responde | Caída, DNS o conexión rechazada | Sin precios de Steam en la búsqueda | Media | Medio | Un reintento con backoff y jitter; si persiste, respaldo local y aviso en `unavailable_sources` | Implementada | `backend/tests/test_steam_resilience.py`: `test_transient_failure_is_retried_and_recovers`, `test_endpoint_reports_a_steam_failure_instead_of_a_silent_empty_search`; `test_search_games.py::test_search_uses_fallback_when_steam_is_unavailable` |
| S11-F02 | Steam responde después del tiempo límite | Latencia alta de Steam o de la red | Búsqueda lenta; antes dependía del timeout por defecto de `httpx` (5 s) | Media | Medio | Timeout explícito de 3 s por defecto (`DRIFT_STEAM_TIMEOUT_SECONDS`), un reintento y respaldo | Implementada, con límite: `httpx` aplica el timeout por fase (conexión, lectura, escritura), no como plazo total | `test_timeout_is_explicit_and_exhausts_the_attempts` |
| S11-F03 | Steam devuelve HTTP 429 | Exceso de peticiones desde la IP de la API | Sin precios de Steam; presión adicional si se insiste | Baja a media (cada búsqueda lanza hasta 6 llamadas) | Medio | Se respeta `Retry-After` en segundos si es ≤ `DRIFT_STEAM_MAX_RETRY_AFTER_SECONDS` (2 s); si pide más, se falla rápido y se degrada; sin la cabecera, backoff | Parcial: no se interpreta `Retry-After` en formato de fecha HTTP | `test_429_waits_for_retry_after_when_it_is_tolerable`, `test_429_with_excessive_retry_after_fails_fast`, `test_429_without_retry_after_uses_backoff` |
| S11-F04 | Steam devuelve HTTP 5xx | Fallo interno o mantenimiento de Steam | Igual que F01 | Media | Medio | Un reintento con backoff; después, respaldo y aviso | Implementada | `test_transient_failure_is_retried_and_recovers[500/503]`, `test_persistent_5xx_ends_as_controlled_error` |
| S11-F05 | Steam devuelve HTTP 4xx no transitorio | Petición rechazada o bloqueo (por ejemplo 403) | Reintentar no ayuda y agrava un posible bloqueo | Baja | Medio | Sin reintentos; respaldo y aviso | Implementada | `test_permanent_4xx_is_never_retried`, `test_endpoint_does_not_retry_a_permanent_4xx` |
| S11-F06 | JSON inválido o datos incompletos | Página HTML de error, cambio de formato o respuesta truncada | Antes (por lectura del código, sin prueba): `ValueError` o `KeyError` sin controlar y la API respondía 500 | Baja | Alto antes, medio ahora | Validación de la estructura: respuesta inválida se eleva como `ExternalSourceError` (respaldo y aviso); ítems sin `id` o `name` se descartan y, si todos son inválidos, se trata como fallo; un juego sin precio o con importe no numérico es un dato válido y queda sin precio | Implementada en el adaptador de Steam de búsqueda | `test_invalid_json_is_a_controlled_error_without_retry`, `test_malformed_search_payload_is_an_error_not_an_empty_result`, `test_incomplete_details_yield_a_game_without_price` |
| S11-F07 | El cliente repite la misma búsqueda | Reintento del usuario o del frontend | Ninguno: `GET /games/search` es una lectura sin efectos de negocio | Alta | Bajo | Caché en memoria de 60 s por consulta; análisis en arc42 §8.12 | Implementada (comportamiento previo) | `test_repeating_a_search_is_a_side_effect_free_read` |
| S11-F08 | Solicitudes concurrentes de búsqueda | Varios usuarios consultan lo mismo a la vez | Llamadas duplicadas a Steam | Media | Bajo a medio | `SingleFlightCache`: una carga en vuelo por clave | Parcial: consultas distintas simultáneas no tienen límite global de concurrencia hacia Steam | `test_source_degradation.py::test_single_flight_cache_loads_each_key_once_under_concurrency` |
| S11-F09 | Dependencia indisponible durante varias solicitudes | Caída sostenida de Steam | Cada búsqueda vuelve a pagar el intento fallido y su reintento | Baja | Medio | Circuit breaker evaluado y diferido, con criterios de revisión en ADR-0009 | Pendiente (decisión de posponer) | [ADR-0009](../adr/0009-decision-extraccion-integracion-steam.md) |
| S11-F10 | Conexión interrumpida durante la llamada | Corte de red o cierre remoto | Igual que F01 | Baja | Medio | Se trata como error de conexión: un reintento y respaldo | Implementada | `test_transient_failure_is_retried_and_recovers[RemoteProtocolError]` |
| S11-F11 | Respuesta inválida de una fuente secundaria (CheapShark, PlayStation) | Cuerpo no JSON o formato inesperado | Por lectura del código: `CombinedGameRepository` solo captura `httpx.HTTPError`; un `ValueError` de esas fuentes podría llegar al endpoint como 500. No verificado con una prueba | Baja | Alto | Reutilizar `get_json` en esos adaptadores y capturar `ExternalSourceError` | Pendiente (fuera del alcance S11) | Sin prueba |
| S11-F12 | La latencia acumulada por reintentos supera el umbral de E6 | Timeout de 3 s por intento, 2 intentos y espera de hasta 0,25 s | En el peor caso, cada fase (búsqueda y detalles) puede tardar cerca de 6,25 s antes del respaldo, frente al umbral p95 ≤ 5 s de E6. No medido | Baja | Medio | Los valores son configurables; falta un plazo total por búsqueda y medirlo con fuentes degradadas | Parcial | Cálculo por configuración; sin medición |
| S11-F13 | Steam cae y el respaldo no tiene el juego | Falla de Steam con una consulta que `InMemoryGameRepository` no contiene | La respuesta es una lista vacía con 200 y no se distingue de «sin resultados» | Media | Medio | Llevar el aviso fuera de la lista cambia el contrato; por ahora queda en el log `external_request_failed` (fuente, motivo, intentos, latencia) | Parcial: observable en logs, no en la respuesta ni en la métrica | Log verificado en `test_logs_report_retries_and_failures_without_the_user_query` |
| S11-F14 | Steam responde dos veces | (a) El mismo juego aparece dos veces en una misma respuesta de búsqueda. (b) Un reintento se lanza mientras la respuesta del primer intento todavía llega tarde | (a) Antes, verificado con prueba: el juego salía repetido en los resultados y sus detalles se pedían dos veces. (b) Ninguno: al vencer el plazo, el primer intento se abandona y su respuesta se descarta; la consulta es una lectura, así que Steam atiende dos lecturas sin efecto de negocio | Baja | Bajo | (a) Se conserva la primera aparición de cada juego por su id. (b) Solo se reintentan lecturas, que son idempotentes (§8.12) | Implementada | (a) `test_a_game_repeated_in_the_response_is_returned_once`; (b) `test_timeout_is_explicit_and_exhausts_the_attempts` |

### Mitigaciones implementadas y pendientes

Implementadas (`backend/app/infrastructure/external/resilient_http.py` y `SteamGameRepository`): timeout explícito y configurable, reintentos limitados a fallos transitorios, backoff exponencial con jitter completo, respeto de `Retry-After` en segundos, validación de la estructura de las respuestas, error controlado `ExternalSourceError` que `ResilientGameRepository` convierte en respaldo con aviso, y registros `external_retry` y `external_request_failed` sin la consulta del usuario.

Pendientes: circuit breaker (ADR-0009), plazo total por búsqueda, `Retry-After` en formato fecha, límite global de concurrencia hacia Steam, cliente HTTP compartido, extender el cliente resiliente a CheapShark, PlayStation y requisitos de Steam, y aviso en la respuesta cuando no hay resultados (requiere cambio de contrato).

Observabilidad: solo hay registros JSON. Los reintentos no tienen contador en `/metrics`, por lo que no existen métricas persistentes de reintentos; las existentes se reinician con el proceso.
