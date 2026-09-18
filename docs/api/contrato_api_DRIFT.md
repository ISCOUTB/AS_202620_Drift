# Contrato de API DRIFT

> **Qué es este documento:** borrador del contrato de la API de DRIFT. Describe cómo se comunican el frontend, el backend y las fuentes externas para buscar videojuegos y estimar compatibilidad de PC.
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
- **Versionado propuesto:** `1.0.0`.
- **Fuente externa real:** Steam.
- **Respaldo:** catálogo local en memoria cuando Steam no está disponible.

La integración es síncrona porque la búsqueda de videojuegos y la compatibilidad necesitan una respuesta inmediata para mostrarse al usuario en la interfaz.

## 3. Contrato síncrono REST

```yaml
openapi: 3.1.0

info:
  title: DRIFT API
  version: 1.0.0
  description: |
    Contrato HTTP de la API de DRIFT.
    Permite buscar videojuegos, consultar el estado del servicio
    y estimar la compatibilidad de un juego con un computador.

servers:
  - url: http://localhost:8000
    description: Entorno local

tags:
  - name: Estado
    description: Verificación de disponibilidad de la API.
  - name: Juegos
    description: Búsqueda y consulta de videojuegos.
  - name: Compatibilidad
    description: Estimación de compatibilidad de PC.

paths:
  /:
    get:
      tags:
        - Estado
      summary: Consultar estado de la API
      operationId: getHealthStatus
      responses:
        "200":
          description: La API está disponible.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/HealthResponse"
              example:
                status: ok

  /games/search:
    get:
      tags:
        - Juegos
      summary: Buscar videojuegos por nombre
      operationId: searchGames
      parameters:
        - name: q
          in: query
          required: true
          description: Texto a buscar. Debe tener al menos un carácter.
          schema:
            type: string
            minLength: 1
          example: Portal 2
      responses:
        "200":
          description: Lista de videojuegos encontrados.
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: "#/components/schemas/GameSearchResult"
              example:
                - id: 620
                  name: Portal 2
                  prices:
                    Steam: 26000.0
                  unavailable_sources: []
        "422":
          description: Parámetro de búsqueda ausente o inválido.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ValidationError"

  /games/{game_id}/compatibility:
    post:
      tags:
        - Compatibilidad
      summary: Estimar compatibilidad de un juego con un PC
      operationId: estimateCompatibility
      parameters:
        - name: game_id
          in: path
          required: true
          description: Identificador del videojuego.
          schema:
            type: integer
          example: 620
      requestBody:
        required: true
        description: Capacidades principales del computador del usuario.
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/CompatibilityRequest"
            example:
              ram_gb: 16
              gpu_score: 80
      responses:
        "200":
          description: Resultado de la estimación o aviso de requisitos no disponibles.
          content:
            application/json:
              schema:
                oneOf:
                  - $ref: "#/components/schemas/CompatibilityResult"
                  - $ref: "#/components/schemas/RequirementsUnavailable"
              examples:
                compatible:
                  summary: Equipo compatible
                  value:
                    game_id: 620
                    status: Compatible
                    minimum_ram_gb: 4
                    recommended_ram_gb: 8
                    minimum_gpu_score: 30
                    recommended_gpu_score: 60
                unavailable:
                  summary: Juego sin requisitos registrados
                  value:
                    game_id: 999999
                    status: Requisitos no disponibles
        "422":
          description: Cuerpo de solicitud o identificador inválido.
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ValidationError"

components:
  schemas:
    HealthResponse:
      type: object
      required:
        - status
      properties:
        status:
          type: string
          example: ok

    GameSearchResult:
      type: object
      required:
        - id
        - name
        - prices
        - unavailable_sources
      properties:
        id:
          type: integer
          description: Identificador del videojuego.
          example: 620
        name:
          type: string
          description: Nombre del videojuego.
          example: Portal 2
        prices:
          type: object
          description: Precios encontrados, indexados por plataforma.
          additionalProperties:
            type: number
          example:
            Steam: 26000.0
        unavailable_sources:
          type: array
          description: Fuentes que no estuvieron disponibles durante la búsqueda.
          items:
            type: string
          example: []

    CompatibilityRequest:
      type: object
      required:
        - ram_gb
        - gpu_score
      properties:
        ram_gb:
          type: integer
          description: Memoria RAM disponible en GB.
          example: 16
        gpu_score:
          type: integer
          description: Puntaje de GPU utilizado por DRIFT para estimar compatibilidad.
          example: 80

    CompatibilityResult:
      type: object
      required:
        - game_id
        - status
        - minimum_ram_gb
        - recommended_ram_gb
        - minimum_gpu_score
        - recommended_gpu_score
      properties:
        game_id:
          type: integer
          example: 620
        status:
          type: string
          enum:
            - Compatible
            - Compatible con limitaciones
            - No compatible
          example: Compatible
        minimum_ram_gb:
          type: integer
          example: 4
        recommended_ram_gb:
          type: integer
          example: 8
        minimum_gpu_score:
          type: integer
          example: 30
        recommended_gpu_score:
          type: integer
          example: 60

    RequirementsUnavailable:
      type: object
      required:
        - game_id
        - status
      properties:
        game_id:
          type: integer
          example: 999999
        status:
          type: string
          const: Requisitos no disponibles

    ValidationError:
      type: object
      description: Respuesta estándar de FastAPI ante datos inválidos.
      properties:
        detail:
          type: array
          items:
            type: object
```

## 4. Contratos asíncronos

DRIFT no tiene contratos asíncronos implementados actualmente.

La versión actual no usa eventos, colas de mensajería, Kafka, RabbitMQ ni AsyncAPI. La búsqueda y la estimación de compatibilidad se ejecutan de forma síncrona porque el usuario necesita recibir una respuesta inmediata en la interfaz.

Como posible evolución futura, el sistema podría publicar eventos relacionados con actualizaciones de precios o indisponibilidad de una fuente externa. Sin embargo, estos eventos no forman parte de la implementación actual y no deben presentarse como funcionalidades terminadas.

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
| Integración real con Epic, Xbox, PlayStation u otras fuentes | No | No |
| Eventos o contratos AsyncAPI | No | No |

## 6. Endpoints propuestos para futuros incrementos

| Endpoint propuesto | Propósito | Estado |
|---|---|---|
| `GET /games/{game_id}` | Consultar detalle de un videojuego. | Pendiente |
| `GET /games/{game_id}/requirements` | Consultar requisitos mínimos y recomendados. | Pendiente |
| `GET /games/{game_id}/prices/history` | Consultar historial de precios. | Pendiente |
| `GET /platforms` | Consultar fuentes o plataformas disponibles. | Pendiente |
| `POST /users/devices` | Registrar especificaciones de un PC. | Pendiente |
| `GET /recommendations` | Obtener recomendaciones personalizadas. | Pendiente |


