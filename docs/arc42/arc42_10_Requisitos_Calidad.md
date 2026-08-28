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


Estas cinco categorías cubren la totalidad de los objetivos de calidad declarados en la Sección 1.2, más la testabilidad como consecuencia directa de la decisión de arquitectura documentada en la Sección 9.

## 10.2 Escenarios de calidad

Los siguientes escenarios detallan, en formato fuente–estímulo–artefacto–entorno–respuesta–medida, los objetivos de calidad de la tabla anterior. Los cinco primeros corresponden a los definidos en `docs/Escenarios.md`; se añade su trazabilidad hacia la categoría de calidad correspondiente.

| ID | Categoría | Fuente del estímulo | Estímulo | Artefacto | Entorno | Respuesta | Medida de respuesta |
|---|---|---|---|---|---|---|---|
| QS-01 | Rendimiento | Jugador | Realiza una búsqueda y comparación de precios de un videojuego | Servicio de Búsqueda y Comparación (Sección 5.2.1) | Operación normal, todas las fuentes externas disponibles | El sistema consulta las tiendas digitales y devuelve la comparación | ≤ 3 s en el percentil 95 |
| QS-02 | Rendimiento | Jugador | Consulta la información de un videojuego específico | Núcleo de dominio / Adaptador de Proveedor de Información | Operación normal | El sistema devuelve la información del videojuego | ≤ 2 s en el percentil 95 |
| QS-03 | Compatibilidad | Jugador | Solicita estimar la compatibilidad/rendimiento de un videojuego en su PC | Servicio de Estimación de Compatibilidad (Sección 5.2.1) | Operación normal, specs del dispositivo ya registradas | El sistema compara especificaciones vs. requisitos y devuelve una estimación | ≤ 5 s en el percentil 95 |
| QS-04 | Disponibilidad | Fuente externa de precios (tienda digital) | Deja de responder o responde con error/timeout | Adaptador de Tiendas Digitales / sub-adaptador afectado (Sección 5.2.2) | Una fuente externa falla, las demás operan con normalidad | El sistema continúa mostrando la información de las fuentes disponibles e informa que la fuente afectada no está disponible | Respuesta completa (parcial + aviso) en ≤ 5 s |
| QS-05 | Usabilidad | Jugador | Busca identificar la opción de compra más conveniente entre varias | Adaptador Web/API + Servicio de Recomendación | Operación normal, resultados de comparación ya disponibles | El sistema resalta o recomienda explícitamente la mejor opción | Identificable en un número reducido de interacciones *(pendiente de definir el número exacto en `docs/Escenarios.md`)* |
