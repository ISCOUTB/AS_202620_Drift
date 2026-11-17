# ADR-0021: Alertas de precio de los favoritos, revisadas al entrar

- **Estado:** Propuesto
- **Fecha:** 2026-11-13
- **Decisores:** Equipo de desarrollo de DRIFT
- **Relacionado con:** [ADR-0015](0015-copia-de-respaldo-de-las-fuentes.md) (disponibilidad primero), [ADR-0016](0016-isthereanydeal-e-historial-de-precios.md) (cuota de IsThereAnyDeal), [ADR-0020](0020-juegos-favoritos.md) (favoritos; esta decisión la modifica)

## Contexto

Con [ADR-0020](0020-juegos-favoritos.md) una persona puede guardar juegos, pero para saber si bajaron tiene que buscarlos uno por uno. Lo que quiere es que DRIFT le diga cuándo un favorito llegó al precio que espera.

## Alternativas

1. **Revisar al entrar.** Cuando la persona abre DRIFT con sesión, la API consulta el precio de hoy de sus favoritos y la página muestra un aviso. No hay procesos en segundo plano ni correo.
2. **Revisar en segundo plano y enviar un correo.** Avisa aunque la persona no entre, pero necesita un proceso programado que corra en el laboratorio, un servicio de correo con sus credenciales y su costo, consentimiento para escribirle y gasta cuota de las fuentes aunque nadie mire.
3. **Revisar en segundo plano y mostrar el aviso al entrar.** Gasta la cuota del punto 2 sin la ventaja del correo.

## Decisión

Se adopta la **alternativa 1**.

### Cuándo avisa un favorito

- **Con precio objetivo** («Avísame si baja de»): cuando el mejor precio de hoy es igual o menor que ese objetivo.
- **Sin precio objetivo:** cuando el mejor precio de hoy está **al menos 5 % por debajo** del que tenía al guardarlo. El margen evita avisos falsos: las tiendas de PC distintas de Steam vienen en dólares y cambian unos pesos cada día con la tasa de cambio.
- La regla vive en `domain/services/price_alerts.py`.

### De dónde sale el precio de hoy

`infrastructure/external/store_current_prices.py`, solo **tiendas de PC**:

- **Steam** en pesos de Colombia: una llamada por juego, sin llave, varias en paralelo.
- **Las demás tiendas de PC** por IsThereAnyDeal: **dos llamadas para todos los favoritos juntos** (traducir los identificadores de Steam y pedir los precios). Sin la llave de IsThereAnyDeal solo se consulta Steam.
- Cada precio se guarda **una hora** en memoria. Volver a entrar en esa hora no llama a ninguna fuente.
- Solo se revisan los **30 favoritos más recientes** de cada persona.

### Disponibilidad

Las alertas son un extra: **nunca rompen la página**.

- Si IsThereAnyDeal falla o se queda sin cuota, se responde solo con Steam.
- Si todas las fuentes fallan, los favoritos se muestran sin precio de hoy y sin alerta. Ese fallo no se recuerda: la siguiente visita vuelve a intentar.
- Si la base de datos falla, la ruta responde «no disponible», como los dispositivos.

### Rutas

- `GET /favorites/alerts`: precio de hoy y alerta de cada favorito. Entra en el límite de tasa por cliente, porque llama a fuentes externas.
- `PUT /favorites/{game_id}/target`: pone o quita (`null`) el precio objetivo. Exige sesión y un origen permitido.
- La tabla `user_favorite` gana la columna `target_price` (migración 5). Guardar de nuevo un favorito conserva su objetivo.

## Consecuencias

**A favor**

- La persona ve al entrar qué favoritos bajaron, sin buscarlos uno por uno.
- No hay servicios nuevos, secretos nuevos ni procesos programados en el laboratorio.
- La cuota de IsThereAnyDeal crece poco: 2 llamadas por persona como máximo una vez por hora.

**En contra**

- **No avisa si la persona no entra.** Una oferta de un fin de semana puede pasar sin que se entere.
- **Los juegos solo de consola no tienen alerta.** PlayStation y la tienda de Xbox no se consultan por identificador; la tarjeta dice «sin consultar».
- **El precio guardado puede ser de una consola.** Si al guardar el más barato era PlayStation, la comparación de hoy es contra tiendas de PC: puede no avisar una baja que sí ocurrió en la consola.
- Steam se consulta juego por juego. Con 30 favoritos que vienen de Steam son 30 llamadas en paralelo la primera vez de cada hora; en un equipo de desarrollo, la primera revisión de 4 favoritos tardó 2,8 s y la repetida 4 ms.
- La caché vive en memoria: se pierde al reiniciar la API y no se comparte si un día hay varias réplicas.

## Lo que se verificó y lo que no

- **Verificado con pruebas** (`backend/tests/test_alertas_de_precio.py`): la regla, la conservación del objetivo, el tope de 30, la respuesta cuando cada fuente falla, la caché de una hora, las dos llamadas juntas a IsThereAnyDeal, las rutas, el origen y el límite de tasa. La migración 5 se probó contra PostgreSQL.
- **Verificado con datos reales (13 de noviembre de 2026)**, con un proveedor de identidad simulado: Portal 2 guardado a $30.000 avisó «bajó $5.501» (hoy $24.499 en Steam); Elden Ring con objetivo avisó (hoy $173.279 en GameBillet); Hollow Knight, que subió, no avisó; un juego solo de Xbox quedó «sin consultar». La página mostró el aviso, el número en la pestaña y el formulario del precio objetivo.
- **No verificado:** con una sesión real de Google, en el laboratorio, ni con muchas personas a la vez.

## Cuándo revisar esta decisión

- Las personas piden avisos sin entrar: ahí vuelve la alternativa 2, con un proceso programado y un servicio de correo.
- PlayStation o Xbox ofrecen consulta de precio por identificador.
- La API pasa a tener varias réplicas: la caché de una hora debería ir a PostgreSQL.
