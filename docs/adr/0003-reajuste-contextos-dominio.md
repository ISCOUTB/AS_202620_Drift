# ADR-0003: Reajuste de contextos y responsabilidades del dominio

**Estado:** Aceptado  
**Fecha:** 2026-09-14

## Contexto

Durante el desarrollo del corte 1, DRIFT se documentó principalmente alrededor del flujo de búsqueda y comparación de videojuegos. Con la evolución del sistema se incorporaron nuevas responsabilidades relacionadas con la resiliencia frente a fallos de fuentes externas y la estimación de compatibilidad de PC.

El análisis realizado en el corte 2 identificó la necesidad de delimitar mejor estas responsabilidades y establecer la propiedad de los datos para evitar que diferentes partes del sistema modifiquen o administren la misma información sin una responsabilidad clara.

Los contextos delimitados identificados son:

- **Búsqueda y comparación:** responsable de la consulta y representación de la información de videojuegos utilizada por el usuario.
- **Integración de fuentes externas:** responsable de obtener información desde fuentes externas y gestionar la fuente de respaldo cuando una fuente principal no está disponible.
- **Compatibilidad de PC:** responsable de consultar los requisitos de un videojuego y estimar su compatibilidad con el hardware del usuario.
- **Experiencia de usuario:** actúa como cliente de los contextos anteriores y presenta sus resultados al usuario.

Esta delimitación se encuentra documentada en la sección de conceptos transversales y en la evidencia del corte 2.

## Problema

El C4 de nivel 3 del primer corte no representaba completamente las nuevas responsabilidades incorporadas al sistema. En particular, no mostraba explícitamente los componentes relacionados con la resiliencia de las fuentes externas ni con la compatibilidad de PC.

Mantener el diagrama anterior generaría una diferencia entre la arquitectura implementada y la arquitectura documentada.

## Alternativas consideradas

### Opción 1: Mantener los límites del primer corte

Conservar el modelo original de búsqueda y comparación sin representar explícitamente las nuevas responsabilidades.

**Desventajas:**

- La documentación no reflejaría completamente el sistema actual.
- Las responsabilidades quedarían menos claras.
- Se dificultaría identificar la propiedad de los datos.

### Opción 2: Reajustar los contextos y responsabilidades manteniendo la arquitectura Hexagonal

Actualizar los límites lógicos y el C4 de nivel 3 para representar las nuevas responsabilidades, manteniendo la Arquitectura Hexagonal como arquitectura base.

**Ventajas:**

- Mantiene la decisión arquitectónica existente.
- Mejora la separación de responsabilidades.
- Permite identificar claramente los puertos y adaptadores involucrados.
- Facilita la evolución del sistema sin introducir una nueva arquitectura.

### Opción 3: Separar inmediatamente los contextos en servicios independientes

Convertir cada contexto en un servicio desplegable independiente.

**Desventajas:**

- Introduce complejidad innecesaria para el estado actual del proyecto.
- Requiere mecanismos adicionales de comunicación y despliegue.
- No es necesario para cumplir el objetivo de separación lógica de responsabilidades.

## Decisión

Se selecciona la **Opción 2: Reajustar los contextos y responsabilidades manteniendo la Arquitectura Hexagonal**.

Los nuevos límites se representan mediante responsabilidades diferenciadas dentro de la arquitectura existente:

- `SearchGames` representa la responsabilidad de búsqueda.
- `ResilientGameRepository` coordina la fuente principal y el catálogo de respaldo.
- `SteamGameRepository` actúa como adaptador hacia Steam.
- `InMemoryGameRepository` proporciona la fuente local de respaldo.
- `EstimateCompatibility` representa el caso de uso de compatibilidad.
- `GameRequirementsRepository` define el puerto para consultar los requisitos.
- `InMemoryGameRequirementsRepository` implementa dicho puerto.

Esta decisión **no introduce microservicios ni cambia los límites de despliegue del sistema**. Los contextos representan límites lógicos y responsabilidades dentro de la arquitectura actual.

## Propiedad de los datos

La delimitación se mantiene alineada con la propiedad de datos definida en el corte 2:


| Dato                          | Contexto responsable             |
|-------------------------------|----------------------------------|
| `Game`                        | Búsqueda y comparación         |
| Precios provenientes de Steam | Integración de fuentes externas |
| Catálogo local de respaldo   | Integración de fuentes externas |
| Datos de caché de Steam      | Integración de fuentes externas |
| `GameRequirements`            | Compatibilidad de PC             |
| Resultado de compatibilidad   | Compatibilidad de PC             |


La propiedad implica que cada contexto es responsable de administrar y transformar sus propios datos, evitando que otro contexto asuma directamente su modificación.

## Consecuencias

### Positivas

- Las responsabilidades del sistema quedan mejor delimitadas.
- El C4 de nivel 3 representa los componentes implementados actualmente.
- La integración con fuentes externas permanece aislada mediante puertos y adaptadores.
- La funcionalidad de compatibilidad mantiene su propia responsabilidad y puerto de acceso a requisitos.
- La propiedad de los datos queda explícita.
- Se conserva la mantenibilidad como atributo de calidad prioritario.

### Negativas

- Aumenta el número de componentes representados en la documentación.
- Se requiere mantener sincronizados C4, arc42 y la evidencia de contextos.
- La separación lógica requiere disciplina para evitar que un contexto modifique directamente los datos de otro.

## Trazabilidad

- [C4 — Diagrama de componentes](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/c4/componentes.md)
- [Arc42 — Conceptos transversales](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/arc42/08-conceptos-transversales.md)
- [Corte 2 — Contextos y propiedad de datos](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/semana-06-contextos-y-propiedad-de-datos.md)
- [ADR-0002 — Selección de Arquitectura Base](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/adr/0002-arquitectura-base.md)

**Commit de implementación:** pendiente de asociar después de realizar el commit de esta actualización.

 
