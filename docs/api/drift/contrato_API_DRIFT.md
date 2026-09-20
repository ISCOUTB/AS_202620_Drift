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
| Estado de salud de la API | Sí | Sí, mediante `GET /` |
| Búsqueda de videojuegos | Sí | Sí, mediante `GET /games/search?q={consulta}` |
| Consulta a Steam | Sí | Sí |
| Catálogo local de respaldo | Sí | Sí, ante falla de Steam |
| Aviso de fuente no disponible | Sí | Sí, mediante `unavailable_sources` |
| Estimación de compatibilidad | Sí | Sí, mediante `POST /games/{game_id}/compatibility` |
| Autenticación de usuarios | No | No |
| Perfil y dispositivos del usuario | No | No |
| Detalle individual de un videojuego | No | No |
| Historial de precios | No | No |
| Integración real con otras fuentes adicionales | No | No |
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

1.0.0

El contrato ejecutable se mantiene en:

[docs/api/drift/openapi.yaml](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/api/drift/openapi.yaml)

Los cambios incompatibles en rutas, parámetros, solicitudes o respuestas deberán reflejarse en una nueva versión del contrato y validarse mediante las pruebas de contrato correspondientes.

## 8. Historial de versiones

| Versión | Fecha | Descripción |
|---|---|---|
| 1.0.0 | 2026-09-19 | Versión inicial del contrato HTTP de la API de DRIFT. Incluye estado de la API, búsqueda de videojuegos, sincronización del catálogo de PlayStation y estimación de compatibilidad. |
