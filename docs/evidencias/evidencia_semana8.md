# Evidencia técnica — S8

## 1. URL del sistema accesible desde fuera de la red de la universidad

### Objetivo

Verificar que el backend de DRIFT se encuentra desplegado y accesible públicamente desde Internet, fuera del entorno local de desarrollo y de la red de la universidad.

### Sistema desplegado

El backend de DRIFT se encuentra desplegado en **Azure App Service** y cuenta con la siguiente URL pública:

**URL:**

https://drift-utb-202620-g5fvchdcgpcthkeg.mexicocentral-01.azurewebsites.net

### Resultado de la comprobación

Al acceder a la URL pública desde un navegador se obtuvo una respuesta exitosa:

```json
{
  "status": "ok"
}
```

**Código de respuesta:** HTTP 200 OK

**Fecha de comprobación:** 27/09/2026

**Hora de comprobación:** `[8:10 pm]`

La respuesta `{"status":"ok"}` confirma que el servicio se encuentra disponible y puede ser consultado mediante su URL pública.

---

# 2. Health check consultable

## Objetivo

Verificar que el sistema cuenta con un endpoint de comprobación de disponibilidad que permita determinar si el backend se encuentra funcionando correctamente.

## Endpoint

El backend expone el siguiente endpoint:

```text
GET /health
```

**URL completa:**

