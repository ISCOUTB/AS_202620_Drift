# ADR-0004: Estrategia híbrida de integración con fuentes externas

- **Estado:** Aceptado
- **Fecha:** 2026-09-19
- **Decisores:** Equipo DRIFT

## Contexto

DRIFT necesita integrar información proveniente de fuentes externas de videojuegos, como PlayStation y otras plataformas. Estas fuentes pueden presentar diferencias en disponibilidad, límites de solicitudes, tiempos de respuesta y, potencialmente, costos de consumo.

El sistema también necesita permitir que los usuarios consulten videojuegos y precios sin depender directamente de la disponibilidad de cada proveedor externo en el momento de la consulta.

El atributo de calidad prioritario del proyecto es la **mantenibilidad**. Por ello, la estrategia de integración debe mantener aisladas las dependencias externas y permitir modificar o incorporar fuentes sin afectar directamente al dominio de DRIFT.

Además, la actualización del catálogo no requiere necesariamente una respuesta inmediata al usuario. La información puede ser obtenida periódicamente, normalizada y almacenada en **MySQL** para ser utilizada posteriormente durante las consultas.

## Decisión

Se adopta una **estrategia híbrida de integración**:

1. Las operaciones que requieren respuesta inmediata al usuario utilizarán comunicación síncrona mediante **HTTP/REST y JSON**.
2. La actualización periódica de información proveniente de fuentes externas se gestionará mediante un flujo **asíncrono**.
3. La información obtenida de las fuentes externas será normalizada antes de incorporarse al modelo interno de DRIFT.
4. La información obtenida será almacenada de forma persistente en **MySQL**, funcionando como fuente local para las consultas de los usuarios y como mecanismo de desacoplamiento frente a los proveedores externos.
5. Cada fuente externa será encapsulada mediante un adaptador, evitando que el dominio dependa directamente de la API del proveedor.
6. Las actualizaciones del catálogo se podrán ejecutar de forma programada, evitando realizar solicitudes a las fuentes externas en cada búsqueda realizada por los usuarios.

## Alternativas consideradas

### Alternativa 1: Integración completamente síncrona

Todas las consultas y actualizaciones se realizarían directamente contra las APIs externas.

**Ventajas:**

- Flujo sencillo.
- No requiere un mecanismo de procesamiento asíncrono.
- La información consultada podría obtenerse directamente del proveedor.

**Consecuencias:**

- Las consultas dependerían de la disponibilidad del proveedor.
- Cada consulta podría generar una solicitud externa.
- Los límites de solicitudes del proveedor afectarían directamente a DRIFT.
- Un proveedor lento aumentaría el tiempo de respuesta para el usuario.
- Los posibles costos de consumo serían más difíciles de controlar.

### Alternativa 2: Integración completamente asíncrona

Toda comunicación con las fuentes externas se realizaría mediante procesos y eventos asíncronos.

**Ventajas:**

- Mayor desacoplamiento temporal.
- Las actualizaciones pueden ejecutarse independientemente de las consultas.
- Facilita procesos periódicos de actualización.

**Consecuencias:**

- Añade complejidad para operaciones que requieren respuesta inmediata.
- Requiere mecanismos adicionales para gestionar eventos, estados y errores.
- No resulta necesario utilizar comunicación asíncrona para una consulta interactiva que necesita una respuesta inmediata.

### Alternativa 3: Estrategia híbrida

Las consultas del usuario utilizan HTTP/REST de forma síncrona, mientras que las actualizaciones de información externa se ejecutan mediante procesos asíncronos y almacenan los resultados normalizados en MySQL.

**Consecuencias:**

- Se mantiene una interacción directa y sencilla para las consultas.
- Las actualizaciones pueden ejecutarse de manera independiente.
- Se reduce la dependencia temporal de las APIs externas.
- Se pueden controlar mejor la frecuencia de solicitudes y los límites de consumo.
- Los adaptadores mantienen aisladas las particularidades de cada proveedor.
- Se introduce una mayor complejidad que una integración completamente síncrona debido al proceso de actualización y almacenamiento.

## Escenario de calidad relacionado

La decisión responde principalmente al escenario **E2 de mantenibilidad**.

