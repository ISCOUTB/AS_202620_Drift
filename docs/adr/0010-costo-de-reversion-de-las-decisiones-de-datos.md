# ADR-0010: Costo de reversión de las decisiones de datos

- **Estado:** Aprobado
- **Fecha:** 2026-10-20
- **Decisores:** Equipo de desarrollo de DRIFT
- **Complementa a:** [ADR-0008](0008-persistencia-ejecucion-y-degradacion-de-fuentes.md), Decisión 1 (persistencia y modelo de ejecución). **No lo sustituye ni lo modifica:** la decisión de mantener los datos en memoria sigue vigente; este ADR añade lo que ADR-0008 no analiza, que es cuánto cuesta revertirla y cómo se compara con otras decisiones.
- **Relacionado con:** [ADR-0009](0009-decision-extraccion-integracion-steam.md) y [arc42 §8.13](../arc42/arc42_8_conceptos_transversales.md)

## Contexto

ADR-0008 comparó almacenamiento en memoria con MySQL (síncrono y asíncrono) y eligió la memoria. Lo verificó contra el repositorio y la justificó por ausencia de datos propios y por el presupuesto de 512 MB. Falta una segunda pregunta, la que hace una decisión de datos **cara de deshacer**: ¿cuánto costaría volver atrás, y es ésa la decisión de datos más difícil de revertir que tiene DRIFT?

Estado real verificado en el código (20 de octubre de 2026):

- **No existe persistencia duradera.** No hay adaptador, dependencia ni servicio de MySQL (`backend/requirements.txt` no incluye un controlador; `deploy/compose.lab.yaml` define solo `api` y `web`, sin volúmenes). **MySQL no está implementado.**
- **Estado en memoria del proceso:** `InMemoryPlayStationCatalog` (único dato que el sistema escribe, y se reconstruye con `POST /games/sync/playstation`), `InMemoryGameRepository` y `InMemoryGameRequirementsRepository` (datos curados en el código), `SingleFlightCache` (Steam, CheapShark, requisitos) y la tasa de cambio. Los detalles de consistencia están en [arc42 §8.13](../arc42/arc42_8_conceptos_transversales.md).
- **Hay un puerto para el catálogo:** `GameCatalogRepository` (`backend/app/domain/ports/`). El caso de uso `SyncPlayStationCatalog` depende del puerto, no de la clase en memoria.
- **No hay datos propios del usuario en el servidor.** El único dato de usuario que se guarda es el equipo del usuario, en `localStorage` de su navegador (`drift.pcProfile`); si el formato guardado no es válido, el frontend lo descarta y vuelve a pedir el equipo (`BrowserPcProfileRepository`).
- **El modelo público del juego sí está acoplado a varios lugares:** `Game` (`id` como texto, `prices` y `links` por nombre de tienda, `unavailable_sources`) lo producen los tres adaptadores de fuentes, lo combinan `CombinedGameRepository` y `main.py`, lo consume el frontend (`Game.js`, `DriftHome.js`) y está fijado en `docs/api/drift/openapi.yaml` (versión 1.4.0, rutas sin prefijo de versión) y en las pruebas de contrato con Schemathesis. La identidad de compatibilidad es el identificador de Steam (`GameRequirements.game_id` es entero) y un juego de PlayStation solo conserva una identidad propia mediante `PLAYSTATION_COMPATIBILITY_IDS` en `main.py`, que hoy tiene **una sola entrada**. `CombinedGameRepository` une por nombre normalizado los precios de PlayStation con un resultado existente; un juego de PlayStation sin coincidencia conserva su identificador (no numérico) y `GET /games/search` lo omite si no está en ese mapa.

## Problema

Identificar cuál es la decisión de datos más costosa de revertir, compararla con las demás con criterios explícitos y fijar cuándo hay que volver a decidir, sin inventar costos observados: el repositorio no registra horas reales, así que todo esfuerzo es una estimación con supuestos declarados.

## Alternativas para la decisión de persistencia

1. **Mantener almacenamiento en memoria** (vigente, ADR-0008 Alternativa 1). Sin dependencias nuevas; se pierde el catálogo de PlayStation al reiniciar y no hay datos compartidos entre instancias.
2. **Migrar a persistencia duradera (MySQL u otro motor).** Alternativa válida del proyecto: la propuso ADR-0004. Añade un servicio, credenciales, migraciones y pruebas con base de datos; resuelve la pérdida al reiniciar y el catálogo compartido entre instancias.
3. **Estrategia híbrida: persistencia duradera más caché en memoria.** Solo se justifica cuando haya datos duraderos y lecturas frecuentes sobre ellos. Hoy no hay ninguno de los dos, así que se descarta por ahora; las cachés actuales ya cumplen su función sobre datos externos.

