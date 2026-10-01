# ADR-0007 — Evaluación de incorporación de componente generativo

- **Estado:** Aceptado
- **Fecha:** 2026-09-30
- **Decisores:** Equipo DRIFT

## Contexto

DRIFT es una plataforma orientada a la búsqueda y comparación de videojuegos, integrando información proveniente de diferentes fuentes externas. El sistema contempla funcionalidades relacionadas con la búsqueda de juegos, comparación de precios y evaluación de compatibilidad de PC.

Durante la evolución del proyecto se ha considerado la posibilidad de incorporar nuevas funcionalidades relacionadas con la experiencia de usuario y el procesamiento de información. Sin embargo, el alcance actual de DRIFT no requiere un componente de Inteligencia Artificial generativa para cumplir sus funcionalidades principales.

Una posible incorporación de IA generativa podría tomar la forma de un chatbot o asistente capaz de interpretar solicitudes escritas en lenguaje natural, por ejemplo, recomendar juegos a partir de una descripción proporcionada por el usuario. Sin embargo, este tipo de interacción no forma parte de los objetivos actuales del sistema.

DRIFT puede realizar operaciones como la búsqueda y filtrado de videojuegos utilizando información estructurada. Por ejemplo, un usuario puede filtrar juegos por género sin necesidad de utilizar un modelo generativo, ya que esta operación puede resolverse mediante los datos y reglas correspondientes del sistema.

## Decisión

**No incorporar un componente de Inteligencia Artificial generativa dentro de DRIFT en el alcance actual del proyecto.**

La decisión se toma debido a que las funcionalidades actuales del sistema pueden implementarse mediante mecanismos convencionales de búsqueda, filtrado, comparación y procesamiento de datos estructurados, sin requerir generación de texto ni interpretación generativa de lenguaje natural.

En particular, la búsqueda y comparación de videojuegos, el filtrado por características como género y la evaluación de compatibilidad de PC corresponden a operaciones determinísticas sobre información disponible en el sistema o proporcionada por fuentes externas.

Por lo tanto, incorporar un chatbot o un modelo generativo en el estado actual del proyecto introduciría una capacidad que no es necesaria para cumplir los objetivos funcionales definidos.

Esta decisión no impide que una futura versión de DRIFT pueda evaluar nuevamente el uso de IA generativa si aparece una necesidad funcional que lo justifique. En ese caso, la incorporación deberá ser evaluada mediante una nueva decisión arquitectónica considerando su utilidad, complejidad, costos, dependencia de proveedores externos y efecto sobre la arquitectura existente.

## Alternativas consideradas

### Incorporar un chatbot generativo

Un chatbot podría permitir que los usuarios realizaran consultas en lenguaje natural, por ejemplo, describiendo el tipo de juego que buscan para recibir resultados.

Esta alternativa no se incorpora porque dicha interacción no es necesaria para las funcionalidades actuales de DRIFT. Las operaciones de búsqueda y filtrado pueden realizarse mediante los mecanismos existentes y datos estructurados.

### Utilizar IA generativa para recomendaciones

Otra posibilidad sería utilizar un modelo generativo para producir recomendaciones personalizadas de videojuegos.

Esta alternativa tampoco se incorpora debido a que el alcance actual de DRIFT está orientado principalmente a la búsqueda, comparación de precios y compatibilidad, y no requiere un sistema generativo de recomendaciones para cumplir estos objetivos.

### Mantener el procesamiento mediante lógica convencional

Se mantiene el uso de búsqueda, filtros, reglas de negocio y procesamiento de datos estructurados para las funcionalidades actuales.

Esta alternativa es coherente con el alcance definido para DRIFT y evita introducir una dependencia adicional de modelos generativos sin una necesidad funcional que la justifique.

## Consecuencias

### Positivas

- Se mantiene el alcance del proyecto enfocado en búsqueda, comparación y compatibilidad de videojuegos.
- Se evita introducir una dependencia adicional de proveedores o modelos de IA generativa.
- Se mantiene una arquitectura más sencilla para las funcionalidades actuales.
- Las operaciones de búsqueda y filtrado pueden mantenerse determinísticas y verificables.
- No se añaden costos asociados al consumo de servicios de modelos generativos.
- Se evita incorporar complejidad técnica que no aporta una funcionalidad necesaria para el alcance actual.

### Negativas

- DRIFT no podrá interpretar consultas complejas expresadas libremente en lenguaje natural mediante un modelo generativo.
- No se contará con un chatbot o asistente conversacional dentro de la plataforma.
- Una futura funcionalidad de recomendaciones generativas requeriría una nueva evaluación arquitectónica.

## Relación con la arquitectura existente

La decisión mantiene la arquitectura Hexagonal adoptada por DRIFT y no requiere incorporar nuevos puertos, adaptadores o servicios relacionados con modelos generativos.

Las funcionalidades actuales continúan utilizando las responsabilidades ya definidas para búsqueda, integración con fuentes externas, comparación y compatibilidad.

La ausencia de IA generativa es, por tanto, una decisión de alcance y arquitectura: no se incorpora un componente tecnológico cuando las necesidades actuales del sistema pueden resolverse mediante las capacidades existentes.

## Criterio para una futura reevaluación

La incorporación de IA generativa podrá volver a evaluarse si DRIFT incorpora una funcionalidad que requiera capacidades como:

- interpretación de consultas complejas en lenguaje natural;
- interacción conversacional con los usuarios;
- generación de recomendaciones a partir de información no estructurada;
- generación de contenido que forme parte de una funcionalidad explícita del sistema.

En ese caso, la decisión deberá documentarse mediante un nuevo ADR y evaluarse considerando el impacto sobre la arquitectura, las dependencias externas, los costos, la seguridad, la mantenibilidad y los requisitos funcionales correspondientes.

## Referencias

- [`docs/adr/0001-adoptar-arquitectura-hexagonal.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/adr/0001-adoptar-arquitectura-hexagonal.md)
- [`docs/adr/0002-adoptar-nextjs-fastapi-arquitectura-hexagonal.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/adr/0002-adoptar-nextjs-fastapi-arquitectura-hexagonal.md)
- [`docs/adr/0003-reajuste-contextos-dominio.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/adr/0003-reajuste-contextos-dominio.md)
- [`docs/adr/0004-estrategia-de-integracion.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/adr/0004-estrategia-de-integracion.md)
- [`docs/adr/0005-estrategia-despliegue.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/adr/0005-estrategia-despliegue.md)
- [`docs/adr/0006-despliegue-serverless-api-busqueda.md`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/adr/0006-despliegue-serverless-api-busqueda.md)
