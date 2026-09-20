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
- **Especificaciones:** OpenAPI 3.0.3 para la integración REST y AsyncAPI 3.0 para el flujo de actualización.
- **Versionado:** `1.0.0`.

Los contratos ejecutables se mantienen separados de este documento:

- **Contrato REST:** `docs/api/playstation/openapi.yaml`
- **Contrato asíncrono:** `docs/api/playstation/asyncapi.yaml`

La documentación de referencia de la API externa se encuentra en [PSN Swagger](https://olegshulyakov.github.io/psn-swagger/).

### Flujo general

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

El contrato REST de la integración se encuentra definido en:

`docs/api/playstation/openapi.yaml`

El contrato está basado en la operación `GetGame` documentada por PSN Swagger:

```
GET /store/api/chihiro/00_09_000/container/{country}/{language}/{age}/{cusa}
```

La operación utiliza los siguientes parámetros obligatorios de ruta:

- `country`: código de país de dos caracteres.
- `language`: código de idioma de dos caracteres.
- `age`: edad del usuario.
- `cusa`: código CUSA del videojuego.

También contempla parámetros opcionales para filtros y ordenamiento, entre ellos `size`, `start`, `sort`, `direction`, `gameContentType`, `subtitleLang`, `releaseDate`, `gameDemo`, `price`, `genre`, `topCategory`, `voiceLang`, `game_type`, `relationship` y `platform`.

La respuesta exitosa utiliza JSON y contiene información del videojuego. Entre los datos disponibles se encuentra el precio dentro de:

`links[].default_sku.price`

También puede utilizarse `links[].default_sku.display_price` para la representación del precio mostrada por el proveedor.

El contrato documenta las respuestas HTTP `200`, `400` y `404`.

## 4. Contrato asíncrono

El contrato asíncrono del proceso de actualización del catálogo se encuentra definido en:

`docs/api/playstation/asyncapi.yaml`

Este contrato representa el flujo lógico de actualización independiente de las consultas interactivas de los usuarios.

| Mensaje | Tipo | Cuándo se produce |
| ------- | ---- | ------------------ |
| `UpdateRequested` | Comando | Se solicita iniciar una actualización del catálogo de PlayStation. |
| `GameCaptured` | Evento | Un videojuego fue obtenido, normalizado y preparado para almacenamiento. |
| `UpdateCompleted` | Evento | La actualización terminó correctamente. |
| `UpdateFailed` | Evento | La actualización presentó un error; la información previamente almacenada se conserva. |

El contrato define la estructura de estos mensajes, pero el mecanismo concreto de transporte, mensajería o programación será definido durante la implementación.

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
| --------- | --------- | ------ |
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


## 8. Historial de versiones

| Versión | Fecha | Descripción |
|---|---|---|
| 1.0.0 | 2026-09-19 | Versión inicial de los contratos de integración REST y asíncrono con PlayStation. |
