# 10. Requisitos de calidad

Esta sección amplía los objetivos de calidad ya introducidos en la Sección 1.2, presentándolos primero como una visión general (árbol/tabla de calidad, 10.1) y luego como escenarios de calidad detallados y medibles (10.2).

## 10.1 Árbol de calidad

| Categoría de calidad | Etiqueta | Descripción para DRIFT |
|---|---|---|
| **Mantenibilidad** | `#flexible` `#modifiable` | Incorporar nuevas plataformas, fuentes de información y funcionalidades sin generar cambios importantes en otros componentes (Sección 1.2, prioridad 1). |
| **Rendimiento** | `#efficient` | Tiempos de respuesta adecuados en búsqueda, comparación, consulta de información y estimación de compatibilidad (Sección 1.2, prioridad 2). |
| **Disponibilidad** | `#reliable` | Mantener la consulta de información operativa cuando una fuente externa de precios falla (Sección 1.2, prioridad 3). |
| **Usabilidad** | `#usable` | Permitir identificar y utilizar la opción más conveniente con una cantidad reducida de interacciones (Sección 1.2, prioridad 4). |
| **Compatibilidad** | `#compatible` | Estimar si un videojuego puede ejecutarse adecuadamente en el dispositivo del usuario (Sección 1.2, prioridad 5). |


Estas cinco categorías cubren la totalidad de los objetivos de calidad declarados en la Sección 1.2 y mantienen trazabilidad con los escenarios de calidad definidos para DRIFT.

## 10.2 Escenarios de calidad

Los siguientes escenarios detallan, en formato fuente–estímulo–artefacto–entorno–respuesta–medida, los objetivos de calidad de la tabla anterior. Los escenarios mantienen trazabilidad con los definidos en `docs/escenarios.md`.

| ID | Categoría | Fuente del estímulo | Estímulo | Artefacto | Entorno | Respuesta | Medida de respuesta |
|---|---|---|---|---|---|---|---|
| E1 | Rendimiento | Jugador | Realiza una búsqueda de un videojuego | Servicio de Búsqueda y Comparación | Hasta 50 usuarios concurrentes, operación normal | El sistema procesa la búsqueda y devuelve los resultados | ≤ 3 s en el percentil 95 |
| E2 | Mantenibilidad | Equipo de desarrollo | Una API externa de precios cambia su contrato | Adaptador de la fuente externa | Durante una modificación de una integración externa | Se modifica el adaptador correspondiente sin alterar el núcleo de dominio ni otros adaptadores | El cambio queda aislado en el adaptador afectado |
| E3 | Usabilidad | Jugador | Busca identificar la opción de compra más conveniente | Interfaz Web + Servicio de Recomendación | Operación normal | El sistema presenta claramente la opción recomendada | La opción recomendada debe ser identificable en un máximo de 3 interacciones |
| E4 | Compatibilidad | Jugador | Consulta si un videojuego puede ejecutarse en su PC | Servicio de Estimación de Compatibilidad | Especificaciones del dispositivo disponibles | El sistema compara las especificaciones del usuario con los requisitos del videojuego y devuelve una estimación | ≤ 5 s en el percentil 95 |
| E5 | Disponibilidad | Fuente externa de precios | Una fuente externa deja de responder o presenta un error | Adaptador de Tiendas Digitales | Una fuente falla mientras las demás continúan disponibles | El sistema continúa mostrando las fuentes disponibles e informa la indisponibilidad de la fuente afectada | Respuesta parcial con aviso en ≤ 5 s |

### Escenario E6 (octubre de 2026)

