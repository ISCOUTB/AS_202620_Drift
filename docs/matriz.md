# Matriz comparativa de estilos arquitectónicos

## Criterios de evaluación

Comparar los estilos de arquitectura en capas, arquitectura hexagonal y monolito modular frente a los escenarios de calidad definidos para DRIFT, con especial énfasis en la mantenibilidad, atributo de calidad priorizado por el equipo.

| Criterio | Capas | Hexagonal | Monolito modular |
|---|---|---|---|
| Mantenibilidad | Media-Alta | Alta | Alta |
| Incorporar nuevas plataformas | Media | Alta | Alta |
| Cambiar una API externa | Media | Alta | Alta |
| Aislamiento de cambios | Medio | Alto | Alto |
| Facilidad de pruebas | Media-Alta | Alta | Alta |
| Bajo acoplamiento | Medio | Alto | Alto |
| Complejidad inicial | Baja | Alta | Media |
| Adecuación a DRIFT | Media | Alta | Alta |

## Análisis

### Arquitectura en capas

Presenta una estructura sencilla y conocida, separando presentación, lógica de negocio y acceso a datos. Su principal ventaja es la baja complejidad inicial. Sin embargo, los cambios relacionados con una fuente externa pueden propagarse entre diferentes capas, aumentando el impacto de mantenimiento.

### Arquitectura hexagonal

Separa el núcleo de negocio de las tecnologías y servicios externos mediante puertos y adaptadores. Esto resulta especialmente adecuado para DRIFT, debido a que el sistema debe obtener información de diferentes plataformas de videojuegos. La incorporación o modificación de una plataforma puede realizarse principalmente mediante cambios en sus adaptadores, reduciendo el impacto sobre la lógica de negocio.

### Monolito modular

Permite mantener una única aplicación desplegable, pero organizada en módulos con responsabilidades claramente delimitadas. Facilita el mantenimiento y permite aislar funcionalidades, aunque requiere disciplina para evitar dependencias excesivas entre módulos.

## Decisión

La arquitectura hexagonal obtiene la mejor valoración para DRIFT debido a su capacidad para aislar las dependencias externas y facilitar la incorporación de nuevas plataformas. Aunque presenta una mayor complejidad inicial que las otras alternativas, esta complejidad se considera aceptable frente al beneficio obtenido en mantenibilidad y capacidad de evolución.