[https://drift-utb-202620-g5fvchdcgpcthkeg.mexicocentral-01.azurewebsites.net/health](https://drift-utb-202620-g5fvchdcgpcthkeg.mexicocentral-01.azurewebsites.net/health)

## Resultado de la comprobación

La solicitud al endpoint `/health` produjo la siguiente respuesta:

```json
{
  "status": "ok"
}
```

**Código de respuesta:** HTTP 200 OK

**Fecha de comprobación:** 27/09/2026

**Hora de comprobación:** `[8:30 pm]`

La respuesta HTTP 200 y el contenido `{"status":"ok"}` permiten comprobar que el backend se encuentra disponible y respondiendo correctamente.

---

# 3. Infraestructura como código versionada en el repositorio

## Objetivo

Demostrar que la infraestructura utilizada para desplegar el backend de DRIFT se encuentra definida como código y versionada dentro del repositorio del proyecto.

## Tecnología utilizada

La infraestructura de Azure se define mediante **Azure Bicep**.

Los archivos se encuentran dentro de la siguiente ruta del repositorio:

```text
infra/azure/
```

La estructura relevante es:

```text
infra/
└── azure/
    ├── main.bicep
    ├── main.parameters.json
    └── README.md
```

## Archivo principal de infraestructura

El archivo:

```text
infra/azure/main.bicep
```

contiene la definición de los recursos de Azure utilizados por el backend.

La infraestructura documentada incluye:

* Plan Linux de Azure App Service.
* SKU F1 (Free).
* Región `Mexico Central`.
* Backend `drift-utb-202620`.
* Python 3.12.
* Inicio mediante `bash startup.sh`.
* HTTPS obligatorio.
* FTPS solamente.
* TLS mínimo 1.2.
* Variables públicas necesarias para compilación y CORS.

## Archivo de parámetros

Los valores utilizados para el despliegue se encuentran separados en:

```text
infra/azure/main.parameters.json
```

Este archivo contiene los parámetros necesarios para realizar el despliegue de la infraestructura.

## Documentación de la infraestructura

La carpeta también contiene:

```text
infra/azure/README.md
```

Este archivo documenta los recursos utilizados y el procedimiento para reproducir la infraestructura mediante Azure CLI.

El procedimiento documentado utiliza el siguiente comando:

```powershell
az deployment group create `
  --resource-group rg-drift-as202620 `
  --template-file infra/azure/main.bicep `
  --parameters @infra/azure/main.parameters.json
```

El README indica que este procedimiento requiere Azure CLI autenticado y permisos sobre el grupo de recursos. También especifica que la carpeta de infraestructura no contiene secretos. ([GitHub][1])

La existencia de los archivos `main.bicep`, `main.parameters.json` y `README.md` dentro del repositorio permite mantener la infraestructura versionada junto con el código del proyecto y reproducir el entorno mediante código.

## Enlaces de verificación

* [Repositorio de DRIFT](https://github.com/ISCOUTB/AS_202620_Drift)
* [Archivo `main.bicep`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/infra/azure/main.bicep)
* [Archivo `main.parameters.json`](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/infra/azure/main.parameters.json)
* [README de infraestructura Azure](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/infra/azure/README.md)

---

# 4. El entorno se puede recrear siguiendo el README

## Objetivo

Demostrar que el entorno de infraestructura utilizado para desplegar el backend de DRIFT puede ser reproducido a partir de los archivos versionados en el repositorio y siguiendo las instrucciones documentadas.

## Documentación

El procedimiento de recreación de la infraestructura se encuentra documentado en:

```text
infra/azure/README.md
```

El README indica que la infraestructura corresponde al backend de DRIFT desplegado en Azure App Service y documenta los recursos utilizados.

Entre los recursos y configuraciones documentados se encuentran:

* Plan Linux de Azure App Service.
* SKU F1 (Free).
* Región Mexico Central.
* Backend `drift-utb-202620`.
* Python 3.12.
* Inicio mediante `bash startup.sh`.
* HTTPS obligatorio.
* FTPS solamente.
* TLS mínimo 1.2.
* Variables públicas necesarias para compilación y CORS.

El README también indica que el código se despliega mediante:

```text
.github/workflows/master_drift-utb-202620.yml
```

Además, especifica que los secretos de autenticación OIDC permanecen almacenados en GitHub Actions y no se incluyen en el repositorio ni en los archivos Bicep. ([GitHub][1])

## Comando de reproducción

Con Azure CLI autenticado y permisos sobre el grupo de recursos, se puede ejecutar:

```powershell
az deployment group create `
  --resource-group rg-drift-as202620 `
  --template-file infra/azure/main.bicep `
  --parameters @infra/azure/main.parameters.json
```

Este comando utiliza el template Bicep y el archivo de parámetros versionados en el repositorio para realizar el despliegue.

## Archivos necesarios

La recreación utiliza los siguientes archivos:

```text
infra/
└── azure/
    ├── main.bicep
    ├── main.parameters.json
    └── README.md
```

### `main.bicep`

Contiene la definición de la infraestructura de Azure.

### `main.parameters.json`

Contiene los parámetros utilizados durante el despliegue.

### `README.md`

Contiene las instrucciones para reproducir la infraestructura.

## Enlace de verificación

[README de infraestructura de Azure](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/infra/azure/README.md)

---

# 5. Pipeline en verde sobre la rama principal

## Objetivo

Demostrar que el proyecto cuenta con integración continua y que existe una ejecución exitosa sobre la rama principal `master`.

## Integración continua

El repositorio contiene el workflow:

```text
.github/workflows/ci.yml
```

Este workflow se denomina:

```yaml
name: CI
```

y está configurado para ejecutarse cuando existe un `push` o un `pull_request` sobre la rama `master`:

```yaml
on:
  push:
    branches: [master]
  pull_request:
    branches: [master]
```

El pipeline contiene, entre otras, las siguientes etapas:

* Pruebas del backend.
* Pruebas de contrato de la API mediante Schemathesis.
* Pruebas unitarias.
* Pruebas del corte vertical.
* Comprobación de conexión del frontend con la API.
* Compilación del frontend.
* Comprobación de la portada del frontend.

El workflow configura Python 3.12 para las pruebas del backend y Node.js 22 para las pruebas relacionadas con el frontend. ([GitHub][2])

## Despliegue

El README de infraestructura indica que el despliegue hacia Azure se realiza mediante:

```text
.github/workflows/master_drift-utb-202620.yml
```

Esto separa el proceso de integración continua del proceso específico de despliegue a Azure. ([GitHub][1])

## Última ejecución utilizada como evidencia

Se cuenta con una ejecución exitosa asociada al cambio de observabilidad:

**Commit:**

```text
0ed61f1
```

**Mensaje del commit:**

```text
feat: agregar métricas y logs estructurados
```

**Rama:**

```text
master
```

**Conclusión:**

```text
Success
```

**URL de la ejecución:**

[https://github.com/ISCOUTB/AS_202620_Drift/actions/runs/36361558457](https://github.com/ISCOUTB/AS_202620_Drift/actions/runs/36361558457)

Esta ejecución se utiliza como evidencia de una ejecución exitosa del pipeline asociada a la rama principal.

## Enlaces de verificación

### Workflow de integración continua

[https://github.com/ISCOUTB/AS_202620_Drift/blob/master/.github/workflows/ci.yml](https://github.com/ISCOUTB/AS_202620_Drift/blob/master/.github/workflows/ci.yml)

---

# 6. Logs estructurados

## Objetivo

Demostrar que el backend genera logs estructurados que permiten registrar información relevante de las operaciones realizadas por la aplicación y facilitar su consulta y análisis.

## Implementación

La funcionalidad de observabilidad fue incorporada al backend junto con las métricas de rendimiento de búsqueda.

Los eventos relacionados con las búsquedas registran información estructurada sobre la ejecución de la operación.

Entre los eventos utilizados se encuentran:

```text
search_completed
search_failed
```

Estos eventos permiten registrar información relacionada con:

* Evento generado.
* Duración de la operación.
* Cantidad de resultados.
* Longitud de la consulta.
* Información asociada a errores.

## Ejemplo de evento de búsqueda exitosa

La estructura esperada de un evento de búsqueda exitosa es:

```json
{
  "event": "search_completed",
  "duration_ms": 952.26,
  "results_count": 10,
  "query_length": 8
}
```

## Ejemplo de evento de búsqueda fallida

La estructura esperada para una operación que genera un error es:

```json
{
  "event": "search_failed",
  "duration_ms": 1200.45,
  "query_length": 8
}
```

> **Nota:** Los valores numéricos mostrados anteriormente son ejemplos de la estructura del evento. Los valores concretos dependen de cada ejecución.

## Archivo de configuración / implementación

La implementación de observabilidad fue incorporada al código del backend mediante el cambio identificado por el commit:

```text
0ed61f1
```

con el mensaje:

```text
feat: agregar métricas y logs estructurados
```
La implementacion se encuentra en: 
```text
backend/app/infrastructure/observability.py
```

## Enlace de referencia

[https://github.com/ISCOUTB/AS_202620_Drift/actions/runs/36361558457](https://github.com/ISCOUTB/AS_202620_Drift/actions/runs/36361558457)

## 7.Metrica Consultable asociada a escenario de calidad

## Métrica
los logs estructurados se encuentran relacionados con la metrica:

```text
drift_search_latency_ms
```

Esta métrica registra la latencia de las operaciones de búsqueda y puede consultarse mediante:

```text
GET /metrics
```
## Escenario de calidad relacionado
```text
E1 — Rendimiento
```

## Respuesta del endpoint `/metrics`

Durante una comprobación en la que se realizaron algunas búsquedas de prueba , el endpoint respondió:

```json
{
  "search_latency": {
    "metric": "drift_search_latency_ms",
    "sample_count": 9,
    "average_ms": 952.26,
    "p95_ms": 5415.11,
    "window": "latest 100 searches in current process",
    "resets_on_restart": true
  }
}
```

Esto confirma que la métrica `drift_search_latency_ms` está disponible y es consultable desde el backend desplegado.

Los resultados obtenidos fueron:

Muestras registradas: 9
Latencia promedio: 952.26 ms
P95: 5415.11 ms
Ventana: últimas 100 búsquedas del proceso actual
Reinicio de muestras: las muestras se reinician al reiniciar el proceso

## 8.Secretos fuera del código y tomados del entorno o del almacén

### Evidencia

Los secretos utilizados por el proyecto no se almacenan directamente en el código fuente.

Se cuenta con un archivo `.env.example` para documentar las variables de entorno necesarias sin incluir sus valores reales.

Además, el workflow de GitHub Actions utiliza referencias a secretos mediante `secrets.*`, por ejemplo:

```yaml
${{ secrets.AZUREAPPSERVICE_CLIENTID_* }}
${{ secrets.AZUREAPPSERVICE_TENANTID_* }}
${{ secrets.AZUREAPPSERVICE_SUBSCRIPTIONID_* }}
```
los valores reales de estos secretos no se encuentran dentro del repositorio

## Archivos usados como evidencia
```text
.env.example
.github/workflows/master_drift-utb-202620.yml
```
