# Contrato de Integración API — PlayStation

> **Qué es este documento:** borrador del contrato de integración de DRIFT con la API de PlayStation (PSN Swagger). Describe cómo el backend obtiene información de videojuegos, la normaliza y la almacena en la memoria local de DRIFT.
>
> **Qué NO es:** una lista de funcionalidades futuras ya implementadas. La sección de estado diferencia lo que funciona actualmente de lo que sigue pendiente.

## 1. Alcance de la API

La integración con PlayStation obtiene información de videojuegos, incluidos precios y disponibilidad cuando estén disponibles, y la almacena en la memoria local de DRIFT. Las consultas de los usuarios se resuelven con la información almacenada, sin depender de una llamada constante a la API externa, y el dominio de DRIFT permanece desacoplado del proveedor.

| Actor o sistema | Necesita realizar | Operación o interacción |
|---|---|---|
| Usuario | Buscar un videojuego | Consulta desde el frontend, resuelta contra la memoria local |
| Usuario | Conocer precios disponibles en PlayStation | Visualiza los resultados de búsqueda |
| Backend FastAPI | Obtener información de videojuegos de PlayStation | Solicitud `GET` al proveedor externo (PSN Swagger) |
| Backend FastAPI | Normalizar la información recibida | Transformación al modelo interno de DRIFT |
| Backend FastAPI | Almacenar la información obtenida | Memoria/repositorio local de DRIFT |
| Backend FastAPI | Informar el resultado de la actualización | Mensajes asíncronos de captura, finalización o fallo |
| Backend FastAPI | Mantener respuesta ante falla de PlayStation | Usa la información almacenada localmente |
| Adaptador PlayStation | Aislar la API externa del dominio | Encapsula solicitudes HTTP, transformación y errores |

## 2. Convenciones del contrato

- **Estilo de integración:** REST síncrono hacia la API externa y contrato asíncrono para el flujo de actualización.
- **Protocolo hacia PlayStation:** HTTP/HTTPS.
- **Formato de intercambio:** JSON.
- **Método principal:** `GET`.
- **Proveedor:** PlayStation Network, documentado mediante PSN Swagger.
- **Consumidor:** DRIFT, mediante el componente que obtiene y actualiza información de PlayStation.
- **Persistencia:** memoria/repositorio local de DRIFT.
- **Aislamiento:** la API externa no se utiliza directamente desde el dominio; toda comunicación pasa por el adaptador.
- **Especificaciones:** OpenAPI 3.1 (sección 3) y AsyncAPI 3.0 (sección 4).
- **Versionado propuesto:** `1.0.0`.

```text
DRIFT ── HTTP ──► PlayStation API
                       │ JSON
                       ▼
             Adaptador PlayStation
                       │ Normalización
                       ▼
              Memoria local DRIFT
```

La consulta a PlayStation es síncrona porque cada solicitud espera su respuesta antes de normalizar y almacenar los datos. Esa consulta ocurre durante la actualización de la información, no en cada búsqueda del usuario. Como la actualización se ejecuta de forma independiente de la búsqueda, su ciclo de vida se describe además mediante un contrato asíncrono.

## 3. Contrato síncrono REST

