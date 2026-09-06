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
