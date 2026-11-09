# ADR-0013: Limitar con un plazo total cada búsqueda en Steam

- **Estado:** Propuesto
- **Fecha:** 2026-11-08
- **Decisores:** Equipo de desarrollo de DRIFT
- **Modifica a:** [ADR-0009](0009-decision-extraccion-integracion-steam.md), solo en lo que dice sobre el tiempo de una búsqueda. Su decisión de no extraer la integración, los 2 intentos y el aplazamiento del circuit breaker siguen vigentes.
- **Corrige:** una cita de [ADR-0010](0010-costo-de-reversion-de-las-decisiones-de-datos.md) (ver «Correcciones a ADR aceptados»). Los ADR aceptados no se editan: las correcciones quedan aquí.
- **Relacionado con:** [arc42 §8.14](../arc42/arc42_8_conceptos_transversales.md), [arc42 §11.8](../arc42/arc42-11-riesgos-y-deuda-tecnica.md) y [evidencia S12](../evidencias/s12-steam-degradado.md)

## Contexto

ADR-0009 fijó un timeout de 3 s por fase y hasta 2 intentos, sin tope para la operación completa. Reconoció que, en el peor caso, cada fase podía tardar cerca de 6,25 s, por encima de los 5 s que piden los escenarios E5 y E6.

La semana 12 agregó un plazo total (`TimeBudget`, commit `02b9437`, 20 de octubre de 2026) sin registrar la decisión en un ADR. Este documento la registra después de implementada.

Al escribirlo se encontró una diferencia entre el código y los documentos:

| Dónde (antes de este ADR) | Valor del plazo total de Steam |
|---|---|
| `backend/app/infrastructure/external/steam/steam_game_repository.py` (`DEFAULT_TOTAL_DEADLINE_SECONDS`), desde el commit que lo introdujo | **5,0 s** |
| `deploy/.env.example`, arc42 §8.13 a §8.15 y [evidencia S12](../evidencias/s12-steam-degradado.md) | 4 s |

La medición de S12 corrió con 4 s pasados de forma explícita: con Steam sin responder, el p95 bajó de 6,24 s a 4,01 s. **El valor de 5 s no se ha medido**, y la corrida de S12 fue en un sandbox con respuestas simuladas.

No se pudo comprobar si el despliegue define `DRIFT_STEAM_TOTAL_DEADLINE_SECONDS`, porque las variables de Dokploy y Azure no están en el repositorio.

## Alternativas

1. **Plazo total por operación, compartido entre fases y reintentos.** Da un tope claro sin estado nuevo. Costo: con Steam lento, más búsquedas terminan usando el respaldo.
2. **Bajar el timeout por fase o quitar el reintento.** Es más simple, pero el total sigue dependiendo de cuántas fases haya y se pierde la recuperación ante fallos breves.
3. **Adelantar el circuit breaker.** Evita repetir llamadas a una fuente caída, pero no limita una búsqueda lenta y añade el estado que ADR-0009 decidió aplazar.
4. **No hacer nada.** La búsqueda sigue pudiendo incumplir los 5 s de E5 y E6.

## Decisión

Se adopta la **alternativa 1**.

- `TimeBudget` (`backend/app/infrastructure/external/resilient_http.py`) comparte un plazo entre todas las fases y reintentos de una búsqueda.
- El valor se configura con `DRIFT_STEAM_TOTAL_DEADLINE_SECONDS`, y `off` lo desactiva.
- **El valor por defecto pasa a 4,0 s** en `DEFAULT_TOTAL_DEADLINE_SECONDS`, y así coincide con `deploy/.env.example`, arc42 §8.13 a §8.15 y la evidencia S12.
- Agotado el plazo, la búsqueda continúa como fallo de la fuente: usa el catálogo de respaldo y avisa en `unavailable_sources`.

**Por qué 4 s y no 5 s:** 4 s es el único de los dos valores que se ha medido, y deja margen para el umbral de 5 s de E5 y E6, que también incluye el servidor y la red. Mantener 5 s obligaba a corregir la documentación y a medir otra vez, con poco o ningún margen.

## Correcciones a ADR aceptados

| ADR | Qué dice | Corrección |
|---|---|---|
| [ADR-0009](0009-decision-extraccion-integracion-steam.md), «Consecuencias» | Cada fase puede tardar cerca de 6,25 s | Ya no aplica a la operación completa: el plazo total de este ADR la limita. |
| [ADR-0009](0009-decision-extraccion-integracion-steam.md), «Estado de la validación» | Texto reescrito después de aceptar el ADR, en los commits `02b9437` y `88cfab3` (PR #31) | El texto aceptado es el del commit `e970355`. La reescritura no cambió la decisión y no se revierte, para no sumar otra edición. |
| [ADR-0010](0010-costo-de-reversion-de-las-decisiones-de-datos.md), «Registro de IA: `docs/ia.md`, Registro 43» | Cita el Registro 43 como registro de ese ADR | Es incorrecta: el Registro 43 es de análisis de dependencias (S13). [`ia.md`](../ia.md) no tiene ningún registro del trabajo de S12. Debe agregarlo quien usó la IA esa semana. |

## Consecuencias

**Positivas**

- Una búsqueda ya no acumula timeouts y reintentos sin tope.
- El código y la documentación vuelven a coincidir.

**Negativas y riesgos**

- Los 4 s se midieron en un sandbox con respuestas simuladas, no en el despliegue. La [medición S14 en el despliegue](../evidencias/s14-e1-medicion.md) se hizo con el código anterior, así que falta medir este valor allí.
- Con Steam lento, más búsquedas usan el respaldo: en S12, con 4 s, fueron el 100 % en el escenario lento.
- Si el despliegue define `DRIFT_STEAM_TOTAL_DEADLINE_SECONDS`, ese valor manda sobre el del código. Hay que revisarlo al desplegar.

## Trazabilidad

- **Aspectos:** E5 y E6 de [`aspectos.md`](../aspectos.md).
- **C4:** adaptador de Steam dentro de Backend / API ([nivel 3](../c4/componentes.md)).
- **Implementación:** commit `02b9437`, integrado con el PR #31. Valor de 4 s en `backend/app/infrastructure/external/steam/steam_game_repository.py`.
- **Pruebas:** `backend/tests/test_s12_plazo_total.py`.
- **Seguimiento:** S14-D1 en [arc42 §11.10](../arc42/arc42-11-riesgos-y-deuda-tecnica.md).

## Cambio estructural

Ninguno. El plazo vive dentro del adaptador existente y no cambia los contenedores, los puertos ni el contrato de la API.