```yaml
openapi: 3.1.0

info:
  title: Integración DRIFT con PlayStation
  version: 1.0.0
  description: |
    Contrato de consumo de la API externa de PlayStation (PSN Swagger)
    por parte de DRIFT. DRIFT actúa como consumidor: obtiene información
    de videojuegos, la normaliza y la almacena en su memoria local.

servers:
  - url: https://{host}
    description: Proveedor externo PlayStation Network.
    variables:
      host:
        default: host-de-playstation
        description: Host de la API, según la documentación de PSN Swagger.

tags:
  - name: Videojuegos
    description: Consulta de información de videojuegos en PlayStation.

paths:
  /{recurso}:
    get:
      tags:
        - Videojuegos
      summary: Consultar información de videojuegos en PlayStation
      description: |
        Solicitud `GET` con `Accept: application/json`. El recurso concreto
        se toma de la documentación de PSN Swagger según la necesidad
        funcional de DRIFT.
      operationId: getPlayStationGames
      parameters:
        - name: recurso
          in: path
          required: true
          description: Recurso concreto documentado en PSN Swagger.
          schema:
            type: string
      responses:
        "200":
          description: Solicitud exitosa. DRIFT procesa y almacena la información.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/PlayStationGame"
              example:
                id: CUSA00000
                name: Nombre del videojuego
                price: 0.0
                currency: COP
                platform: PlayStation
        "400":
          description: Solicitud incorrecta. DRIFT registra el error y descarta la respuesta.
        "401":
          description: No autorizado. DRIFT registra el error de autenticación.
        "403":
          description: Acceso prohibido. DRIFT registra el error de acceso.
        "404":
          description: Recurso no encontrado. DRIFT registra la ausencia del recurso.
        "429":
          description: Límite de solicitudes superado. DRIFT aplica control de solicitudes o reintento.
        "500":
          description: Error del servidor externo. DRIFT registra el error y conserva la información local disponible.
        "502":
          $ref: "#/components/responses/ServicioNoDisponible"
        "503":
          $ref: "#/components/responses/ServicioNoDisponible"
        "504":
          $ref: "#/components/responses/ServicioNoDisponible"

components:
  responses:
    ServicioNoDisponible:
      description: Servicio externo no disponible. DRIFT registra el error y utiliza información local cuando sea posible.

  schemas:
    PlayStationGame:
      type: object
      description: |
        Videojuego tal como lo entrega PlayStation. Puede incluir información
        adicional según el recurso consultado.
      required:
        - id
        - name
      additionalProperties: true
      properties:
        id:
          type: string
          description: Identificador del videojuego en PlayStation.
          example: CUSA00000
        name:
          type: string
          description: Nombre del videojuego.
          example: Nombre del videojuego
        price:
          type: number
          description: Precio del videojuego.
          example: 0.0
        currency:
          type: string
          description: Moneda del precio.
          example: COP
        platform:
          type: string
          example: PlayStation

    NormalizedGame:
      type: object
      description: |
        Representación interna de DRIFT, independiente del proveedor.
        Es el formato que el adaptador entrega y la memoria local almacena.
      required:
        - id
        - name
        - source
        - platform
        - price
        - currency
        - discount
        - captured_at
      properties:
        id:
          type: string
          example: CUSA00000
        name:
          type: string
          example: Nombre del videojuego
        source:
          type: string
          const: playstation
        platform:
          type: string
          example: PlayStation
        price:
          type: number
          example: 0.0
        currency:
          type: string
          example: COP
        discount:
          type: integer
          example: 0
        captured_at:
          type: string
          format: date-time
          description: Momento en que DRIFT capturó la información.
          example: "2026-09-19T00:00:00Z"
```

## 4. Contratos asíncronos

El flujo de actualización de la información de PlayStation se describe como contrato asíncrono porque se ejecuta de forma independiente de la búsqueda del usuario. Cada etapa produce un mensaje:

| Mensaje | Tipo | Cuándo se produce |
|---|---|---|
| `UpdateRequested` | Comando (recibido por DRIFT) | Se solicita iniciar una actualización. |
| `GameCaptured` | Evento (publicado por DRIFT) | Un videojuego fue obtenido, normalizado y guardado en la memoria local. |
| `UpdateCompleted` | Evento (publicado por DRIFT) | La actualización terminó. |
| `UpdateFailed` | Evento (publicado por DRIFT) | La actualización falló; se conserva la información local disponible. |

