# ADR-0005: Estrategia de despliegue de la API REST de DRIFT

**Estado:** Propuesto
**Fecha:** 2026-09-25

## Contexto

DRIFT es una plataforma web para comparar videojuegos, precios y compatibilidad con PC. El sistema utiliza una arquitectura hexagonal, con un backend desarrollado en FastAPI y un frontend desarrollado en Next.js.

Para esta decisión se considera únicamente una pieza concreta del sistema: **la API REST de DRIFT**, responsable de exponer los servicios del backend y atender las solicitudes realizadas por el frontend.

La API actualmente dispone de pruebas automatizadas y de una prueba de rendimiento para el escenario E1, utilizando 50 usuarios virtuales sobre el endpoint:

`GET /games/search?q=Minecraft`

La condición operativa E1 establece como referencia un máximo de **50 usuarios concurrentes** y un **p95 menor o igual a 3 segundos**.

La entrega requiere comparar dos alternativas de despliegue para esta pieza, considerando rendimiento, disponibilidad de la plataforma, costos, restricciones de tarjeta, observabilidad, reproducibilidad y posibilidad de reversión.

La API debe conservar su implementación en FastAPI y su arquitectura hexagonal, evitando cambios importantes en el dominio y en los casos de uso.

## Decisión

Se compararán dos alternativas de despliegue para la **API REST de DRIFT**:

1. **Alternativa A: Google Cloud Run**
2. **Alternativa B: Render**

Las dos alternativas serán evaluadas utilizando el mismo escenario E1 y, en lo posible, las mismas condiciones de prueba.

La comparación tendrá como mínimo los siguientes criterios:

* p95 obtenido con 50 usuarios concurrentes.
* Cantidad de errores durante la prueba.
* Cumplimiento del p95 objetivo de 3 segundos.
* Tiempo de respuesta observado.
* Facilidad de despliegue.
* Compatibilidad con FastAPI.
* Necesidad o no de tarjeta bancaria.
* Capa gratuita disponible.
* Punto en el que la capa gratuita deja de ser suficiente.
* Costo mensual estimado.
* Facilidad para consultar logs y métricas.
* Reproducibilidad del despliegue.
* Procedimiento de reversión.

La alternativa seleccionada será aquella que, de acuerdo con las mediciones y evidencias obtenidas, resulte más adecuada para las condiciones operativas y restricciones establecidas para la entrega.

## Alternativa A: Google Cloud Run

Google Cloud Run permite desplegar la API FastAPI como un contenedor HTTP, manteniendo la estructura actual del backend.

La implementación requiere:

* Dockerfile para el backend.
* Imagen del backend.
* Servicio de Cloud Run.
* URL HTTP pública.
* Configuración de variables de entorno.
* Configuración de secretos cuando corresponda.
* Terraform para infraestructura reproducible.
* GitHub Actions para automatizar validaciones y despliegue.
* Cloud Logging para logs.
* Cloud Monitoring para métricas.

Esta alternativa permite mantener el modelo actual de ejecución de FastAPI sin convertir la aplicación en funciones individuales.

### Costos

El costo será calculado considerando:

* Región utilizada.
* CPU asignada.
* Memoria asignada.
* Número de solicitudes mensuales.
* Tiempo promedio de procesamiento.
* Consumo de almacenamiento.
* Consumo de logs.
* Cuotas gratuitas aplicables.

Se documentará explícitamente el punto en el que el consumo supera la capa gratuita y comienza a generar cobro.

La activación de facturación y las condiciones de la cuenta deberán quedar documentadas antes del despliegue.

## Alternativa B: Render

Render permite desplegar la API FastAPI como un servicio web, manteniendo la implementación actual del backend y sin modificar la lógica de dominio de la aplicación.

La implementación requiere:

* Configuración del servicio web en Render.
* Repositorio conectado con el proyecto.
* Comando de construcción cuando corresponda.
* Comando de inicio del servidor FastAPI.
* URL HTTP pública.
* Configuración de variables de entorno.
* Configuración de secretos cuando corresponda.
* Configuración de health check.
* Logs proporcionados por la plataforma.
* Configuración necesaria para reproducir el despliegue.

La API deberá conservar FastAPI y la arquitectura hexagonal. Cualquier configuración específica de Render deberá mantenerse separada de la lógica de negocio.

### Costos

El costo será calculado considerando:

* Tipo de servicio utilizado.
* Recursos asignados.
* Horas de ejecución.
* Número de solicitudes cuando aplique.
* Consumo de almacenamiento.
* Límites de la capa gratuita.
* Restricciones de la plataforma.

Se documentará explícitamente el punto en el que el consumo supera la capa gratuita y comienza a generar cobro.

La necesidad de tarjeta bancaria y las condiciones de facturación deberán quedar documentadas antes del despliegue.

## Prototipo y medición

Para comparar las alternativas se utilizará el escenario **E1**.

### Condición de prueba

* Usuarios concurrentes: **50**
* Endpoint: `GET /games/search?q=Minecraft`
* Métrica principal: **p95**
* Objetivo: **p95 ≤ 3 segundos**

Se utilizará el mismo script de k6 para ambas alternativas.

La prueba se ejecutará sobre una API desplegada en cada plataforma y se registrarán como mínimo:

| Métrica                |    Alternativa A |  Alternativa B |
| ---------------------- | ---------------: | -------------: |
| Usuarios concurrentes  |               50 |             50 |
| p95                    |        Por medir |      Por medir |
| Errores                |        Por medir |      Por medir |
| Cumple E1              |   Por determinar | Por determinar |
| URL pública            |               Sí | Por determinar |
| Tarjeta requerida      | Sí/Por confirmar |  Por confirmar |
| Costo mensual estimado |     Por calcular |   Por calcular |

Los resultados deberán quedar almacenados como evidencia reproducible dentro del repositorio.

## Criterio de comparación

La comparación no se realizará únicamente con base en la existencia de una capa gratuita.

Se considerará conjuntamente:

1. Cumplimiento del p95 establecido por E1.
2. Tasa de errores.
3. Compatibilidad con la API existente.
4. Reproducibilidad del despliegue.
5. Observabilidad.
6. Restricción de tarjeta.
7. Costo estimado.
8. Facilidad de reversión.

Los resultados medidos serán los que sustenten la decisión final del ADR.

## Infraestructura como código

El despliegue deberá poder reproducirse mediante infraestructura como código cuando la plataforma seleccionada lo permita.

Para Google Cloud Run se utilizará Terraform para definir los recursos necesarios.

La infraestructura y configuración deberán mantenerse versionadas en el repositorio.

No se almacenarán secretos directamente en el código fuente.

## CI/CD

GitHub Actions será utilizado para ejecutar las validaciones necesarias antes del despliegue.

El pipeline deberá permitir:

1. Ejecutar pruebas.
2. Validar el proyecto.
3. Construir la imagen cuando corresponda.
4. Desplegar la API.
5. Verificar que el servicio esté disponible.

El despliegue no deberá depender de cambios manuales no documentados.

## Health check

La API deberá disponer de un endpoint de salud que permita comprobar que el servicio está disponible.

Se utilizará el endpoint:

`GET /`

como comprobación básica de disponibilidad.

La respuesta deberá permitir diferenciar entre un servicio disponible y un despliegue que no inició correctamente.

## Observabilidad

Para cada alternativa se documentarán los mecanismos disponibles para consultar:

* Solicitudes.
* Errores.
* Latencia.
* Estado del servicio.
* Logs de la aplicación.

Cuando la plataforma lo permita, se utilizarán logs estructurados y métricas consultables.

La métrica principal relacionada con el escenario E1 será la latencia, especialmente el valor p95.

