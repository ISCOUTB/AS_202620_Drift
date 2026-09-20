# Contrato de Integración API — PlayStation

> **Qué es este documento:** contrato de integración de DRIFT con la API de PlayStation (PSN Swagger). Describe cómo el backend obtiene información de videojuegos, la normaliza y la incorpora al almacenamiento persistente de DRIFT.
>
> **Qué NO es:** una lista de funcionalidades futuras ya implementadas. La sección de estado diferencia lo que funciona actualmente de lo que corresponde a la estrategia de integración y a incrementos posteriores.

## 1. Alcance de la API

La integración con PlayStation permite obtener información de videojuegos, incluidos precios y disponibilidad cuando estén disponibles, y transformarla al modelo interno de DRIFT. La información obtenida puede ser almacenada en MySQL para reducir la dependencia de consultas directas al proveedor externo durante las búsquedas de los usuarios.

| Actor o sistema | Necesita realizar | Operación o interacción |
|---|---|---|
| Usuario | Buscar un videojuego | Consulta desde el frontend de DRIFT |
| Usuario | Conocer precios disponibles en PlayStation | Visualiza los resultados disponibles en DRIFT |
| Backend FastAPI | Obtener información de videojuegos de PlayStation | Solicitud `GET` al proveedor externo mediante PSN Swagger |
| Backend FastAPI | Normalizar la información recibida | Transformación al modelo interno de DRIFT |
| Backend FastAPI | Almacenar la información obtenida | Persistencia en MySQL |
| Backend FastAPI | Actualizar información del catálogo | Ejecución del proceso de actualización definido para la fuente |
| Backend FastAPI | Mantener disponibilidad ante una falla externa | Utiliza la información previamente almacenada cuando esté disponible |
| Adaptador PlayStation | Aislar la API externa del dominio | Encapsula solicitudes HTTP, transformación y manejo de errores |

## 2. Convenciones del contrato

- **Estilo de integración:** REST síncrono hacia la API externa y flujo asíncrono para procesos de actualización del catálogo.
- **Protocolo hacia PlayStation:** HTTP/HTTPS.
- **Formato de intercambio:** JSON.
- **Método principal:** `GET`.
- **Proveedor:** PlayStation Network, documentado mediante PSN Swagger.
- **Persistencia:** MySQL.
- **Aislamiento:** la API externa no se utiliza directamente desde el dominio; toda comunicación pasa por el adaptador correspondiente.
- **Especificaciones:** OpenAPI 3.1 para la integración REST y AsyncAPI 3.0 para el flujo de actualización.
- **Versionado:** `1.0.0`.

```text
DRIFT ── HTTP/HTTPS + JSON ──► PlayStation API
                                  │
                                  ▼
                         Adaptador PlayStation
                                  │
                           Normalización
                                  │
                                  ▼
                                MySQL
```

La consulta a PlayStation utiliza comunicación síncrona porque cada solicitud necesita una respuesta del proveedor antes de poder procesar la información obtenida.

La estrategia de actualización del catálogo se separa de las consultas interactivas del usuario. La información obtenida puede ser procesada, normalizada y almacenada periódicamente en MySQL, reduciendo la necesidad de consultar directamente al proveedor en cada búsqueda.

## 3. Contrato síncrono REST

```yaml
openapi: 3.1.0

info:
  title: Integración DRIFT con PlayStation
  version: 1.0.0
  description: |
    Contrato de consumo de la API externa de PlayStation (PSN Swagger)
    por parte de DRIFT. DRIFT actúa como consumidor: obtiene información
    de videojuegos, la normaliza y la almacena en MySQL.

servers:
  - url: https://{host}
    description: Proveedor externo PlayStation Network.
    variables:
      host:
        default: host-de-playstation
        description: Host de la API según la documentación de PSN Swagger.

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
        Solicitud GET con Accept: application/json.
        El recurso concreto se toma de la documentación de PSN Swagger
        según la necesidad funcional de DRIFT.
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
          description: Límite de solicitudes superado. DRIFT registra el error y puede aplicar control de solicitudes o reintento.

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
      description: |
        Servicio externo no disponible. DRIFT registra el error
        y utiliza información previamente almacenada cuando sea posible.

  schemas:

    PlayStationGame:
      type: object
      description: |
        Representación de un videojuego obtenida desde PlayStation.
        Puede incluir información adicional según el recurso consultado.
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
          description: Plataforma de origen.
          example: PlayStation

    NormalizedGame:
      type: object
      description: |
        Representación interna de DRIFT, independiente del proveedor.
        Es el formato que el adaptador entrega para su almacenamiento
        y posterior utilización por el sistema.
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

## 4. Contrato asíncrono

El flujo de actualización del catálogo se define mediante un contrato asíncrono independiente de las consultas interactivas de los usuarios.

La estrategia contempla que una actualización sea solicitada y que el proceso obtenga información desde PlayStation, la normalice y la almacene en MySQL. El mecanismo concreto de programación o mensajería será definido durante la implementación.

| Mensaje | Tipo | Cuándo se produce |
| ------- | ---- | ------------------ |
| `UpdateRequested` | Comando | Se solicita iniciar una actualización del catálogo de PlayStation. |
| `GameCaptured` | Evento | Un videojuego fue obtenido, normalizado y preparado para almacenamiento. |
| `UpdateCompleted` | Evento | La actualización terminó correctamente. |
| `UpdateFailed` | Evento | La actualización presentó un error; la información previamente almacenada se conserva. |

```yaml
asyncapi: 3.0.0