```yaml
asyncapi: 3.0.0

info:
  title: Actualización de información de PlayStation en DRIFT
  version: 1.0.0
  description: |
    Contrato asíncrono del flujo de actualización de la información de
    PlayStation: solicitar información, recibir la respuesta JSON,
    normalizarla y guardarla en la memoria local de DRIFT.
    Las consultas de los usuarios no forman parte de este flujo.

defaultContentType: application/json

channels:
  updateRequested:
    address: playstation.catalog.update.requested
    description: Solicitud de inicio de una actualización.
    messages:
      updateRequested:
        $ref: "#/components/messages/UpdateRequested"

  gameCaptured:
    address: playstation.catalog.game.captured
    description: Videojuego normalizado y guardado en la memoria local.
    messages:
      gameCaptured:
        $ref: "#/components/messages/GameCaptured"

  updateCompleted:
    address: playstation.catalog.update.completed
    description: Fin exitoso de una actualización.
    messages:
      updateCompleted:
        $ref: "#/components/messages/UpdateCompleted"

  updateFailed:
    address: playstation.catalog.update.failed
    description: Fallo de una actualización.
    messages:
      updateFailed:
        $ref: "#/components/messages/UpdateFailed"

operations:
  receiveUpdateRequest:
    action: receive
    summary: Recibir la solicitud de actualización.
    channel:
      $ref: "#/channels/updateRequested"

  publishGameCaptured:
    action: send
    summary: Publicar cada videojuego capturado.
    channel:
      $ref: "#/channels/gameCaptured"

  publishUpdateCompleted:
    action: send
    summary: Publicar la finalización de la actualización.
    channel:
      $ref: "#/channels/updateCompleted"

  publishUpdateFailed:
    action: send
    summary: Publicar el fallo de la actualización.
    channel:
      $ref: "#/channels/updateFailed"

components:
  messages:
    UpdateRequested:
      name: UpdateRequested
      title: Actualización solicitada
      payload:
        $ref: "#/components/schemas/UpdateRequestedPayload"
      examples:
        - payload:
            source: playstation
            requested_at: "2026-09-19T00:00:00Z"

    GameCaptured:
      name: GameCaptured
      title: Videojuego capturado
      payload:
        $ref: "#/components/schemas/NormalizedGame"
      examples:
        - payload:
            id: CUSA00000
            name: Nombre del videojuego
            source: playstation
            platform: PlayStation
            price: 0.0
            currency: COP
            discount: 0
            captured_at: "2026-09-19T00:00:00Z"

    UpdateCompleted:
      name: UpdateCompleted
      title: Actualización completada
      payload:
        $ref: "#/components/schemas/UpdateCompletedPayload"
      examples:
        - payload:
            source: playstation
            games_loaded: 1
            completed_at: "2026-09-19T00:00:05Z"

    UpdateFailed:
      name: UpdateFailed
      title: Actualización fallida
      payload:
        $ref: "#/components/schemas/UpdateFailedPayload"
      examples:
        - payload:
            source: playstation
            reason: Servicio externo no disponible
            http_status: 503
            local_data_preserved: true
            occurred_at: "2026-09-19T00:00:05Z"

  schemas:
    UpdateRequestedPayload:
      type: object
      required:
        - source
        - requested_at
      properties:
        source:
          type: string
          const: playstation
        requested_at:
          type: string
          format: date-time

    NormalizedGame:
      type: object
      description: Misma representación normalizada definida en la sección 3.
      required:
        - id
        - name
        - source
        - platform
        - price
        - currency
        - discount
        - captured_at
      properties:
        id:
          type: string
        name:
          type: string
        source:
          type: string
          const: playstation
        platform:
          type: string
        price:
          type: number
        currency:
          type: string
        discount:
          type: integer
        captured_at:
          type: string
          format: date-time

    UpdateCompletedPayload:
      type: object
      required:
        - source
        - games_loaded
        - completed_at
      properties:
        source:
          type: string
          const: playstation
        games_loaded:
          type: integer
          description: Cantidad de videojuegos guardados en la memoria local.
        completed_at:
          type: string
          format: date-time

    UpdateFailedPayload:
      type: object
      required:
        - source
        - reason
        - local_data_preserved
        - occurred_at
      properties:
        source:
          type: string
          const: playstation
        reason:
          type: string
          description: Motivo del fallo.
        http_status:
          type: integer
          description: Código HTTP devuelto por la API externa, si aplica.
        local_data_preserved:
          type: boolean
          description: Indica que la información local existente se conservó.
        occurred_at:
          type: string
          format: date-time
```

Este contrato no fija el transporte de los mensajes (broker o cola) ni el disparador de `UpdateRequested` (manual o periódico). Su estado de implementación se indica en la sección 5.

Beneficios del flujo asíncrono:

- Reduce la dependencia de la disponibilidad de la API externa.
- Evita consultas innecesarias a PlayStation.
- Facilita incorporar nuevas fuentes sin acoplar el dominio a PlayStation.

## 5. Estado actual de implementación

| Operación o funcionalidad | En el contrato | Implementado actualmente |
|---|---|---|
| Puerto de fuente externa de catálogo (`GameCatalogSource`) | Sí | Sí |
| Adaptador PlayStation con PSN Swagger | Sí | No; el adaptador actual consulta PlatPrices |
| Normalización al modelo interno | Sí | Sí, transformación a `Game` |
| Almacenamiento en memoria local | Sí | Sí, mediante `InMemoryGameRepository` |
| Búsqueda contra la información local | Sí | Sí, mediante `GET /games/search?q={consulta}` |
| Actualización de la información local | Sí | Sí, mediante `POST /games/sync/platprices` |
| Conservación de la información local ante falla externa | Sí | Sí, el catálogo anterior no se reemplaza |
| Publicación de mensajes de actualización (AsyncAPI) | Sí | No; la actualización se ejecuta de forma directa, sin publicar mensajes |
| Registro de errores de la API externa | Sí | No; el error se devuelve en la respuesta de la sincronización |
| Control de solicitudes o reintento ante `429` | Sí | No |
| Actualización periódica automática | Sí | No |
| Historial de precios | No | No |

## 6. Endpoints propuestos para futuros incrementos

Los recursos concretos dependerán de los endpoints disponibles en PSN Swagger y de las necesidades funcionales de DRIFT.

| Endpoint propuesto | Propósito | Estado |
|---|---|---|
| `GET` Buscar videojuegos | Obtener videojuegos según un criterio de búsqueda. | Pendiente |
| `GET` Consultar información de videojuego | Obtener información detallada. | Pendiente |
| `GET` Consultar información comercial | Obtener precio, descuento y disponibilidad. | Pendiente |
| `GET` Consultar imágenes | Obtener recursos visuales. | Pendiente |
| `GET` Actualizar información local | Capturar nuevamente información desde PlayStation. | Pendiente |