## Comparación del costo de reversión

«Revertir» significa deshacer la decisión tal como está tomada hoy. Los conteos de archivos son observados en el repositorio; las horas son **estimaciones** (supuestos al final de esta sección).

| Criterio | A. Cambiar un adaptador (p. ej. CheapShark) | B. Memoria → persistencia duradera (esta decisión, hoy) | C. Extraer la integración con Steam (ADR-0009) | D. Cambiar el modelo público de datos (identidad y contrato del juego) | E. Revertir persistencia **después** de que existan datos propios del usuario (escenario futuro) |
|---|---|---|---|---|---|
| Componentes y archivos | 1 adaptador, `main.py` y 5 archivos de prueba | 1 adaptador nuevo detrás de `GameCatalogRepository`, `main.py`, configuración, `compose` y despliegue; 3 clases en memoria afectadas (`InMemoryPlayStationCatalog` en lo que escribe; las otras dos son datos curados) | 2 adaptadores, `resilient_http`, caché y `main.py`, más un servicio nuevo y su contrato de red | 11 archivos del backend, 2 del frontend, `openapi.yaml`, el contrato de la API y las pruebas de contrato | Todo lo de B más cada modelo y consulta que dependa de los datos |
| Modelo de datos | Ninguno | Un esquema nuevo (una tabla de catálogo) y una herramienta de migraciones que hoy no existe | Ninguno propio; aparece un contrato entre servicios | El modelo del dominio y su serialización | Esquemas de varias entidades con claves y restricciones |
| Migraciones y recuperación | No aplica | **Ninguna hoy:** el único dato escrito se reconstruye con el `POST` de sincronización | No aplica | No hay datos persistidos del servidor que migrar | Migración hacia adelante y hacia atrás, copia de seguridad, restauración |
| Contratos y frontend | Sin cambios | Sin cambios: el contrato no cambia | Sin cambios visibles, nuevo contrato interno | **Cambio incompatible**: los clientes deben actualizarse a la vez; hay que servir ambos formatos de identificador durante la transición | Posible según el cambio |
| Riesgo de pérdida o inconsistencia | Bajo | Bajo hoy; el catálogo se puede recargar | Medio: aparecen fallos de red nuevos que hoy no existen | Medio: un identificador mal mapeado hace desaparecer juegos del resultado (ya ocurre con PlayStation sin coincidencia ni mapa) | **Alto**: datos que el usuario escribió y la fuente externa no puede reponer |
| Costo de pruebas y despliegue | Pruebas unitarias | Base de datos en CI y en el despliegue; credenciales | Segundo despliegue, observabilidad y pruebas entre servicios | Pruebas de contrato, despliegue coordinado de frontend y backend | Pruebas de migración, ensayos de reversión, ventanas de despliegue |
| Esfuerzo estimado de revertir | 6 a 10 h | 24 a 40 h | 40 a 80 h para extraer; 16 a 24 h para volver a integrarla | 30 a 50 h | 60 a 120 h o más |
| Compatibilidad durante la transición | Total | Posible con una opción de configuración que elija el adaptador en memoria o el duradero | Posible con una opción que elija el adaptador local o el remoto | Solo sirviendo ambos formatos a la vez | Posible, con escritura doble y mayor riesgo |

**Supuestos de las estimaciones** (no son costos observados): una persona del equipo con conocimiento del código; incluye pruebas y actualización de documentos; excluye esperas de revisión y de despliegue; cada fila de «revertir» es el esfuerzo para deshacer lo que existe hoy, no para construirlo; el escenario E supone una entidad persistida con datos reales y es hipotético, porque hoy no hay ninguna. Se revisan con horas reales cuando existan.

### Qué muestra la comparación

1. **La decisión de datos más costosa de revertir que existe hoy es D, el modelo público de datos y la identidad del juego, no B.** Atraviesa backend, frontend, contrato y pruebas, obliga a una transición con dos formatos y su error silencioso es que algunos juegos desaparecen del resultado. Esa es la conclusión que hay que defender con el código, no con el rótulo del ADR.
2. **B, mantener la memoria, es barata de deshacer hoy, y por una razón concreta:** el único dato que el sistema escribe es derivado (se reconstruye desde PlayStation con el `POST`) y está detrás de un puerto. No hay nada que migrar ni contrato que cambiar. ADR-0008 acierta al elegirla, pero lo justificó por simplicidad y no por esta propiedad, que es la que realmente sostiene la decisión.
3. **B pasa a ser la decisión más costosa de revertir en el momento en que exista el primer dato propio del usuario en el servidor** (columna E): favoritos, alertas de precio o cualquier historial. A partir de ahí la reversión implica migraciones en dos sentidos, copia de seguridad y riesgo de pérdida de datos que ninguna fuente puede reponer. Su esfuerzo estimado supera al de todas las demás.
4. **C, extraer Steam, es cara de deshacer por razones operativas** (otro despliegue, otros fallos de red), pero queda contenida detrás del puerto `GameRepository`. Esa es la razón por la que ADR-0009 la pospone sin cerrarla.
5. **A, cambiar un adaptador, es la reversión más barata.** Por eso el diseño hexagonal es una buena base para las fuentes, y no lo es para blindar el modelo público.

