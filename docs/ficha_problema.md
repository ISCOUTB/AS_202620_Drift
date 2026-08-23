# Ficha del problema — DRIFT

## Título del problema

**Plataforma web para comparar precios y rendimiento de videojuegos**

## Descripción

Los jugadores deben consultar diferentes tiendas digitales como Steam, Epic Games Store, PlayStation Store y Xbox Store para comparar el precio de un mismo videojuego. Esta información se encuentra distribuida entre distintas plataformas, haciendo que el usuario tenga que realizar las comparaciones manualmente.

Además del precio, la decisión de compra depende de factores como descuentos, historial de precios, plataforma disponible y, en PC, las características del equipo y los requisitos del videojuego. Al no contar con esta información centralizada, resulta difícil determinar cuál es la opción más conveniente.

Esto puede generar compras a precios más altos, mayor tiempo de búsqueda o adquirir un juego sin conocer el rendimiento que tendrá en el dispositivo disponible.
## Problema encontrado

* Los precios están distribuidos entre diferentes tiendas digitales.
* Cada plataforma maneja sus propios catálogos y descuentos.
* La información sobre requisitos y rendimiento se encuentra separada de los precios.
* El usuario debe comparar manualmente las diferentes opciones.
* No se tiene en cuenta de forma conjunta el precio, la plataforma disponible y el rendimiento del dispositivo.

## Impacto del problema

* Mayor tiempo dedicado a buscar y comparar videojuegos.
* Posibles compras a precios más altos.
* Dificultad para identificar la plataforma más conveniente.
* Riesgo de adquirir un juego que no tenga un rendimiento adecuado en el dispositivo disponible.

## Propuesta de solución

Desarrollar **DRIFT**, una plataforma web que permita:

* Comparar precios y descuentos entre plataformas.
* Consultar el historial de precios.
* Filtrar según las plataformas disponibles.
* Registrar los dispositivos del usuario.
* Estimar el rendimiento de un juego en PC según sus especificaciones.
* Recomendar la opción más conveniente considerando precio, compatibilidad y rendimiento.

## Beneficio esperado

DRIFT busca **reducir el tiempo de búsqueda y facilitar decisiones de compra más informadas**, permitiendo encontrar la opción que ofrezca la mejor relación entre **precio y experiencia de juego**.

## Tensiones de calidad

DRIFT presenta las siguientes tensiones de calidad que deben ser consideradas en las decisiones arquitectónicas:

### Mantenibilidad vs. Rendimiento

DRIFT debe contar con una arquitectura modular y desacoplada que facilite agregar nuevas plataformas de videojuegos, modificar componentes y mantener el sistema a medida que evoluciona. Sin embargo, un mayor desacoplamiento mediante capas, interfaces y adaptadores puede introducir procesamiento adicional y afectar los tiempos de respuesta. Por lo tanto, se debe buscar un equilibrio entre la facilidad de mantenimiento y el rendimiento del sistema.

### Disponibilidad vs. Actualización de precios

DRIFT depende de información proveniente de diferentes plataformas y fuentes externas. Utilizar mecanismos como almacenamiento temporal o caché puede permitir que el sistema continúe disponible cuando una fuente externa presente fallos, pero puede ocasionar que algunos precios no estén completamente actualizados. Por lo tanto, se debe buscar un equilibrio entre mantener la disponibilidad del sistema y ofrecer información actualizada.
