# ADR-0024: Separar los precios de Colombia de los precios de referencia

- **Estado:** Propuesto (pasa a Aceptado cuando el equipo dé su visto bueno)
- **Fecha:** 2026-11-22
- **Decisores:** Equipo de desarrollo de DRIFT
- **Modifica a:** [ADR-0019](0019-recomendacion-de-compra.md), en el paso 1 de su regla, y [ADR-0021](0021-alertas-de-precio.md), en el precio que revisa la alerta. No edita esos archivos.
- **Complementa a:** [ADR-0016](0016-isthereanydeal-e-historial-de-precios.md), que declaró esta limitación sin resolverla.
- **Respeta:** [ADR-0010](0010-costo-de-reversion-de-las-decisiones-de-datos.md): no cambia el modelo público del juego.

## Contexto

IsThereAnyDeal y CheapShark entregan el precio de Estados Unidos, y DRIFT lo convierte a pesos. Ese valor se comparaba con los precios reales de Colombia y podía ganar «Más barato».

El 12 de octubre de 2026 el equipo comparó DRIFT con las páginas oficiales desde Colombia:

| Tienda | Juego | DRIFT | Página oficial |
|---|---|---|---|
| Steam | Elden Ring | $201.900 | COL$ 201.900 |
| Epic Games | Hades II | $96.175,93 | 70.000 COP |
| GameBillet | Elden Ring | US$52,89 convertido | «Doesn't activate in CO» |
| Fanatical | Elden Ring | $172.789,57 | «This product will not activate in Colombia» |
| GreenManGaming | Elden Ring | $192.383,94 | «Game unavailable where you live» |

El 22 de noviembre de 2026 DRIFT todavía mostraba a GameBillet y Fanatical como las opciones más baratas de Elden Ring.

## Alternativas

1. **Marcar esos precios como referencia y no dejarlos ganar a un precio de Colombia.** Cambio pequeño, sin tocar el contrato.
2. **Quitar las tiendas sin precio de Colombia.** Evita el error, pero pierde información útil y varias tiendas sí venden en Colombia.
3. **Comprobar precio y activación tienda por tienda.** Es lo correcto a largo plazo, pero exige un adaptador por tienda y no todas publican esa información.
4. **Añadir al contrato un campo con el origen de cada precio.** Es más explícito, pero ADR-0010 trata el modelo público como la decisión más cara de revertir y aquí basta con el nombre de la tienda.

## Decisión

Se adopta la **alternativa 1**.

- **Tienen precio de Colombia:** Steam, PlayStation, Xbox y Microsoft Store, porque se consultan directamente para Colombia.
- **Las demás tiendas de PC son referencia:** se muestran después, con el aviso «Precio de EE. UU.; confirma que se venda en Colombia».
- **«Más barato»** solo se asigna a una tienda con precio de Colombia. Si un juego solo tiene precios de referencia, se etiqueta «Referencia EE. UU.».
- **Recomendación:** dentro de cada plataforma, un precio de Colombia gana siempre a uno de referencia. Si solo hay referencia, se recomienda con un aviso.
- **Alertas:** el precio de hoy sigue la misma regla.

La regla vive en `domain/services/platforms.py` (`has_colombia_price`, `purchase_order`) y en `frontend/domain/model/Game.js` (`hasColombiaPrice`, `sortPricesForPurchase`).

## Consecuencias

**Positivas**

- DRIFT deja de presentar como la mejor compra una oferta que puede no servir en Colombia.
- El contrato de la API no cambia.

**Negativas**

- Una tienda de referencia que sí venda más barato en Colombia, como GOG o Epic, no gana «Más barato» aunque sea la mejor opción real.
- PlayStation cobra en dólares: su valor en pesos sigue siendo aproximado.
- Un favorito guardado antes de este cambio puede tener como referencia un precio de otra tienda, así que puede mostrar una subida que no ocurrió.
- El historial de precios sigue incluyendo tiendas de referencia.

## Condiciones para revisar la decisión

- Se integra un adaptador con el precio real de Colombia de otra tienda (GOG o Epic): se añade a la lista.
- Una fuente publica si cada oferta se activa en Colombia.

## Trazabilidad

- **Aspecto:** F5 en [docs/aspectos.md](../aspectos.md).
- **Código:** `backend/app/domain/services/platforms.py`, `recommendation.py`, `backend/app/infrastructure/external/store_current_prices.py`, `frontend/domain/model/Game.js`, `Favorite.js`, `frontend/ui/components/DriftHome.js` y `RecommendationPanel.js`.
- **Pruebas:** `test_a_reference_price_never_beats_a_colombian_price`, `test_a_reference_price_is_used_when_no_colombian_price_exists` y `test_steam_wins_over_reference_prices_of_the_other_pc_stores`.
- **Riesgo:** [arc42 §11.12](../arc42/arc42-11-riesgos-y-deuda-tecnica.md).
