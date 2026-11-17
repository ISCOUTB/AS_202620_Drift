# ADR-0020: Juegos favoritos de quien inicia sesión

- **Estado:** Propuesto
- **Fecha:** 2026-11-13
- **Decisores:** Equipo de desarrollo de DRIFT
- **Relacionado con:** [ADR-0014](0014-postgresql-como-persistencia.md) (PostgreSQL), [ADR-0017](0017-inicio-de-sesion-con-google-y-dispositivos.md) (cuentas y sesión)

## Contexto

Quien inicia sesión solo podía registrar dispositivos. Para seguir el precio de un juego tenía que buscarlo de nuevo cada vez y recordar cuánto costaba antes.

## Alternativas

1. **Guardar el juego con el precio que tenía al guardarlo**, y comparar contra ese precio cuando la persona lo vuelve a buscar.
2. **Revisar los precios de los favoritos en segundo plano** y avisar por correo o al entrar. Es lo más útil, pero necesita un proceso programado, gasta cuota de las fuentes sin que nadie esté mirando y, para el correo, un servicio de envío.
3. **Guardar los favoritos en el navegador.** No necesita sesión, pero se pierden al cambiar de equipo, que es justo lo que resuelve la cuenta.

## Decisión

Se adopta la **alternativa 1**. La alternativa 2 queda como paso siguiente (alertas de precio) y se apoyará en esta tabla.

- Tabla `user_favorite` (migración 4): usuario, identificador del juego, nombre, imagen, mejor precio y tienda al guardar, y fecha. Borrar la cuenta borra sus favoritos.
- Rutas, todas con sesión: `GET /favorites`, `PUT /favorites/{game_id}` y `DELETE /favorites/{game_id}`. Las dos que cambian datos exigen venir de un origen permitido, igual que los dispositivos.
- Guardar un juego que ya estaba actualiza su precio de referencia.
- Máximo 100 favoritos por cuenta.
- En la página: botón «Guardar en favoritos» en el detalle del juego, pestaña «Favoritos» y, al abrir un juego guardado, el aviso «Bajó (o subió) tanto desde que lo guardaste».
- **Los favoritos no consultan ninguna fuente.** «Ver precios de hoy» lanza una búsqueda normal con el nombre del juego.

## Consecuencias

**A favor**

- La lista sigue a la persona en cualquier navegador.
- No suma llamadas a las tiendas ni a la cuota de IsThereAnyDeal.
- Deja lista la base para las alertas de precio.

**En contra**

- **No avisa solo.** La persona tiene que entrar y pulsar «Ver precios de hoy» en cada juego.
- **El precio de referencia lo envía la página**, no lo recalcula el servidor. Solo afecta a la lista de quien lo envía; se validan el tamaño, el rango y que la imagen sea una dirección `https`.
- La lista muestra el precio de cuando se guardó, no el de hoy.
- El juego se vuelve a encontrar **por nombre**. Si la búsqueda devuelve otra edición primero, el aviso de cambio de precio solo aparece al abrir la que tiene el mismo identificador.
- Un dato personal más: qué juegos le interesan a cada persona (ver [privacidad](../seguridad/privacidad.md), sección 8).
- Si la base de datos no responde, los favoritos responden «no disponible», como los dispositivos. La búsqueda no depende de ellos.

## Lo que se verificó y lo que no

- **Verificado con pruebas** (`backend/tests/test_favoritos.py`), en memoria y en PostgreSQL: cada quien ve solo lo suyo, guardar de nuevo reemplaza, borrar la cuenta borra los favoritos, el límite, los datos inválidos, el rechazo sin sesión o desde otro origen y la respuesta cuando el almacén falla.
- **Verificado en un equipo de desarrollo (13 de noviembre de 2026)**, con un proveedor de identidad simulado en lugar de Google: guardar Portal 2 desde su detalle, verlo en la pestaña, el aviso «Bajó $5.501 desde que lo guardaste» y quitarlo.
- **No verificado:** con una sesión real de Google ni en el laboratorio.

## Cuándo revisar esta decisión

- Se construyen las alertas de precio: ahí hay que decidir cada cuánto se revisan los favoritos y cuánta cuota se les reserva.

## Actualización del 13 de noviembre de 2026

[ADR-0021](0021-alertas-de-precio.md) agrega las alertas de precio. Desde entonces:

- Los favoritos sí consultan fuentes: al entrar con sesión, la API revisa el precio de hoy en las tiendas de PC.
- La lista muestra el precio de hoy y avisa si un favorito llegó a su precio objetivo o bajó 5 % o más.
- El botón «Ver precios de hoy» pasó a llamarse «Ver todas las tiendas»: sigue lanzando una búsqueda normal, que incluye las consolas.
