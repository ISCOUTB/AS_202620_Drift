# ADR-0005: Estrategia de despliegue de DRIFT

## Estado

Aceptado

## Fecha

2026-09-25

## Contexto

DRIFT es una plataforma web para comparar videojuegos, consultar precios y estimar compatibilidad básica de PC. Actualmente el sistema utiliza una arquitectura hexagonal (Ports and Adapters), con un backend en FastAPI y un frontend en Next.js. El repositorio separa el sistema en `backend/`, `frontend/`, `docs/` y `scripts/`, y ya cuenta con pruebas del backend, compilación de producción del frontend y una prueba de rendimiento de 50 usuarios virtuales sobre `GET /games/search?q=Minecraft`.

Para la entrega de despliegue se requiere que el sistema sea accesible desde fuera de la red de la universidad y que la solución permita evidenciar:

- URL pública del sistema.
- Infraestructura como código (IaC) versionada.
- Pipeline de integración/despliegue en verde.
- Health check.
- Logs estructurados.
- Una métrica consultable.
- Protección de secretos.
- Estimación del costo mensual y sus supuestos.

Además, la solución debe conservar en lo posible la estructura actual del backend FastAPI y permitir continuar con la arquitectura hexagonal sin introducir una migración innecesaria del código de negocio.

## Decisión

Se adopta una estrategia de despliegue dividida en frontend y backend:

- **Frontend:** Netlify.
- **Backend:** Google Cloud Run.
- **Infraestructura como código:** Terraform.
- **CI/CD:** GitHub Actions.
- **Logs:** Google Cloud Logging.
- **Métricas:** Google Cloud Monitoring.
- **Secretos:** Google Secret Manager.
- **Imágenes de contenedor:** Google Artifact Registry.
- **Repositorio de código e infraestructura:** GitHub.

### Frontend

El frontend Next.js se desplegará en Netlify utilizando el directorio `frontend/`. Netlify soporta las características principales de Next.js, incluido App Router, y puede configurar automáticamente la infraestructura necesaria para aplicaciones Next.js.

La configuración prevista es:

- Base directory: `frontend`
- Build command: `npm run build`
- Publish directory: `.next`

La URL pública del frontend será proporcionada por Netlify y posteriormente podrá asociarse a un dominio personalizado si se requiere.

### Backend

El backend FastAPI se desplegará como un servicio de Google Cloud Run.

La aplicación se empaquetará como contenedor y Cloud Run será responsable de ejecutar el servicio HTTP y proporcionar una URL pública. La aplicación mantendrá su estructura interna actual de arquitectura hexagonal; Cloud Run se considera un adaptador de infraestructura y no modifica el dominio ni los casos de uso.

El servicio expondrá, como mínimo, un endpoint de health check que permita comprobar que la instancia está disponible.

### Infraestructura como código

Terraform será utilizado para declarar y versionar la infraestructura de Google Cloud necesaria para el despliegue.

La configuración de infraestructura se almacenará dentro del repositorio, separada del código de aplicación. Como mínimo se contemplará la configuración del servicio de Cloud Run y los recursos de soporte que sean necesarios para el despliegue.

Los archivos de credenciales, tokens, claves privadas y valores secretos no se almacenarán en Git.

### CI/CD

GitHub Actions será utilizado para automatizar la validación y el despliegue.

El pipeline deberá conservar las validaciones existentes del proyecto y añadir las etapas necesarias para construir y desplegar el backend y, cuando corresponda, ejecutar la infraestructura definida mediante Terraform.

El objetivo es que los cambios que lleguen a `master` puedan validarse automáticamente antes de considerarse desplegados.

### Observabilidad

Cloud Logging se utilizará para consultar los registros generados por el backend.

Los registros de aplicación se producirán en formato estructurado cuando sea necesario para facilitar la consulta de campos como nivel, operación, endpoint y resultado.

Cloud Monitoring se utilizará para consultar métricas operativas del servicio, como solicitudes, latencia y errores. La métrica seleccionada para la evidencia de la entrega deberá poder consultarse desde la consola de Google Cloud.