## Decisión

1. **Se mantiene el almacenamiento en memoria** (ADR-0008, Decisión 1). Este ADR no la cambia; añade el razonamiento de reversión.
2. **Punto de no retorno.** Antes de construir cualquier función que **escriba datos propios del usuario en el servidor**, el equipo decide la persistencia y el modelo de datos **juntos**, con un ADR nuevo, porque desde ese momento el costo de revertir deja de ser el de la fila B y pasa al de la fila E.
3. **El modelo público del juego se trata como una decisión cara.** Un cambio en `Game` o en su contrato (formato del identificador, claves de `prices` y `links`, `unavailable_sources`) se evalúa con la fila D: requiere un ADR, la actualización de `openapi.yaml`, las pruebas de contrato y una transición compatible.
4. **Se mantiene el puerto `GameCatalogRepository`** como único punto de acople con el almacenamiento del catálogo, que es lo que hace barata la fila B.

## Consecuencias

**Positivas**

- Deja explícito por qué la memoria es hoy una decisión reversible y por qué dejará de serlo.
- Evita un falso supuesto en el diseño: la decisión de datos más costosa hoy es el contrato y la identidad, no la base de datos.
- Fija un criterio verificable (el primer dato propio del usuario) para volver a decidir.
- No añade infraestructura ni cambia código.

**Negativas y riesgos**

- Las horas son estimaciones sin base observada y pueden estar lejos de la realidad.
- La comparación incluye un escenario hipotético (columna E) que no se puede medir hoy.
- Mantener la memoria conserva sus límites ya aceptados: el catálogo de PlayStation queda vacío tras un reinicio y no hay datos compartidos entre instancias ([arc42 §8.13](../arc42/arc42_8_conceptos_transversales.md)).
- Queda sin resolver, y fuera del alcance de este ADR, que la identidad de compatibilidad anclada a Steam y el mapa de una sola entrada dejan fuera de `GET /games/search` a los juegos de PlayStation sin equivalente por nombre en otra fuente. Se registra como observación; no se verificó con datos reales de PlayStation.

## Condiciones para revisar la decisión

Revisar este ADR, y evaluar la alternativa 2 o la híbrida, si ocurre alguno de estos casos:

- Se planea una función que guarde datos propios del usuario en el servidor (favoritos, alertas, historial de precios, cuentas).
- Hay que conservar el catálogo de PlayStation entre reinicios, o compartirlo entre instancias, porque la recarga manual deja de ser aceptable.
- Se despliega más de una instancia y la diferencia entre sus cachés o catálogos produce resultados que el equipo no acepta.
- Se mide el costo real de un cambio de adaptador o de modelo y difiere de forma material de las estimaciones de esta tabla.
- Un cambio planeado del contrato público (`openapi.yaml`) afecta el identificador o la estructura de precios del juego.

## Verificación de ADR-0008 contra el código (errata, sin modificar ADR-0008)

ADR-0008, «Decisión» de la Decisión 1, dice que Steam, CheapShark y la tasa de cambio usan caché de 60 s, 24 h y 12 h «respectivamente». En el código:

- **Búsqueda en Steam:** 60 s (`SingleFlightCache`).
- **Búsqueda en CheapShark:** 60 s; las 24 h corresponden solo a la lista de tiendas (`_stores_duration_seconds`).
- **Requisitos de Steam:** 24 h.
- **Tasa de cambio:** 12 h.

La tabla correcta está en [arc42 §8.13](../arc42/arc42_8_conceptos_transversales.md). ADR-0008 no se reescribe: es una decisión histórica aceptada y esta errata la deja señalada.

## Trazabilidad

- Código verificado: `backend/app/domain/ports/game_catalog_repository.py`, `backend/app/infrastructure/persistence/in_memory_playstation_catalog.py`, `backend/app/application/usecases/sync_playstation_catalog.py`, `backend/app/main.py` (`PLAYSTATION_COMPATIBILITY_IDS`), `frontend/infrastructure/storage/BrowserPcProfileRepository.js`, `docs/api/drift/openapi.yaml`.
- Garantías por operación: [arc42 §8.13](../arc42/arc42_8_conceptos_transversales.md) y [§8.14](../arc42/arc42_8_conceptos_transversales.md).
- Registro de IA: `docs/ia.md`, Registro 43.
