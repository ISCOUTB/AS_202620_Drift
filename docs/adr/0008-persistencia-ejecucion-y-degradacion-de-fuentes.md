# ADR-0008: Persistencia, modelo de ejecución y degradación controlada de fuentes

- **Estado:** Aceptado
- **Fecha:** 2026-10-11
- **Decisores:** Equipo de desarrollo de DRIFT
- **Sustituye a:** ADR-0004 (estrategia híbrida con MySQL y actualización asíncrona)
- **Relacionado con:** escenarios E5 (fallo de una fuente) y E6 (degradación bajo carga)

Este ADR recoge dos decisiones relacionadas: (1) la persistencia y el modelo de ejecución y (2) la degradación controlada de las fuentes de la búsqueda. Se registran juntas porque la segunda depende de que el catálogo sea en memoria y la ejecución síncrona.

## Contexto

### Persistencia y modelo de ejecución

DRIFT es una plataforma web para consultar y comparar videojuegos y su información comercial. Su arquitectura separa las responsabilidades del sistema mediante un enfoque de puertos y adaptadores, con el objetivo de favorecer la mantenibilidad y permitir que las fuentes de datos puedan evolucionar sin afectar directamente al dominio.

Durante la revisión arquitectónica se identificó la necesidad de verificar la coherencia entre las decisiones documentadas, la implementación del backend y la infraestructura de persistencia.

En particular, deben aclararse dos aspectos:

1. El mecanismo de almacenamiento utilizado para conservar la información de los videojuegos.
2. El modelo de ejecución empleado para realizar las operaciones de consulta e integración con fuentes externas.

La documentación debe representar el comportamiento real del sistema y distinguir entre las funcionalidades implementadas y las que todavía se encuentran pendientes.

### Degradación de las fuentes

La búsqueda consulta Steam, CheapShark y PlayStation. Antes de este cambio:

- `CombinedGameRepository` descartaba en silencio los errores de CheapShark y PlayStation; solo Steam figuraba en `unavailable_sources`.
- Los adaptadores de Steam y CheapShark mantenían un lock global durante la llamada HTTP, de modo que las búsquedas con caché fría se serializaban.
- No había un plazo propio por fuente: la espera dependía del timeout de cada llamada HTTP.
- El catálogo en memoria devolvía objetos compartidos que otros componentes modificaban.

Una respuesta con precios de tiendas faltantes se parece a una respuesta completa y puede llevar a elegir un «mejor precio» incorrecto.

## Problema

Es necesario establecer una decisión arquitectónica coherente sobre la persistencia y el modelo de ejecución para evitar contradicciones entre los ADR, los diagramas C4, la documentación arc42 y el código fuente.

La decisión debe considerar la complejidad de implementación, la mantenibilidad, la confiabilidad y las necesidades actuales del proyecto.

Además, la búsqueda debe seguir respondiendo con las fuentes disponibles cuando una de ellas es lenta o falla, y debe avisarlo.

## Decisión 1: persistencia y modelo de ejecución

### Alternativas consideradas

#### Alternativa 1: almacenamiento en memoria y ejecución síncrona

Utilizar un repositorio en memoria para almacenar temporalmente los datos y ejecutar las operaciones de consulta de manera síncrona.

**Ventajas:**

- Menor complejidad de implementación.
- Facilita las pruebas y el desarrollo inicial.
- Reduce la configuración de infraestructura necesaria.

**Desventajas:**

- Los datos almacenados pueden perderse al reiniciar el proceso.
- No proporciona persistencia compartida entre instancias.
- Puede resultar insuficiente si se requiere conservar información de manera permanente.

#### Alternativa 2: persistencia mediante MySQL y ejecución síncrona

Utilizar una base de datos MySQL para conservar la información y realizar las operaciones mediante un flujo síncrono.

**Ventajas:**

- Permite conservar los datos entre reinicios.
- Facilita la gestión de información persistente.
- Mantiene un modelo de ejecución relativamente sencillo.

**Desventajas:**

- Requiere configurar y mantener la base de datos.
- Introduce dependencias de infraestructura.
- Las operaciones de entrada y salida pueden bloquear el flujo de ejecución durante la espera.

#### Alternativa 3: persistencia mediante MySQL y ejecución asíncrona

Utilizar MySQL como mecanismo de persistencia e implementar operaciones asíncronas cuando las necesidades de concurrencia y rendimiento lo justifiquen.

**Ventajas:**

- Permite conservar información de forma persistente.
- Puede mejorar el aprovechamiento de recursos durante operaciones de entrada y salida.
- Facilita la evolución hacia escenarios con mayor concurrencia, si la implementación está diseñada adecuadamente.

**Desventajas:**

- Incrementa la complejidad del código y de las pruebas.
- Requiere controlar correctamente las operaciones asíncronas y los errores.
- Puede añadir complejidad innecesaria si las necesidades actuales no lo justifican.

### Decisión

