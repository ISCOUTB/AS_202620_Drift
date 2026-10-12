# ADR-0008: Degradación controlada y aviso por fuente en la búsqueda

- **Estado:** Aprobado
- **Fecha:** 2026-10-11
- **Decisores:** Equipo de desarrollo de DRIFT
- **Relacionado con:** E6 (degradación bajo carga)

## Contexto

La búsqueda consulta Steam, CheapShark y PlayStation. Antes de este cambio:

- `CombinedGameRepository` descartaba en silencio los errores de CheapShark y PlayStation; solo Steam figuraba en `unavailable_sources`.
- Los adaptadores de Steam y CheapShark mantenían un lock global durante la llamada HTTP, de modo que las búsquedas con caché fría se serializaban.
- No había un plazo propio por fuente: la espera dependía del timeout de cada llamada HTTP.
- El catálogo en memoria devolvía objetos compartidos que otros componentes modificaban.

Una respuesta con precios de tiendas faltantes se parece a una respuesta completa y puede llevar a elegir un «mejor precio» incorrecto.

## Decisión (propuesta)

Tres cambios solo en infraestructura, sin tocar dominio, puertos ni casos de uso:

1. **Lock fuera del I/O.** `SingleFlightCache` protege solo el diccionario; una sola llamada en vuelo por clave. Los adaptadores entregan copias de los objetos en caché y `InMemoryGameRepository` devuelve copias.
2. **Plazo por fuente.** `CombinedGameRepository` espera como máximo `DRIFT_SOURCE_TIMEOUT_SECONDS` (3 s por defecto) a la fuente secundaria, contado desde que se lanza la consulta.
3. **Aviso por fuente.** Si la fuente secundaria falla o vence, su nombre se añade a `unavailable_sources` de los resultados. El frontend ya muestra esa lista.

## Alternativas descartadas

- Dejar el estado actual: mantiene el problema.
- Circuito de corte con biblioteca externa: más dependencias para un problema que un plazo resuelve.
- MySQL con actualización asíncrona: es la alternativa de ADR-0004; ver ADR-0008.

## Consecuencias

- La búsqueda deja de esperar más de 3 s a CheapShark y a PlayStation; un hilo abandonado termina por su propio timeout HTTP.
- La fuente primaria (Steam) no tiene plazo propio; depende del timeout de httpx y de `ResilientGameRepository`.
- Si la búsqueda no devuelve ningún juego, no hay resultado donde llevar el aviso (arc42 §11.7).
- La fuente que vence se vuelve a consultar en la siguiente búsqueda; no hay circuito de corte.

## Validación

Experimento E6 antes/después: `docs/evidencias/e6-degradacion-bajo-carga.md`. Pruebas: `backend/tests/test_source_degradation.py`.
