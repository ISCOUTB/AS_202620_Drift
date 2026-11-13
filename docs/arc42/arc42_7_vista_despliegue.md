# 7. Vista de despliegue

## 7.1 Infraestructura de despliegue

DRIFT se despliega en **un solo entorno**: el servidor compartido del laboratorio, con Dokploy y Docker Compose ([ADR-0022](../adr/0022-desplegar-solo-en-el-laboratorio.md)). Hasta el 12 de noviembre de 2026 también existían el backend en Azure App Service y el frontend en Vercel; se retiraron (sección 7.9).

```text
                    ┌─────────────────────┐
                    │       Usuario       │
                    └──────────┬──────────┘
                               │ HTTPS
                               ▼
              ┌─────────────────────────────────┐
              │  Traefik (Dokploy)              │
              │  https://drift.iscoutb.dev      │
              └───────┬─────────────────┬───────┘
                 "/"  │                 │  "/api" (Strip Path)
                      ▼                 ▼
              ┌──────────────┐   ┌───────────────┐        ┌──────────────┐
              │ web          │   │ api           │ ─────► │ postgres     │
              │ Next.js      │   │ FastAPI       │        │ PostgreSQL 17│
              └──────────────┘   └───────┬───────┘        └──────────────┘
                                         │ HTTPS
                                         ▼
                    Steam · IsThereAnyDeal · PlayStation · Xbox
                    open.er-api.com · Google (inicio de sesión)

   GitHub ──► GitHub Actions: pruebas, contrato, SonarQube y dependencias (no despliega)
   GitHub ──► Dokploy toma `master` y ejecuta docker compose up --build
```

## 7.2 Piezas y ubicación

| Pieza | Tecnología / servicio | Ubicación |
|---|---|---|
| Sitio / interfaz | Frontend (Next.js) | Contenedor `web` en el laboratorio |
| API | Backend (FastAPI) | Contenedor `api` en el laboratorio |
| Base de datos | PostgreSQL 17 | Contenedor `postgres` con el volumen `drift_pgdata` |
| Repositorio | GitHub | GitHub |
| Pipeline de pruebas | GitHub Actions | GitHub Actions (no despliega) |
| Despliegue | Dokploy + Docker Compose | Servidor del laboratorio |
| Infraestructura como código | Docker Compose y Dockerfiles | `deploy/compose.lab.yaml`, `backend/Dockerfile`, `frontend/Dockerfile` |
| Observabilidad | Logs estructurados y métricas | Backend (`/api/health`, `/api/metrics`) |

## 7.3 El servidor del laboratorio

| Elemento | Valor |
|---|---|
| URL | `https://drift.iscoutb.dev` (frontend en `/`, API en `/api` con *Strip Path*) |
| Infraestructura como código | `deploy/compose.lab.yaml`, `backend/Dockerfile`, `frontend/Dockerfile` |
| Contenedores | `api` (FastAPI, 1 proceso) y `web` (Next.js), 192 MB y 0,5 CPU cada uno; `postgres` (PostgreSQL 17), 96 MB y 0,25 CPU, con el volumen `drift_pgdata` (ADR-0014). Total: 480 MB de 512 MB |
| Despliegue | Automático en cada push a `master` |
| Health check | `GET /api/health` |
| Métricas | `GET /api/metrics`: latencia de búsqueda y `drift_source_unavailable_total` |
| Configuración | `CORS_ALLOWED_ORIGINS`, `USD_TO_COP_RATE`, `DRIFT_SOURCE_TIMEOUT_SECONDS` (3 s por defecto), `DRIFT_STEAM_TIMEOUT_SECONDS`, `DRIFT_STEAM_MAX_ATTEMPTS` y variables `DRIFT_STEAM_BACKOFF_*` / `DRIFT_STEAM_MAX_RETRY_AFTER_SECONDS` (ver [ADR-0009](../adr/0009-decision-extraccion-integracion-steam.md)) |
| Secretos | `DRIFT_DB_PASSWORD`, `DRIFT_ADMIN_TOKEN`, `DRIFT_ITAD_API_KEY`, `DRIFT_GOOGLE_CLIENT_SECRET` y las direcciones de los puntajes de hardware, en Dokploy → Environment |

El catálogo de PlayStation, las cachés de 60 s y las métricas viven en la memoria del contenedor `api`: se pierden en cada despliegue o reinicio (ADR-0008). Las copias de respaldo de las fuentes, las cuentas, los dispositivos y los favoritos se guardan en PostgreSQL y sobreviven a los despliegues (ADR-0014, ADR-0015, ADR-0017 y ADR-0020). Si PostgreSQL no responde, la búsqueda sigue funcionando con una copia en memoria; las cuentas responden «no disponible».

## 7.4 Integración continua y despliegue

El código se aloja en GitHub. **GitHub Actions prueba y analiza; no despliega.** Corre en cada push a `master` y en cada pull request hacia `master`:

```text
GitHub
   │
   ▼
GitHub Actions
   ├── Pruebas del backend y contrato de la API
   ├── Frontend conectado a la API
   ├── Análisis de dependencias
   └── SonarQube Cloud
```

El despliegue lo hace Dokploy: al cambiar `master`, reconstruye y levanta los contenedores con `deploy/compose.lab.yaml`.

## 7.5 Infraestructura como código

La infraestructura se define en el repositorio con Docker Compose y los Dockerfiles:

```text
deploy/
├── compose.lab.yaml
└── .env.example
backend/Dockerfile
frontend/Dockerfile
```

Las reglas del laboratorio (sin `ports:`, límites de memoria y CPU, sin `docker.sock`) están comentadas en el propio compose.

## 7.6 Observabilidad

El backend incorpora mecanismos de observabilidad mediante logs estructurados y métricas.

La implementación se encuentra en:

```text
backend/app/infrastructure/observability.py
```

Entre las métricas disponibles se encuentra:

```text
drift_search_latency_ms
```

Esta métrica puede consultarse mediante `GET /metrics`, que exige el token administrativo (ADR-0011).

## 7.7 Flujo general de despliegue

```text
Desarrollador
     │ push o pull request
     ▼
   GitHub ───────────► GitHub Actions (pruebas y análisis)
     │
     │ cambio en master
     ▼
  Dokploy ──► docker compose up --build ──► web + api + postgres
```

## 7.8 Resumen

DRIFT tiene un solo entorno desplegado, el servidor del laboratorio, con tres contenedores. GitHub Actions comprueba la calidad del código y Dokploy hace el despliegue. Esto permite que el inicio de sesión y la base de datos funcionen en el mismo sitio que la página (ADR-0017).

## 7.9 Entornos retirados (13 de noviembre de 2026)

| Entorno | Qué hacía | Por qué se retiró |
|---|---|---|
| Azure App Service | Backend, desplegado por GitHub Actions | Sin base de datos ni cuentas; un segundo entorno que mantener |
| Vercel | Frontend y una API de búsqueda sin servidor | Dominio distinto al de la API: la cookie de sesión no viaja; sin límite de tasa |

La decisión y sus consecuencias están en [ADR-0022](../adr/0022-desplegar-solo-en-el-laboratorio.md), que sustituye a ADR-0005 y ADR-0006. Sus archivos siguen en el historial de git.