**Alternativa 1: catálogo en memoria y ejecución síncrona.**

Verificación contra el repositorio (octubre de 2026):

- No existe ningún adaptador, dependencia, configuración ni servicio de MySQL: `backend/requirements.txt` no incluye un controlador de base de datos y `deploy/compose.lab.yaml` define solo los servicios `api` y `web`, sin volúmenes (el límite del laboratorio es 512 MB).
- El catálogo de PlayStation es `InMemoryPlayStationCatalog` y el respaldo de Steam es `InMemoryGameRepository`; ambos se pierden al reiniciar.
- No hay planificador ni cola: la sincronización de PlayStation es un `POST /games/sync/playstation` invocado de forma síncrona y las búsquedas consultan las fuentes con HTTP síncrono en hilos (`CombinedGameRepository`).
- Las fuentes que se consultan en cada búsqueda (Steam, CheapShark, tasa de cambio) usan caché en memoria de 60 s, 24 h y 12 h respectivamente.

**Justificación:** DRIFT no guarda datos propios del usuario ni histórico; el catálogo se obtiene de fuentes externas y se puede reconstruir. MySQL añadiría un contenedor y memoria dentro de un presupuesto de 512 MB sin un requisito que lo exija hoy.

Componentes afectados: `InMemoryGameRepository`, `InMemoryPlayStationCatalog`, `CombinedGameRepository`, los adaptadores de Steam y CheapShark, C4 contenedores, arc42 §5, §7 y §11, y el despliegue Docker Compose.

Consecuencias negativas asumidas: el catálogo de PlayStation queda vacío tras un reinicio hasta nueva sincronización; no hay datos compartidos entre réplicas (cada una tiene su propia caché).

ADR-0004 queda `Superseded por ADR-0008` en cuanto a MySQL y actualización asíncrona. De ADR-0004 se conservan el encapsulamiento de cada fuente en un adaptador y la normalización antes del modelo interno. Lo que depende de MySQL o de un proceso asíncrono quedaría como evolución futura.

## Decisión 2: degradación controlada y aviso por fuente

Tres cambios, solo en infraestructura, sin tocar dominio, puertos ni casos de uso:

1. **Lock fuera del I/O.** `SingleFlightCache` protege solo el diccionario; una sola llamada en vuelo por clave. Los adaptadores entregan copias de los objetos en caché y `InMemoryGameRepository` devuelve copias.
2. **Plazo por fuente.** `CombinedGameRepository` espera como máximo `DRIFT_SOURCE_TIMEOUT_SECONDS` (3 s por defecto) a la fuente secundaria, contado desde que se lanza la consulta.
3. **Aviso por fuente.** Si la fuente secundaria falla o vence, su nombre se añade a `unavailable_sources` de los resultados. El frontend ya muestra esa lista.

### Alternativas descartadas

- Dejar el estado actual: mantiene el problema.
- Circuito de corte con biblioteca externa: más dependencias para un problema que un plazo resuelve.

## Consecuencias

La decisión definitiva deberá reflejarse de manera consistente en:

- Los modelos y puertos del dominio.
- Los adaptadores de persistencia del backend.
- Los casos de uso de consulta.
- Los diagramas C4 de contenedores y componentes, cuando corresponda.
- Las secciones 5, 6, 7, 8 y 9 de arc42, según los cambios realizados.
- Las pruebas automatizadas y la configuración de despliegue.
- El README y las instrucciones de ejecución del proyecto.

La aceptación del ADR no demuestra por sí misma que la alternativa elegida esté implementada. La implementación y sus pruebas deberán verificarse por separado.

Consecuencias de la decisión 2:

- La búsqueda deja de esperar más de 3 s a CheapShark y a PlayStation; un hilo abandonado termina por su propio timeout HTTP.
- La fuente primaria (Steam) no tiene plazo propio; depende del timeout de httpx y de `ResilientGameRepository`.
- Si la búsqueda no devuelve ningún juego, no hay resultado donde llevar el aviso (arc42 §11.7).
- La fuente que vence se vuelve a consultar en la siguiente búsqueda; no hay circuito de corte.

## Criterios de validación

La decisión se considerará validada cuando:

1. El mecanismo de persistencia esté identificado y documentado.
2. El modelo de ejecución coincida con el código real.
3. Las pruebas relevantes se ejecuten correctamente.
4. Los diagramas y documentos afectados estén actualizados.
5. La decisión y sus consecuencias puedan relacionarse con los componentes implementados.
6. La decisión 2 se contraste con el umbral del escenario 6 mediante el experimento E6 (`docs/evidencias/e6-degradacion-bajo-carga.md`) y las pruebas `backend/tests/test_source_degradation.py`.

## Referencias

- Documentación de arquitectura arc42 de DRIFT.
- Diagramas C4 del proyecto.
- ADR anteriores relacionados con persistencia y ejecución.
- Código fuente y pruebas automatizadas del backend.