### Secretos

Los secretos necesarios para el backend no se incluirán en el código fuente ni en archivos versionados.

Los secretos de infraestructura y despliegue se administrarán mediante los mecanismos de secretos de Google Cloud y los secretos protegidos de GitHub Actions cuando corresponda.

Las variables públicas necesarias para el frontend, como la URL pública de la API, se tratarán como configuración del cliente y no como secretos.

## Alternativas consideradas

### 1. Render

Permite desplegar el backend FastAPI como un servicio web sin convertir la aplicación a funciones.

**Ventajas:**
- Adaptación pequeña del backend existente.
- Integración sencilla con GitHub.
- URL pública.
- Despliegue de aplicaciones web tradicionales.

**Desventajas:**
- La estrategia de observabilidad e infraestructura queda repartida entre servicios de terceros.
- Se dispone de menos integración nativa con el conjunto de servicios que se utilizará para observabilidad y secretos.
- La solución tendría que documentar por separado varias capacidades operativas.

### 2. Railway

Permite desplegar aplicaciones y contenedores y es compatible con aplicaciones backend como FastAPI.

**Ventajas:**
- Despliegue sencillo.
- Integración con GitHub.
- Adecuado para aplicaciones existentes.

**Desventajas:**
- La solución tendría que integrar por separado los mecanismos de observabilidad, secretos e infraestructura que se requieran.
- El cálculo de costos depende de los recursos consumidos y del plan utilizado.

### 3. AWS Lambda

Es una alternativa FaaS con escalado administrado.

**Ventajas:**
- Modelo serverless.
- Escalado automático.
- Integración amplia con servicios de AWS.
- Buen soporte para infraestructura como código.

**Desventajas:**
- El backend actual es una aplicación FastAPI completa y requiere una adaptación al modelo de ejecución de Lambda/API Gateway.
- Introduce más cambios en la forma de ejecutar la API que un despliegue directo de la aplicación como servicio.
- Aumenta la cantidad de componentes que deben configurarse para exponer la API.

### 4. Azure Functions

Es otra alternativa FaaS que permite ejecutar aplicaciones Python mediante el modelo de Functions.

**Ventajas:**
- Escalado administrado.
- Integración con servicios de Azure.
- Soporte para infraestructura como código.

**Desventajas:**
- Requiere adaptar la aplicación FastAPI al modelo de Functions.
- Añade componentes y configuración adicionales para exponer la API.

### 5. Google Cloud Run

**Ventajas:**
- Permite desplegar una aplicación FastAPI como servicio HTTP sin transformar cada endpoint en una función.
- Es un servicio administrado y basado en contenedores.
- Se integra directamente con Cloud Logging y Cloud Monitoring.
- Se puede administrar mediante Terraform.
- Proporciona una URL pública para el servicio.
- Mantiene una separación clara entre la aplicación y la infraestructura.

**Desventajas:**
- Requiere habilitar facturación en el proyecto de Google Cloud.
- El uso se factura por consumo cuando se superan las cuotas gratuitas.
- Requiere configurar correctamente IAM, despliegue, secretos y recursos de Google Cloud.

## Criterios de decisión

La selección se realizó considerando:

| Criterio | Importancia para DRIFT |
|---|---|
| Mantener FastAPI con pocos cambios | Alta |
| URL pública | Alta |
| Compatibilidad con IaC | Alta |
| CI/CD | Alta |
| Health check | Alta |
| Logs consultables | Alta |
| Métricas consultables | Alta |
| Protección de secretos | Alta |
| Control y estimación de costos | Alta |
| Compatibilidad con la arquitectura hexagonal | Alta |
| Escalabilidad administrada | Media-Alta |

La decisión prioriza una plataforma que permita desplegar la aplicación FastAPI existente como servicio y que concentre las capacidades operativas requeridas por la entrega.

## Costos y supuestos

La solución se diseñará inicialmente para mantenerse dentro de las cuotas gratuitas disponibles y para un volumen de uso correspondiente a una evaluación académica.

