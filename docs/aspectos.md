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

Los escenarios de calidad de DRIFT se documentan mediante los elementos de fuente, estímulo, artefacto, entorno, respuesta y medida verificable. La siguiente tabla consolida estos elementos junto con el atributo de calidad y el identificador de cada escenario.

| ID | Aspecto de calidad | Fuente | Estímulo | Artefacto | Entorno | Respuesta | Medida verificable |
|---|---|---|---|---|---|---|---|
| [E1](escenarios.md#escenario-1) | Eficiencia de desempeño | Usuario de DRIFT. | El usuario realiza una búsqueda de un videojuego para comparar su precio. | Módulo de búsqueda y comparación de precios de DRIFT. | Sistema funcionando normalmente con hasta 50 usuarios concurrentes. | DRIFT consulta y muestra los precios disponibles del videojuego en las diferentes tiendas digitales. | ≤ 3 segundos en el p95. |
| [E2](escenarios.md#escenario-2) | Eficiencia de desempeño | Usuario de DRIFT. | El usuario selecciona un videojuego de los resultados de búsqueda. | Módulo de información y detalle del videojuego. | Sistema funcionando normalmente con hasta 50 usuarios concurrentes. | DRIFT muestra información del videojuego, incluyendo precios, descuentos, plataformas disponibles e historial de precios. | ≤ 3 segundos en el p95. |
| [E3](escenarios.md#escenario-3) | Usabilidad / eficiencia | Usuario de DRIFT. | El usuario busca un videojuego y desea determinar cuál de las opciones disponibles es más conveniente. | Módulo de comparación y recomendación de DRIFT. | Usuario con acceso a los resultados de las diferentes tiendas digitales. | DRIFT presenta las opciones ordenadas o diferenciadas según precio, disponibilidad de plataforma y demás criterios considerados por el sistema. | Máximo 3 interacciones. |
| [E4](escenarios.md#escenario-4) | Rendimiento / compatibilidad | Usuario con un dispositivo PC registrado en DRIFT. | El usuario consulta un videojuego para conocer si su equipo puede ejecutarlo. | Módulo de compatibilidad y estimación de rendimiento. | El usuario tiene previamente registrado su dispositivo y sus especificaciones. | DRIFT compara las especificaciones del dispositivo con los requisitos del videojuego e informa el nivel de compatibilidad o rendimiento estimado. | ≤ 5 segundos en el p95. |
| [E5](escenarios.md#escenario-5) | Disponibilidad | Servicio externo de una tienda digital. | Una de las fuentes externas de precios deja de responder durante una consulta. | Módulo de consulta e integración de fuentes de precios de DRIFT. | DRIFT se encuentra funcionando normalmente y el usuario está realizando una comparación de precios. | DRIFT continúa mostrando la información obtenida de las demás fuentes disponibles e indica que una fuente no pudo ser consultada. | Consulta operativa y demás fuentes disponibles en ≤ 5 segundos. |
