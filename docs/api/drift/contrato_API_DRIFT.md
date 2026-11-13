# Contrato de API DRIFT

> **Qué es este documento:** contrato de la API de DRIFT. Describe cómo se comunican el frontend y el backend para buscar videojuegos y estimar la compatibilidad de un PC.
>
> **Qué NO es:** una lista de funcionalidades futuras ya implementadas. La sección de estado diferencia lo que funciona actualmente de lo que sigue pendiente.

## 1. Alcance de la API

DRIFT es una plataforma que ayuda a los jugadores a buscar videojuegos, comparar precios disponibles y estimar si un PC puede ejecutar un juego según sus requisitos.

| Actor o sistema | Necesita realizar | Operación o interacción |
|---|---|---|
| Usuario | Buscar un videojuego | Consulta desde el frontend de DRIFT |
| Usuario | Conocer precios disponibles | Visualiza los resultados de búsqueda |
| Usuario | Estimar compatibilidad de su PC | Envía RAM disponible y nivel de GPU |
| Frontend Next.js | Obtener resultados de búsqueda | `GET /games/search?q={consulta}` |
| Frontend Next.js | Solicitar estimación de compatibilidad | `POST /games/{game_id}/compatibility` |
| Backend FastAPI | Consultar información externa | Consulta síncrona a Steam mediante HTTP y JSON |
| Backend FastAPI | Mantener respuesta ante falla de Steam | Usa catálogo local de respaldo |

## 2. Convenciones del contrato

- **Estilo de integración:** REST síncrono.
- **Protocolo entre frontend y backend:** HTTP.
- **Formato de intercambio:** JSON.
- **Servidor local:** `http://localhost:8000`.
- **Autenticación:** no implementada en la versión actual.
- **Versionado:** `1.0.0`.
- **Fuente externa:** Steam.
- **Respaldo:** catálogo local en memoria cuando Steam no está disponible.

La integración es síncrona porque las operaciones actuales necesitan una respuesta inmediata para mostrar los resultados al usuario.

## 3. Contrato síncrono REST

El contrato REST de la API de DRIFT se encuentra definido en:

`docs/api/drift/openapi.yaml`

El contrato está especificado mediante **OpenAPI 3.1.0** y documenta las operaciones disponibles actualmente en el backend.

### Endpoints principales

| Método | Endpoint | Propósito |
|---|---|---|
| `GET` | `/` | Consultar el estado de disponibilidad de la API. |
| `GET` | `/games/search?q={consulta}` | Buscar videojuegos por nombre. |
| `POST` | `/games/{game_id}/compatibility` | Estimar la compatibilidad de un videojuego con las especificaciones de un PC. |

Las solicitudes y respuestas utilizan **HTTP y JSON**.

El contrato OpenAPI define los parámetros, cuerpos de solicitud, respuestas y esquemas correspondientes a cada operación.

El archivo `openapi.yaml` constituye el contrato técnico ejecutable y versionado, mientras que este documento proporciona su descripción funcional y arquitectónica.

## 4. Contratos asíncronos

La API actual de DRIFT no utiliza contratos asíncronos.

Las operaciones expuestas actualmente son síncronas y funcionan mediante el modelo solicitud-respuesta HTTP.

No se utilizan actualmente eventos, colas de mensajería, Kafka, RabbitMQ ni otros mecanismos de comunicación asíncrona dentro de esta API.

Los procesos asíncronos relacionados con la actualización de información de fuentes externas se documentan de manera independiente en el contrato de integración de PlayStation:

`docs/api/playstation/asyncapi.yaml`

Estos procesos forman parte de la estrategia de integración externa y no de los endpoints actuales de la API de DRIFT.

## 5. Estado actual de implementación