Cloud Run ofrece actualmente, para facturación basada en solicitudes y según la región de referencia indicada por Google, una cuota gratuita mensual de 2 millones de solicitudes, 180.000 vCPU-segundos y 360.000 GiB-segundos de memoria. El uso que supere las cuotas gratuitas se factura según las tarifas vigentes de Google Cloud.

La estimación definitiva de costo mensual se documentará en el artefacto de costos de la entrega y deberá indicar:

1. Región utilizada.
2. Memoria asignada al servicio.
3. CPU asignada.
4. Número estimado de solicitudes mensuales.
5. Tiempo promedio de procesamiento.
6. Uso estimado de almacenamiento y registro.
7. Cuotas gratuitas aplicables.
8. Punto a partir del cual se produciría consumo facturable.

La activación de facturación de Google Cloud es un requisito operativo de la plataforma y no se considera equivalente a un costo mensual de consumo del sistema. El costo mensual se calculará a partir del uso real o estimado de los servicios.

## Consecuencias positivas

- El frontend y el backend quedan desacoplados y pueden desplegarse independientemente.
- FastAPI puede conservar su estructura actual.
- La arquitectura hexagonal no depende de una plataforma FaaS específica.
- Terraform permite versionar la infraestructura.
- GitHub Actions permite automatizar validaciones y despliegues.
- Cloud Logging y Cloud Monitoring proporcionan una ruta directa para las evidencias de observabilidad.
- Secret Manager permite separar secretos de la configuración versionada.
- Cloud Run proporciona una URL pública para que el evaluador pueda acceder a la API desde fuera de la universidad.
- La solución permite documentar explícitamente los supuestos y límites de costo.

## Consecuencias negativas y riesgos

- Se introduce dependencia operativa de Google Cloud para el backend y de Netlify para el frontend.
- Es necesario configurar correctamente facturación, IAM y permisos.
- El sistema queda sujeto a las cuotas gratuitas y precios vigentes de los proveedores.
- La primera configuración de Cloud Run, Terraform y autenticación de GitHub Actions tiene una complejidad mayor que un despliegue manual sencillo.
- Será necesario configurar CORS para permitir la comunicación entre el frontend desplegado en Netlify y la API desplegada en Cloud Run.
- La URL pública del backend deberá tratarse como configuración del frontend y mantenerse separada de secretos.

## Relación con la arquitectura actual

La decisión no modifica la arquitectura hexagonal del backend.

La estructura de negocio continúa siendo:

`Frontend → API REST → casos de uso → puertos del dominio → adaptadores`

El despliegue añade infraestructura alrededor de esta estructura:

`Netlify → HTTPS → Cloud Run → FastAPI → adaptadores externos`

Por tanto, la decisión de infraestructura queda separada de las decisiones anteriores sobre arquitectura hexagonal y sobre la utilización de Next.js y FastAPI.

## Plan de implementación

1. Crear/configurar el proyecto de Google Cloud y habilitar los servicios necesarios.
2. Añadir el `Dockerfile` del backend.
3. Crear la infraestructura Terraform.
4. Configurar permisos y autenticación segura para CI/CD.
5. Configurar Secret Manager y variables de entorno.
6. Desplegar el backend en Cloud Run.
7. Implementar/verificar el health check.
8. Configurar logs estructurados.
9. Seleccionar y consultar una métrica operativa.
10. Configurar Netlify para el frontend.
11. Configurar la URL de Cloud Run como variable de entorno del frontend.
12. Configurar CORS.
13. Ejecutar el pipeline completo.
14. Registrar las evidencias de URL pública, pipeline, health check, logs, métrica, secretos y costos.

## Estado de implementación

La decisión de plataforma está aceptada. La infraestructura y los despliegues descritos en este ADR se implementarán progresivamente como parte de la entrega de despliegue.

## Referencias

- Documentación oficial de Google Cloud Run para aplicaciones FastAPI.
- Documentación oficial de precios de Cloud Run.
- Documentación oficial del provider de Google Cloud para Terraform.
- Documentación oficial de Netlify para Next.js.
- Repositorio de DRIFT y documentación arquitectónica existente.
