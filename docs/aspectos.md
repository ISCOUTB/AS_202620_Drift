# Aspectos de Calidad

## Aspecto declarado: Mantenibilidad

### Descripción

DRIFT debe contar con una arquitectura que permita modificar, ampliar y mantener el sistema sin afectar de manera significativa las funcionalidades existentes. Este aspecto busca facilitar principalmente:

* Incorporar nuevas plataformas digitales o tiendas de videojuegos.
* Agregar nuevas fuentes de información sobre precios y disponibilidad.
* Modificar la lógica de comparación y recomendación.
* Añadir nuevos filtros o características para personalizar las búsquedas.
* Realizar cambios en un componente sin generar problemas en otras partes del sistema.

### Por qué se eligió este aspecto

La plataforma dependerá de información proveniente de diferentes tiendas y servicios, los cuales pueden cambiar con el tiempo. Además, DRIFT está planteado para crecer e incorporar nuevas plataformas, funcionalidades y criterios de recomendación. Por esta razón, una arquitectura mantenible permitirá realizar estos cambios de forma organizada, reduciendo el impacto sobre el sistema y facilitando su evolución.

### Cómo se va a evaluar 

La mantenibilidad se evaluará mediante la capacidad de incorporar una nueva plataforma o fuente de precios sin realizar modificaciones importantes en los demás componentes del sistema. También se revisará que las funcionalidades estén separadas de manera que los cambios puedan realizarse de forma independiente y que el código sea fácil de comprender y mantener.

### Estado

* Aspecto identificado y declarado
* Arquitectura y mecanismos para favorecerlo definidos
* Implementado
* Pruebas de mantenibilidad realizadas

### Decisión arquitectónica relacionada

La mantenibilidad es el principal atributo de calidad considerado en la selección de la arquitectura de DRIFT. El ADR-0002 establece la **Arquitectura Hexagonal (Ports and Adapters)** como arquitectura base, debido a su bajo acoplamiento, facilidad para incorporar nuevas integraciones y capacidad para facilitar la evolución del sistema.

* [`ADR-0002: Selección de Arquitectura Base`](adr/0002-arquitectura-base.md)

## Escenarios de calidad

| ID | Aspecto de calidad | Escenario | Medida verificable | Enlace |
|---|---|---|---|---|
| E1 | Eficiencia de desempeño | Búsqueda y comparación de precios | ≤ 3 segundos en p95 con hasta 50 usuarios concurrentes | [Escenario 1](escenarios.md#escenario-1) |
| E2 | Eficiencia de desempeño | Consulta de información del videojuego | ≤ 3 segundos en p95 con hasta 50 usuarios concurrentes | [Escenario 2](escenarios.md#escenario-2) |
| E3 | Usabilidad / eficiencia | Identificación de la opción recomendada | Máximo 3 interacciones | [Escenario 3](escenarios.md#escenario-3) |
| E4 | Rendimiento / compatibilidad | Consulta de compatibilidad del dispositivo | ≤ 5 segundos en p95 | [Escenario 4](escenarios.md#escenario-4) |
| E5 | Disponibilidad | Fallo de una fuente externa de precios | Mantener la consulta operativa y mostrar las demás fuentes en ≤ 5 segundos | [Escenario 5](escenarios.md#escenario-5) |