| Operación o funcionalidad | En el contrato | Implementado actualmente |
|---|---|---|
| Estado de salud de la API | Sí | Sí, mediante `GET /` y `GET /health`; métricas administrativas en `GET /metrics` |
| Búsqueda de videojuegos | Sí | Sí, mediante `GET /games/search?q={consulta}` |
| Consulta a Steam | Sí | Sí |
| Catálogo local de respaldo | Sí | Sí, ante falla de Steam |
| Aviso de fuente no disponible | Sí | Sí, mediante `unavailable_sources` |
| Aviso de precio tomado de la copia de respaldo | Sí | Sí, mediante `cached_sources` (ADR-0015) |
| Estimación de compatibilidad | Sí | Sí, mediante `POST /games/{game_id}/compatibility` |
| Autenticación de usuarios | Sí (`/auth/me`, `/auth/google/login`, `/auth/google/callback`, `/auth/logout`) | Sí, con Google (ADR-0017) |
| Perfil y dispositivos del usuario | Sí (`/devices`, `/devices/{device_id}`) | Sí |
| Detalle individual de un videojuego | No | No |
| Recarga de los puntajes de hardware | Sí (`POST /hardware/benchmarks/sync`) | Sí, con el token administrativo (ADR-0018) |
| Juegos del momento y lista de tiendas | Sí (`GET /games/featured`, `GET /stores`) | Sí |
| Explorar el catálogo por género y filtros | Sí (`GET /games/explore`) | Sí, con el catálogo de Steam |
| Juegos favoritos | Sí (`GET /favorites`, `PUT` y `DELETE /favorites/{game_id}`) | Sí, con sesión (ADR-0020) |
| Alertas de precio de los favoritos | Sí (`GET /favorites/alerts`, `PUT /favorites/{game_id}/target`) | Sí, con sesión; solo tiendas de PC y solo al abrir DRIFT (ADR-0021) |
| Recomendación de compra | Sí (`POST /games/{game_id}/recommendation`) | Sí, con los precios y dispositivos que envía la página (ADR-0019) |
| Historial de precios | Sí | Sí, mediante `GET /games/{game_id}/price-history`, con la llave de IsThereAnyDeal (ADR-0016) |
| Precios de la tienda de Xbox (Colombia, en pesos) | Sí | Sí |
| Descuento de cada tienda | Sí | Sí, mediante `discounts` |
| Filtro por plataforma | Sí | Sí, mediante `platform` y el campo `platforms` |
| Juegos que solo existen en una tienda de consola | Sí | Sí, con el identificador de esa tienda |
| Eventos o contratos AsyncAPI para la API de DRIFT | No | No |

## 6. Relación con la arquitectura

La API de DRIFT forma parte de la arquitectura basada en puertos y adaptadores.

El frontend Next.js consume los endpoints HTTP expuestos por FastAPI. El backend utiliza puertos para desacoplar los casos de uso de las implementaciones concretas de las fuentes externas.

El acceso a Steam se realiza mediante un adaptador externo, mientras que el catálogo local permite disponer de información cuando la fuente externa no está disponible.

```text
Frontend Next.js
       │
       │ HTTP + JSON
       ▼
   FastAPI / DRIFT
       │
       ├── Búsqueda de videojuegos
       │
       ├── Compatibilidad de PC
       │
       ▼
 Adaptadores externos
       │
       └── Steam
```
La API mantiene actualmente un modelo síncrono para las operaciones que requieren respuesta inmediata. Los procesos de actualización externa que puedan ejecutarse de manera independiente se documentan mediante contratos de integración específicos.

## 7. Versionado del contrato

La versión actual del contrato es:

1.8.0

El contrato ejecutable se mantiene en:

[docs/api/drift/openapi.yaml](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/api/drift/openapi.yaml)

Los cambios incompatibles en rutas, parámetros, solicitudes o respuestas deberán reflejarse en una nueva versión del contrato y validarse mediante las pruebas de contrato correspondientes.

## 8. Historial de versiones

