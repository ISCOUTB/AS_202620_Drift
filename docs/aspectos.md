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
* Arquitectura y mecanismos para garantizarlo definidos
* Implementado
* Pruebas de mantenibilidad realizadas