Cuando DRIFT necesite incorporar una nueva fuente de información o modificar la integración con un proveedor existente, la dependencia específica del proveedor estará encapsulada en su adaptador y el resto del sistema podrá continuar utilizando el modelo interno de DRIFT.

La separación entre las consultas de los usuarios y la actualización de fuentes externas también permite modificar la frecuencia o el mecanismo de actualización sin modificar el flujo principal de búsqueda.

Esta separación facilita que una modificación en la API de un proveedor quede localizada principalmente en su adaptador y en el proceso de actualización correspondiente, reduciendo el impacto sobre el dominio y los demás componentes de DRIFT.

## Consecuencias

### Positivas

- Menor acoplamiento entre el dominio y los proveedores externos.
- Las consultas de los usuarios no dependen directamente de la disponibilidad de las APIs externas.
- Permite controlar la frecuencia de actualización del catálogo.
- Facilita incorporar nuevas fuentes.
- Permite conservar información obtenida anteriormente cuando un proveedor no está disponible.
- Mantiene HTTP/REST como mecanismo sencillo para las operaciones interactivas.
- Permite centralizar la información normalizada de diferentes fuentes en MySQL.
- Facilita controlar el consumo de APIs externas que puedan tener límites o costos asociados.

### Negativas

- Se requiere almacenamiento persistente en MySQL para conservar la información obtenida.
- La información almacenada puede no representar el estado más reciente del proveedor.
- El sistema debe gestionar la frecuencia de actualización del catálogo.
- El procesamiento asíncrono requiere mecanismos adicionales para programar, ejecutar y controlar las actualizaciones.
- El sistema debe gestionar errores durante las actualizaciones y mantener la consistencia de la información almacenada.
- Se introduce un desfase potencial entre la información disponible en DRIFT y la información actual del proveedor externo.

## Flujo de integración

La estrategia definida separa el flujo interactivo del usuario del proceso de actualización de las fuentes externas.

### Consulta del usuario

```text
Usuario
   |
   | HTTP/REST + JSON
   v
Frontend Next.js
   |
   | HTTP/REST + JSON
   v
Backend FastAPI
   |
   | Consulta
   v
MySQL
   |
   | Datos normalizados
   v
Backend FastAPI
   |
   | HTTP/REST + JSON
   v
Frontend Next.js
   |
   v
Usuario
```

### Actualización del catálogo

```text
Scheduler / proceso programado
            |
            v
   Solicitud de actualización
            |
            v
    Adaptador de fuente externa
            |
            | HTTP/HTTPS + JSON
            v
       API externa
            |
            | Respuesta
            v
       Normalización
            |
            v
          MySQL
```

La actualización puede ejecutarse en un horario definido por el sistema, obteniendo la mayor cantidad de información disponible de las fuentes externas y almacenándola en MySQL.

## Relación con la arquitectura

La estrategia mantiene la arquitectura hexagonal de DRIFT.

Las APIs externas son accedidas mediante adaptadores de infraestructura que implementan los puertos definidos por el dominio. La información obtenida se transforma al modelo interno antes de ser almacenada o utilizada por el resto del sistema.

MySQL pertenece a la infraestructura de persistencia y permite que los casos de uso de DRIFT trabajen con información almacenada localmente sin depender directamente de las APIs externas.

La comunicación entre el frontend y el backend continúa utilizando HTTP/REST y JSON, mientras que el proceso de actualización del catálogo se desacopla temporalmente mediante el flujo asíncrono.

## Relación con los contratos de API

La estrategia se refleja en los contratos definidos para DRIFT:

- **OpenAPI:** describe las operaciones HTTP/REST síncronas expuestas por el backend de DRIFT.
- **OpenAPI de integración:** describe las interacciones HTTP/REST con las fuentes externas.
- **AsyncAPI:** describe los mensajes asociados al proceso asíncrono de actualización del catálogo.

Los contratos permiten separar la comunicación interactiva de los usuarios de los procesos de actualización de información externa.

## Estado de implementación

Aceptado como estrategia arquitectónica.

La decisión establece la estrategia objetivo de integración de DRIFT. La implementación concreta del mecanismo de programación, procesamiento asíncrono, persistencia en MySQL y mensajería se incorporará progresivamente.