## Reversión

El procedimiento de reversión deberá permitir regresar a la versión anterior de la API si un despliegue presenta errores o incumple las condiciones operativas.

El procedimiento será:

1. Identificar la versión que presenta el problema.
2. Detener o retirar la versión problemática.
3. Volver a desplegar la versión anterior conocida como funcional.
4. Ejecutar el health check `GET /`.
5. Ejecutar nuevamente una prueba básica de la API.
6. Registrar el resultado de la reversión.

Cuando la plataforma permita mantener versiones o revisiones del servicio, se utilizará la revisión anterior para facilitar el rollback.

## Consecuencias

### Positivas

* La decisión se concentra en una pieza concreta: la API REST.
* Se conserva FastAPI y la arquitectura hexagonal.
* Las dos alternativas pueden compararse bajo el mismo escenario E1.
* Se obtiene evidencia mediante pruebas reales de despliegue.
* Se incorpora el análisis de costos.
* Se considera explícitamente la restricción de tarjeta.
* Se establece un procedimiento de reversión.
* El despliegue puede integrarse con CI/CD.

### Negativas

* Será necesario mantener y probar dos despliegues.
* Las plataformas pueden tener diferencias en observabilidad y configuración.
* La medición de costos depende de los supuestos de tráfico y consumo.
* Una de las alternativas puede requerir adaptaciones de configuración.
* Las capas gratuitas y sus restricciones deben verificarse antes de realizar la estimación final.

## Relación con la arquitectura

Esta decisión no modifica la arquitectura interna de DRIFT.

La API mantiene el flujo:

`Frontend → API REST → Casos de uso → Puertos del dominio → Adaptadores`

La decisión únicamente modifica la infraestructura utilizada para ejecutar la API REST.

La arquitectura hexagonal continúa aislando la lógica de negocio de los mecanismos concretos de infraestructura y despliegue.

## Plan de implementación

1. Seleccionar definitivamente las dos plataformas.
2. Verificar las condiciones de uso y restricciones de tarjeta.
3. Preparar el despliegue de la API REST.
4. Configurar el health check.
5. Preparar la infraestructura como código cuando corresponda.
6. Configurar las variables de entorno y secretos.
7. Desplegar la API en la primera alternativa.
8. Ejecutar la prueba E1 con 50 usuarios concurrentes.
9. Registrar p95 y errores.
10. Desplegar la API en la segunda alternativa.
11. Ejecutar exactamente la misma prueba.
12. Registrar p95 y errores.
13. Estimar los costos mensuales.
14. Identificar el punto de ruptura de la capa gratuita.
15. Documentar el procedimiento de reversión.
16. Incorporar las evidencias al repositorio.
17. Actualizar este ADR con los resultados obtenidos.
18. Cambiar el estado del ADR a **Aceptado** una vez tomada la decisión.

## Evidencias esperadas

La entrega deberá incluir evidencia de:

* API desplegada públicamente.
* Health check funcionando.
* Prueba E1 ejecutada.
* Resultado de p95.
* Errores obtenidos.
* Comparación de las dos alternativas.
* Estimación de costos.
* Punto de ruptura de la capa gratuita.
* Procedimiento de reversión.
* Configuración reproducible del despliegue.
* Ejecución del pipeline de CI/CD cuando corresponda.

## Estado de la decisión

Este ADR se encuentra **Propuesto** mientras se realizan las pruebas de las dos alternativas.

Una vez obtenidas las mediciones y seleccionada la alternativa de despliegue para la API REST, se actualizará el estado a **Aceptado** y se incorporarán los resultados reales de las pruebas.

## Referencias

* `docs/escenarios.md`
* `docs/evidencias/e1-linea-base.md`
* `docs/api/drift/openapi.yaml`
* `scripts/k6_baseline.js`

* Infraestructura como código utilizada para el despliegue.
* Evidencias de ejecución de las pruebas.