| ID | Atributo | Escenario | Medida | Estado |
|---|---|---|---|---|
| [E6](../escenarios.md#escenario-6) | Disponibilidad y rendimiento | Con 50 usuarios concurrentes y CheapShark lento en cerca del 35 % de las consultas, DRIFT responde con las demás fuentes y avisa cuál faltó. | p95 ≤ 5 s, < 1 % de fallos, 0 respuestas degradadas sin aviso. | Medido antes y después: [evidencia E6](../evidencias/e6-degradacion-bajo-carga.md). |

### Medición de E1 (noviembre de 2026)

El umbral de E1 (≤ 3 s en el p95, hasta 50 usuarios concurrentes, operación normal) no cambió. La medición de S14 se juzgó contra ese valor. **En el despliegue no cumple:** con búsquedas distintas, el p95 mediano fue de 9,05 s en 3 corridas. Con la misma búsqueda fue de 2,40 s y cumplió en 2 de 3. Ver [evidencia S14](../evidencias/s14-e1-medicion.md) y [§11.10](arc42-11-riesgos-y-deuda-tecnica.md#1110-revisión-entre-pares-y-medición-de-e1-evidencia-s14).

Una [medición local con fuentes simuladas](../evidencias/s14-medicion-e1.md) dio un p95 mediano de 0,63 s en 5 corridas. Muestra el costo propio de la búsqueda, sin fuentes reales ni TLS por cliente, y no describe el sistema desplegado.

## 10.3 Estado de cada escenario a la entrega final (22 de noviembre de 2026)

Los umbrales no se cambiaron para hacerlos cumplir. «Medido» significa que hay una corrida con procedimiento y resultados versionados; «probado» significa que hay pruebas automatizadas que verifican el comportamiento pero no la cifra.

| Escenario | Umbral | Estado | Evidencia vigente |
|---|---|---|---|
| E1 Rendimiento | p95 ≤ 3 s, 50 usuarios | **Medido: no cumple en el despliegue** (p95 mediano de 9,05 s con búsquedas distintas). En local, con fuentes simuladas, cumple (0,63 s y 0,96 s). | [S14 despliegue](../evidencias/s14-e1-medicion.md), [S14 local](../evidencias/s14-medicion-e1.md), [remedición](../evidencias/s14-remedicion-e1-e6.md) |
| E2 Mantenibilidad | cambiar una fuente sin tocar el dominio | **Probado y demostrado:** Xbox e IsThereAnyDeal se agregaron como adaptadores nuevos sin cambiar `SearchGames` ni el dominio; la regla la vigilan `test_architecture.py` y `scripts/validar_docs.py` en cada CI. | PR #62, [C4 nivel 3](../c4/componentes.md) |
| E3 Usabilidad | opción más conveniente en ≤ 3 interacciones | **Probado manualmente** (sin medición con usuarios externos). | [Evidencia E3](../evidencias/e3-usabilidad.md) |
| E4 Compatibilidad | p95 ≤ 5 s | **Probado; la latencia no se ha medido.** Las pruebas verifican el resultado de la comparación, no el tiempo. | [Evidencia E4](../evidencias/e4-compatibilidad.md), `test_compatibility.py`, `test_hardware_benchmarks.py` |
| E5 Disponibilidad | sigue con las demás fuentes y responde en ≤ 5 s | **Probado y medido en local con fuentes simuladas** (Steam sin responder: p95 de 4,01 s). | [S12](../evidencias/s12-steam-degradado.md), `test_source_degradation.py`, `test_copia_de_respaldo.py` |
| E6 Disponibilidad y rendimiento | p95 ≤ 5 s con una fuente lenta | **Medido en local con fuentes simuladas:** cumple (3,41 s en la remedición); no medido en el despliegue. | [E6](../evidencias/e6-degradacion-bajo-carga.md), [remedición](../evidencias/s14-remedicion-e1-e6.md) |
| Seguridad y privacidad (S13) | amenazas de prioridad Alta mitigadas antes que las demás | **Probado:** A1–A3 y A12–A14 mitigadas con prueba automatizada; pendientes y aceptadas declaradas. No es una auditoría de seguridad. | [Modelo de amenazas](../seguridad/modelo-amenazas.md), [privacidad](../seguridad/privacidad.md) |
