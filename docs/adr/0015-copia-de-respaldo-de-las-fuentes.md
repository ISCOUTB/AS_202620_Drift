# ADR-0015: Responder con la última copia cuando una fuente falla

- **Estado:** Propuesto
- **Fecha:** 2026-11-12
- **Decisores:** Equipo de desarrollo de DRIFT
- **Modifica a:** [ADR-0008](0008-persistencia-ejecucion-y-degradacion-de-fuentes.md), en la degradación de fuentes: antes de marcar una fuente como no disponible se intenta responder con su última copia.
- **Relacionado con:** [ADR-0014](0014-postgresql-como-persistencia.md) (dónde se guardan las copias), [ADR-0009](0009-decision-extraccion-integracion-steam.md) y [ADR-0010](0010-costo-de-reversion-de-las-decisiones-de-datos.md) (modelo público del juego).

## Contexto

La ficha del problema plantea la tensión **disponibilidad contra actualización de precios**. Hasta ahora DRIFT la resolvía a medias:

- Cada fuente tiene una caché en memoria de 60 segundos. Sirve para no repetir llamadas, no para sobrevivir a una caída: cuando vence, se borra.
- Si una fuente falla o tarda más de 3 s, la búsqueda sigue sin ella y la lista en `unavailable_sources`. El usuario ve el juego **sin los precios de esa tienda**.

Para el equipo ese es uno de los peores casos. Además se planea cambiar CheapShark por IsThereAnyDeal, que limita a 1.000 llamadas cada 5 minutos: quedarse sin cuota no puede dejar la búsqueda sin precios.

## Alternativas

1. **Guardar la última respuesta de cada fuente y usarla si la fuente falla**, avisando al usuario de qué fecha es el dato.
2. **Alargar la caché actual** (de 60 s a horas). Es más simple, pero muestra precios viejos aunque la fuente esté sana y sin avisar.
3. **Recargar en segundo plano** los juegos más buscados. Mantiene los datos frescos, pero gasta cuota todo el tiempo y exige un proceso programado que DRIFT no tiene (ADR-0008 mantiene la ejecución síncrona).
4. **No hacer nada.** Se mantiene el aviso de fuente no disponible.

## Decisión

Se adopta la **alternativa 1**, con un envoltorio que sirve para cualquier fuente: `StaleFallbackGameRepository` (`backend/app/infrastructure/persistence/`). Envuelve a Steam, CheapShark y PlayStation sin tocar sus adaptadores.

Según la edad de la copia de una búsqueda:

| Edad de la copia | Qué pasa |
|---|---|
| Menos de **15 minutos** | Se devuelve la copia **sin llamar a la fuente**. Se considera un precio actual y no lleva aviso. |
| Entre 15 minutos y **72 horas** | Se llama a la fuente. Si responde, se renueva la copia. Si falla, se devuelve la copia **con aviso**. |
| Más de 72 horas, o no hay copia | El fallo sigue el camino de siempre: la fuente va a `unavailable_sources`. |

Los dos plazos se configuran con `DRIFT_CACHE_FRESH_SECONDS` y `DRIFT_CACHE_STALE_SECONDS`.

### El aviso al usuario

`GET /games/search` añade a cada juego el campo `cached_sources`: un objeto con la fuente y la fecha en que se obtuvo el dato, por ejemplo `{"CheapShark": "2026-11-12T08:00:00+00:00"}`. La pantalla lo muestra como «Precio guardado hace 2 h».

- Es un campo **nuevo y opcional**: no cambia ni quita ninguno de los existentes, así que respeta la decisión de ADR-0010 de no romper el modelo público del juego. El contrato pasa a la versión 1.6.0.
- Una fuente aparece en `cached_sources` **o** en `unavailable_sources`, nunca en las dos.
- `/metrics` añade `source_backup`: cuántas búsquedas se respondieron con una copia, por fuente.

### Reglas que protegen al usuario

- **Solo se guarda una respuesta completa y correcta de la fuente.** Un error nunca se guarda.
- **Solo se usa la copia ante un fallo de la fuente** (timeout, conexión, 429, 5xx, respuesta inválida). Un error de programación no se esconde detrás de la copia.
- **Una copia sin juegos no se presenta como dato guardado.** Si la fuente falla y lo único guardado es «sin resultados», se avisa que la fuente no respondió.
- **Fuente que excede su plazo de 3 s:** su hilo sigue ocupado y no puede entregar la copia. Por eso `CombinedGameRepository` la pide aparte (`secondary_last_known`).

### Límites del respaldo guardado

Para que búsquedas inventadas no llenen la memoria ni el disco:

- En memoria: 500 búsquedas como máximo; se descarta la que lleva más tiempo sin usarse.
- En PostgreSQL: 5.000 filas como máximo y nada de más de 72 horas; se limpia cada 10 minutos. No se guarda una respuesta de más de 256 KB.

## Consecuencias

**A favor**

- Una fuente caída o sin cuota ya no deja al usuario sin los precios de esa tienda, si alguien buscó ese juego en las últimas 72 horas.
- Se llama menos a las fuentes: una búsqueda repetida en 15 minutos no gasta cuota.
- Sirve igual para la fuente de Xbox y para IsThereAnyDeal cuando se integren.

**En contra**

- **Un precio puede tener hasta 15 minutos sin aviso** y hasta 72 horas con aviso. Antes el máximo era 60 segundos. Es el costo aceptado a cambio de disponibilidad.
- **Un juego que nadie ha buscado no tiene copia.** Si la fuente cae, ese juego sigue mostrando «fuente no disponible».
- El catálogo de respaldo de Steam (`InMemoryGameRepository`) pasa a usarse solo cuando tampoco hay copia de esa búsqueda.
- Cada búsqueda hace una lectura por fuente en el almacén de copias.

## Lo que se verificó y lo que no

- **Verificado:** 22 pruebas en `backend/tests/test_copia_de_respaldo.py` (ventanas de 15 minutos y 72 horas, fallos por timeout, conexión, 429 y 5xx, plazo excedido, copias independientes, métricas y el endpoint).
- **Verificado de punta a punta en un equipo de desarrollo:** una búsqueda real de «portal 2», luego un reinicio de la API con las tres fuentes forzadas a fallar. La respuesta trajo los precios de Steam y PlayStation desde PostgreSQL, con su fecha en `cached_sources`.
- **No verificado:** el escenario E6 (degradación bajo carga) con este cambio. Hay que repetir la corrida de `scripts/e6_corrida.py`: ahora una fuente caída debería responder con copia en lugar de degradar.
- **No verificado:** el control de cuota de IsThereAnyDeal (frenar antes de las 1.000 llamadas). Se hará junto con ese adaptador; este ADR solo cubre qué pasa cuando la fuente ya respondió 429.

## Cuándo revisar esta decisión

- Los usuarios reportan precios desactualizados: bajar los 15 minutos.
- Las métricas de `source_backup` muestran que casi nunca hay copia cuando una fuente cae: evaluar la recarga en segundo plano de los juegos más buscados (alternativa 3).