info:
  title: Actualización de información de PlayStation en DRIFT
  version: 1.0.0
  description: |
    Contrato asíncrono del flujo de actualización del catálogo de PlayStation.
    El proceso permite solicitar una actualización, obtener información,
    normalizarla y almacenarla en MySQL sin depender del ciclo de vida
    de las consultas realizadas por los usuarios.

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
    description: Videojuego obtenido y normalizado para su almacenamiento.
    messages:
      gameCaptured:
        $ref: "#/components/messages/GameCaptured"

  updateCompleted:
    address: playstation.catalog.update.completed
    description: Finalización exitosa de una actualización.
    messages:
      updateCompleted:
        $ref: "#/components/messages/UpdateCompleted"

  updateFailed:
    address: playstation.catalog.update.failed
    description: Fallo durante una actualización.
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
      description: Representación normalizada de un videojuego en DRIFT.
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
          description: Cantidad de videojuegos procesados durante la actualización.

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
          description: Indica que la información almacenada previamente se conserva.

        occurred_at:
          type: string
          format: date-time
```

El contrato asíncrono define la interacción lógica del proceso de actualización, pero no fija todavía el mecanismo concreto de transporte de mensajes ni el programador que iniciará la actualización.

## 5. Estado actual de implementación

| Operación o funcionalidad | En el contrato | Estado actual |
| -------------------------- | -------------- | -------------- |
| Puerto de fuente externa de catálogo (`GameCatalogSource`) | Sí | Implementado |
| Integración con PlayStation mediante PSN Swagger | Sí | Implementada según la integración actual |
| Normalización al modelo interno | Sí | Implementada mediante transformación al modelo `Game` |
| Almacenamiento persistente del catálogo | Sí | Previsto mediante MySQL |
| Búsqueda contra información almacenada | Sí | Parte del flujo de consulta de DRIFT |
| Actualización de información de PlayStation | Sí | Parte de la estrategia de integración |
| Conservación de información previamente almacenada ante falla externa | Sí | Considerada dentro de la estrategia de integración |
| Publicación de mensajes definidos en AsyncAPI | Sí | Pendiente de implementación |
| Programación automática de actualizaciones | Sí | Pendiente de implementación |
| Control de solicitudes o reintentos ante `429` | Sí | Pendiente de implementación |
| Historial de precios | No | No implementado |


## 6. Capacidades de la integración

La integración con PlayStation permite obtener información de videojuegos mediante PSN Swagger. La información recibida puede ser transformada al modelo interno de DRIFT para ser utilizada por la aplicación.

| Operación | Propósito | Estado |
|---|---|---|
| Buscar videojuegos | Consultar videojuegos mediante la API de PlayStation y obtener la información disponible para el resultado de búsqueda. | Implementado |
| Obtener información comercial | Obtener información disponible sobre precio, moneda y disponibilidad cuando sea proporcionada por PlayStation. | Implementado |
| Normalizar información | Transformar la respuesta de PlayStation al modelo interno de DRIFT. | Implementado |
| Integrar resultados en DRIFT | Incorporar la información obtenida al flujo de búsqueda de videojuegos. | Implementado |
| Actualizar información del catálogo | Obtener nuevamente información desde PlayStation para mantener actualizado el catálogo local. | En desarrollo |
| Persistir información en MySQL | Almacenar la información normalizada para reducir consultas directas al proveedor externo. | Parte de la arquitectura objetivo |
| Actualización periódica | Ejecutar automáticamente procesos de actualización del catálogo. | Pendiente |

## 7. Relación con la estrategia de integración

La integración de PlayStation forma parte de la estrategia híbrida definida en el [**ADR-0004**](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/docs/adr/0004-estrategia-de-integracion.md).

La comunicación con la API externa se realiza mediante HTTP/HTTPS y JSON. La actualización del catálogo se separa del flujo interactivo del usuario para permitir que la información externa sea obtenida y procesada de manera independiente.

Esta estrategia permite reducir la dependencia de la disponibilidad inmediata del proveedor y controlar la frecuencia de las solicitudes externas.

La información obtenida se normaliza antes de incorporarse al modelo interno de DRIFT, manteniendo el dominio desacoplado de las estructuras específicas de PlayStation.

La misma estrategia puede aplicarse posteriormente a otras fuentes externas, como Xbox u otros proveedores, cuando sus características de disponibilidad, límites de solicitudes o costos hagan conveniente una actualización periódica y almacenamiento local.