| Versión | Fecha | Descripción |
|---|---|---|
| 1.0.0 | 2026-09-19 | Versión inicial del contrato HTTP de la API de DRIFT. Incluye estado de la API, búsqueda de videojuegos, sincronización del catálogo de PlayStation y estimación de compatibilidad. |
| 1.1.0 | 2026-10-11 | Cambio compatible: `GET /games/search` añade el campo opcional `image` y `unavailable_sources` puede listar también `CheapShark` y `PlayStation` cuando esas fuentes fallan o superan el plazo de 3 s (ADR-0008). |
| 1.2.0 | 2026-10-12 | Cambio compatible: `POST /games/{game_id}/compatibility` acepta `gpu_name` y `storage_gb` opcionales; la respuesta añade el desglose por componente (`checks`), el almacenamiento, la fuente y el texto de los requisitos. `minimum_gpu_score` y `recommended_gpu_score` pueden ser nulos. Los requisitos se obtienen de Steam cuando no están en el catálogo propio. |
| 1.3.0 | 2026-10-12 | Cambio compatible: nuevos `GET /hardware/gpus` y `GET /hardware/cpus` con los nombres y el nivel aproximado de las tarjetas gráficas y los procesadores conocidos (sin puntajes). La estimación acepta `cpu_name` y `cpu_score` opcionales y añade el procesador al desglose. Gráfica y procesador se comparan por puntaje cuando el componente del usuario y el del requisito están en el catálogo (`gpu_benchmark`, `cpu_benchmark`); en otro caso, por niveles. |
| 1.4.0 | 2026-10-12 | Cambio compatible: `GET /games/search` añade `links`, con la página de compra de cada tienda (Steam, PlayStation Store y las tiendas de PC mediante el enlace de redirección de CheapShark). |
| 1.6.0 | 2026-11-12 | Cambio compatible: `GET /games/search` añade `cached_sources`. Cuando una fuente falla y existe una copia de su última respuesta (de menos de 72 horas), los precios salen de esa copia y el campo indica la fuente y la fecha del dato. Esa fuente ya no aparece en `unavailable_sources` (ADR-0015). Además: nueva fuente Xbox (puede aparecer en `unavailable_sources` y `cached_sources`); nuevos campos `discounts` y `platforms`; nuevo parámetro opcional `platform`. **Cambio de comportamiento:** la búsqueda ya no omite los juegos sin identificador de Steam. Los que solo existen en PlayStation, Xbox u otra tienda de PC aparecen con el identificador de esa tienda, que no es numérico; `POST /games/{game_id}/compatibility` sigue aceptando solo identificadores de Steam. Nuevo `GET /games/{game_id}/price-history`. Con la llave de IsThereAnyDeal, las tiendas de PC salen de esa fuente y el nombre `IsThereAnyDeal` reemplaza a `CheapShark` en `unavailable_sources` y `cached_sources` (ADR-0016). |
| 1.7.0 | 2026-11-13 | Cambio compatible: se documentan en OpenAPI las rutas que ya existían sin contrato: estado (`GET /health`, `GET /metrics`), portada (`GET /games/featured`, `GET /stores`), recomendación (`POST /games/{game_id}/recommendation`), cuentas (`/auth/*`, `/devices`), favoritos y alertas (`/favorites`, `/favorites/alerts`, `/favorites/{game_id}/target`) y la recarga de puntajes (`POST /hardware/benchmarks/sync`). Nuevo esquema de seguridad `sessionCookie` (cookie `drift_session`). **Correcciones:** una respuesta 405 lista en `Allow` todos los métodos de la dirección, y `PUT`/`DELETE /favorites/alerts` responden 405 en vez de tratar «alerts» como un juego. |
| 1.8.0 | 2026-11-13 | Cambio compatible: nuevo `GET /games/explore`, una página del catálogo de Steam por género, etiquetas, orden y precio, con la ficha de cada juego (imágenes, descripción, etiquetas, fecha, desarrolladores, reseñas y precio en Steam). `GET /games/featured` mantiene sus campos, pero `image`, `hero` y `header` ahora son las rutas reales de Steam: las armadas con el identificador daban 404 en los juegos recientes. **Corrección:** el `Allow` de los 405 también lista los métodos de las rutas de cuentas con FastAPI 0.162, que guarda los routers incluidos de otra forma. |
