# 7. Vista de despliegue

## 7.1 Infraestructura de despliegue

El sistema DRIFT se despliega utilizando diferentes servicios según la responsabilidad de cada pieza de la arquitectura.

La distribución es la siguiente:

```text
                    ┌─────────────────────┐
                    │       Usuario       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │       Vercel        │
                    │      Frontend       │
                    └──────────┬──────────┘
                               │
                               │ HTTP/HTTPS
                               ▼
              ┌─────────────────────────────────┐
              │       Azure App Service         │
              │                                 │
              │          Backend / API          │
              │                                 │
              │  /health    /metrics    /api   │
              └─────────────────────────────────┘

                    ┌─────────────────────┐
                    │   GitHub Actions    │
                    │       CI/CD         │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Azure App Service │
                    │      Deployment      │
                    └─────────────────────┘
```

## 7.2 Piezas y ubicación

| Pieza                       | Tecnología / servicio         | Ubicación                   |
| --------------------------- | ----------------------------- | --------------------------- |
| Sitio / interfaz            | Frontend                      | Vercel                      |
| API                         | Backend                       | Azure App Service           |
| Repositorio                 | GitHub                        | GitHub                      |
| Pipeline CI/CD              | GitHub Actions                | GitHub Actions              |
| Infraestructura como código | Azure Bicep                   | `infra/azure/`              |
| Observabilidad              | Logs estructurados y métricas | Backend / Azure App Service |

## 7.3 Frontend

El frontend de DRIFT se encuentra desplegado en Vercel.

Vercel se encarga de servir la interfaz de usuario y proporcionar el acceso público al frontend.

```text
Frontend
   │
   └── Vercel
```

## 7.4 Backend

El backend de DRIFT se encuentra desplegado en Azure App Service.

La API proporciona los endpoints utilizados por el sistema, incluyendo:

```text
/health
/metrics
```

El backend cuenta con una URL pública:

```text
https://drift-utb-202620-g5fvchdcgpcthkeg.mexicocentral-01.azurewebsites.net
```

El endpoint de comprobación de salud se encuentra disponible mediante:

```text
GET /health
```

## 7.5 Integración continua y despliegue

El código fuente se encuentra alojado en GitHub y el proceso de integración y despliegue utiliza GitHub Actions.

El flujo general es:

```text
GitHub
   │
   ▼
GitHub Actions
   │
   ├── Pruebas
   ├── Validaciones
   └── Despliegue
          │
          ▼
   Azure App Service
```

## 7.6 Infraestructura como código

La infraestructura de Azure se define mediante Azure Bicep y se encuentra versionada dentro del repositorio:

```text
infra/azure/
├── main.bicep
├── main.parameters.json
└── README.md
```

Esto permite definir y reproducir la infraestructura mediante código.

## 7.7 Observabilidad

El backend incorpora mecanismos de observabilidad mediante logs estructurados y métricas.

La implementación se encuentra en:

```text
backend/app/infrastructure/observability.py
```

Entre las métricas disponibles se encuentra:

```text
drift_search_latency_ms
```

Esta métrica puede consultarse mediante:

```text
GET /metrics
```

## 7.8 Flujo general de despliegue

El proceso completo de despliegue queda representado de la siguiente manera:

```text
Desarrollador
     │
     ▼
   GitHub
     │
     ▼
GitHub Actions
     │
     ├──────────────► Vercel
     │                 │
     │                 ▼
     │             Frontend
     │
     └──────────────► Azure App Service
                       │
                       ▼
                    Backend
                       │
                       ├── /health
                       ├── /metrics
                       └── API
```

## 7.9 Resumen

La arquitectura de despliegue separa el frontend y el backend en servicios independientes. El frontend se ejecuta en Vercel y el backend en Azure App Service. GitHub y GitHub Actions proporcionan el repositorio y el proceso de integración y despliegue, mientras que Azure Bicep permite definir la infraestructura como código.
