# ADR-0016: Usar IsThereAnyDeal para las tiendas de PC y el historial de precios

- **Estado:** Propuesto
- **Fecha:** 2026-11-12
- **Decisores:** Equipo de desarrollo de DRIFT
- **Relacionado con:** [ADR-0004](0004-estrategia-de-integracion.md) (cada fuente es un adaptador), [ADR-0014](0014-postgresql-como-persistencia.md) y [ADR-0015](0015-copia-de-respaldo-de-las-fuentes.md) (copia de respaldo y cuota)

## Contexto

La ficha del problema pide **consultar el historial de precios**. DRIFT no lo tenía: no guarda precios y ninguna de sus fuentes lo entregaba.

Las tiendas de PC distintas de Steam llegaban por CheapShark, que cubre 13 tiendas, no pide llave y no ofrece un historial utilizable.

## Alternativas

1. **IsThereAnyDeal para precios e historial.** Cubre las 13 tiendas de CheapShark y unas 22 más (comprobado el 12 de noviembre de 2026 con la lista de tiendas de cada API para Colombia). Entrega el registro de cambios de precio. Costo: pide una llave y limita a 1.000 llamadas cada 5 minutos.
2. **Mantener CheapShark y usar IsThereAnyDeal solo para el historial.** Menos cambio, pero dos fuentes de PC que mantener y dos listas de tiendas distintas en la misma pantalla.
3. **Construir un historial propio** guardando en PostgreSQL cada precio que DRIFT observa. No depende de nadie, pero empieza vacío, solo cubre los juegos que alguien buscó y tarda meses en ser útil.
4. **No ofrecer historial.** Deja sin cumplir un punto de la ficha.

## Decisión

Se adopta la **alternativa 1**, con CheapShark como respaldo cuando no hay llave.

- **Con `DRIFT_ITAD_API_KEY`:** las tiendas de PC salen de IsThereAnyDeal (`ItadGameRepository`) y se habilita `GET /games/{game_id}/price-history`.
- **Sin la llave** (pruebas, CI, o un entorno donde no se configuró): se usa CheapShark, como antes, y el historial responde `available: false` con `reason: not_configured`. DRIFT no deja de funcionar por una llave faltante.
- **El historial no se guarda en DRIFT.** Se pide a IsThereAnyDeal cuando alguien abre un juego y se conserva una hora en memoria.
- El dominio no conoce a IsThereAnyDeal: define el puerto `PriceHistoryRepository` y calcula la línea del mejor precio en `domain/services/price_timeline.py`.

### Cómo se cuida la cuota

- Una búsqueda cuesta **2 llamadas** (buscar por nombre y pedir los precios de todos los juegos a la vez). Un historial cuesta hasta 3, y una hora de caché evita repetirlas.
- `ItadClient` lleva la cuenta de las llamadas y **se detiene en 900 por cada 5 minutos**. La llamada siguiente falla sin salir a la red, como «sin cuota».
- Si la fuente responde 429, no se la vuelve a llamar durante 60 segundos.
- En los dos casos la búsqueda responde con su copia de respaldo (ADR-0015). El uso de la cuota se ve en `/metrics` (`itad_quota`).
- La llave viaja en una cabecera, nunca en la URL, y no se registra.

### Qué muestra el historial

- La línea del **mejor precio entre las tiendas de PC que hoy venden el juego**, en los últimos 12 meses, terminada en el precio de hoy.
- El **precio más bajo registrado** en ese periodo por cualquier tienda.
- El **mayor descuento de Steam** en ese periodo, solo como porcentaje.

## Consecuencias

**A favor**

- Se cumple el punto del historial de la ficha.
- Más tiendas de PC por búsqueda, con descuento y enlace de compra.

**En contra**

- **Los precios de IsThereAnyDeal para Colombia vienen en dólares**, igual que los de CheapShark: son precios de Estados Unidos convertidos a pesos. La limitación que ya existía no se resuelve.
- **El historial es aproximado en pesos:** los importes antiguos se convierten con la tasa de hoy, no con la de su fecha.
- **Steam no entra en la línea del historial**, porque su precio en dólares no es el que paga un usuario en Colombia. Un juego que solo se vende en Steam no tiene línea, solo el dato de su mayor descuento.
- El registro de cambios no dice cuándo una tienda dejó de vender un juego. Por eso la línea usa solo las tiendas que lo venden hoy: una oferta antigua de una tienda que ya no lo vende cuenta para el «más bajo registrado», pero no aparece en la línea.
- Un secreto más que administrar, y una cuota compartida por todos los usuarios de DRIFT.
- Los juegos de IsThereAnyDeal se unen con los de Steam **por nombre**, no por identificador. Un nombre escrito distinto en las dos fuentes produce dos tarjetas del mismo juego.

## Lo que se verificó y lo que no

- **Verificado con la llave real (12 de noviembre de 2026):** búsquedas de «elden ring» y «hollow knight» con 9 a 12 tiendas de PC por juego; historial de Elden Ring con 38 puntos, cuyo precio final coincide con el mejor precio vigente de la búsqueda.
- **Verificado con pruebas** (`backend/tests/test_isthereanydeal.py`): corte de cuota, pausa tras un 429, respuesta desde la copia de respaldo sin cuota, respuestas con forma inesperada y el historial servido desde su última copia cuando la fuente falla.
- **No verificado:** el comportamiento real al llegar a las 1.000 llamadas. El corte propio en 900 se probó con un reloj simulado, no contra la fuente.
- **No verificado:** el efecto en E1 (p95 ≤ 3 s). La búsqueda con las cuatro fuentes tardó entre 1,8 y 2,2 s en un equipo de desarrollo, más que antes (1,4 s con CheapShark).

## Cuándo revisar esta decisión

- IsThereAnyDeal cambia sus condiciones o su límite.
- La medición de E1 no se cumple por las dos llamadas encadenadas.
- Se quiere un historial exacto en pesos o que incluya consolas: ahí vuelve la alternativa 3, apoyada en PostgreSQL.

## Actualización del 12 de noviembre de 2026: Steam entra en la línea, en pesos

La decisión original dejaba a Steam fuera de la línea del historial porque IsThereAnyDeal solo conoce su precio en dólares. Eso dejaba sin línea a todo juego que solo se vende en Steam, que son muchos.

**Cambio:** el historial ahora incluye a Steam con precios de Colombia.

- La API le pide a Steam el precio normal y el precio de hoy del juego en pesos (una llamada, sin llave).
- El precio de Steam en cada fecha se reconstruye como **precio normal de hoy menos el descuento que tuvo ese día**. Steam aplica el mismo porcentaje de descuento en todas las regiones.
- Para un juego que no vino de Steam, se le pregunta a IsThereAnyDeal cuál es su identificador en Steam.
- Si Steam no responde, el historial se entrega sin su serie, como antes.

**Supuesto que hay que conocer:** se asume que el precio normal del juego en Colombia no cambió en los 12 meses. Si Steam subió o bajó el precio base en ese periodo, los valores antiguos de su serie quedan desviados.

**Verificado con datos reales:** Portal 2 pasó de 0 a 9 puntos en su historial, con su mínimo en $4.900 (80 % de descuento, 1 de octubre de 2026); Hollow Knight muestra a Steam como el mejor precio de hoy.

**Lo que sigue sin historial:** los juegos que solo existen en una tienda de consola y los que IsThereAnyDeal no conoce.

**Costo:** un historial pasa de 3 a 4 llamadas externas (5 si el juego no vino de Steam). Sigue con una hora de caché y un plazo propio de 6 segundos.
