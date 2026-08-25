# Matriz comparativa de estilos arquitectónicos

## Criterios de evaluación

Comparar los estilos de arquitectura en capas, arquitectura hexagonal y monolito modular frente a los escenarios de calidad definidos para DRIFT, con especial énfasis en la mantenibilidad, atributo de calidad priorizado por el equipo.

| Criterio | Arquitectura en capas | Arquitectura hexagonal | Monolito modular |
|---|---|---|---|
| Mantenibilidad | Media | **Alta** | Media-Alta |
| Incorporar nuevas plataformas | Media | **Alta** | Media-Alta |
| Cambiar una API externa | Media | **Alta** | Media |
| Aislamiento de cambios | Media | **Alto** | Media-Alta |
| Bajo acoplamiento | Media | **Alto** | Media-Alta |
| Facilidad de pruebas | Media | **Alta** | Alta |
| Complejidad inicial | **Baja** | Media-Alta | Media |
| Adecuación a DRIFT | Media | **Alta** | Media-Alta |

## Relación con los escenarios de calidad

La evaluación de los estilos arquitectónicos se relaciona con los escenarios E1-E5 definidos en el árbol de utilidad y detallados en [`docs/escenarios.md`](docs/escenarios.md). Estos escenarios permiten evaluar cómo cada alternativa responde a las necesidades de calidad de DRIFT.

| Escenario | Atributo de calidad | Arquitectura en capas | Arquitectura hexagonal | Monolito modular |
|---|---|---|---|---|
| [E1](escenarios.md#escenario-1) - Búsqueda y comparación de precios | Rendimiento | Media | **Alta** | Media-Alta |
| [E2](escenarios.md#escenario-2) - Modificar una fuente externa sin afectar el sistema | Mantenibilidad | Media | **Muy Alta** | Media-Alta |
| [E3](escenarios.md#escenario-3) - Identificación de la opción recomendada | Usabilidad | Media | **Alta** | Alta |
| [E4](escenarios.md#escenario-4) - Compatibilidad del dispositivo | Compatibilidad | Media | **Alta** | Alta |
| [E5](escenarios.md#escenario-5) - Fallo de una fuente externa de precios | Disponibilidad | Media | **Muy Alta** | Media |

## Análisis

### Arquitectura en capas

Presenta una estructura sencilla y conocida, separando presentación, lógica de negocio y acceso a datos. Su principal ventaja es la baja complejidad inicial. Sin embargo, los cambios relacionados con una fuente externa pueden propagarse entre diferentes capas, aumentando el impacto de mantenimiento.

### Arquitectura hexagonal

Separa el núcleo de negocio de las tecnologías y servicios externos mediante puertos y adaptadores. Esto resulta especialmente adecuado para DRIFT, debido a que el sistema debe obtener información de diferentes plataformas de videojuegos. La incorporación o modificación de una plataforma puede realizarse principalmente mediante cambios en sus adaptadores, reduciendo el impacto sobre la lógica de negocio.

### Monolito modular

Permite mantener una única aplicación desplegable, pero organizada en módulos con responsabilidades claramente delimitadas. Facilita el mantenimiento y permite aislar funcionalidades, aunque requiere disciplina para evitar dependencias excesivas entre módulos.

## Decisión

La arquitectura hexagonal obtiene la mejor valoración para DRIFT debido a su capacidad para aislar las dependencias externas y facilitar la incorporación de nuevas plataformas. Aunque presenta una mayor complejidad inicial que las otras alternativas, esta complejidad se considera aceptable frente al beneficio obtenido en mantenibilidad y capacidad de evolución.
