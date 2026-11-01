# Modelo de amenazas de DRIFT (STRIDE)

- **Commit de referencia:** `7d045f9` (1 de noviembre de 2026)
- **Base del modelo:** vista vigente de contenedores del [C4](../c4/contenedores.md), actualizada el 20 de octubre de 2026
- **Método:** STRIDE aplicado a cada elemento del C4 y a cada flujo entre elementos

## 1. Elementos del C4 analizados y límites de confianza


| Elemento del C4                                                                       | Límite de confianza                                                                           |
|---------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **Usuario** → **Frontend web (Next.js)**                                            | Internet → frontend (Vercel y Dokploy)                                                       |
| **Almacén del navegador** (`localStorage`, clave `drift.pcProfile`)                  | En el dispositivo del usuario; el usuario lo controla                                          |
| **Frontend** → **Backend / API (FastAPI)**                                          | Internet → API (Azure App Service, Vercel y Dokploy). Los endpoints de la API son públicos. |
| **Backend** → **Steam**, **CheapShark**, **PlayStation Store**, **open.er-api.com** | API → terceros por HTTPS. DRIFT no controla sus respuestas.                                  |
| **Pipeline CI/CD** (GitHub Actions → Azure)                                         | Repositorio → producción, con secretos de despliegue                                        |
| **Configuración del despliegue** (variables de Dokploy y Azure)                      | Contiene las URLs privadas de los puntajes de hardware                                         |


## 2. Escala de priorización

- **Probabilidad (P):** 1 = baja (requiere condiciones poco comunes), 2 = media (requiere un atacante con intención), 3 = alta (trivial o ya conocida públicamente).
- **Impacto (I):** 1 = bajo (molestia o fuga de información operativa), 2 = medio (degrada el servicio o altera datos mostrados), 3 = alto (ejecución de código, caída del servicio o suplantación).
- **Prioridad = P × I:** 6–9 **Alta**, 3–4 **Media**, 1–2 **Baja**.

## 3. Tabla de amenazas (ordenada por prioridad)

Estados posibles: **Hecha**, **Pendiente** o **Aceptada**. Los riesgos aceptados se justifican en [arc42 §11.9](../arc42/arc42-11-riesgos-y-deuda-tecnica.md).


| ID  | STRIDE  | Elemento del C4                                               | Amenaza                                                                                                                                                                                           | P | I | Prioridad   | Mitigación                                                                                                                | Dueño           | Estado        | Evidencia                                                                               |
|-----|---------|---------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---|---|-------------|----------------------------------------------------------------------------------------------------------------------------|------------------|---------------|-----------------------------------------------------------------------------------------|
| A1  | T, E    | Frontend web (Next.js)                                        | Dependencias con RCE crítica conocida (`next` 16.3.2, `sharp`) y versiones `latest` que cambian sin control                                                                                      | 3 | 3 | **9 Alta**  | Actualizar a `next` 16.4.3, fijar versiones exactas y auditar dependencias en el CI                                        | JerryDBM         | **Hecha**     | PR #33, PR #36, [análisis de dependencias](../evidencias/s13-analisis-dependencias.md) |
| A2  | E, T, D | Backend / API → PlayStation Store                           | `POST /games/sync/playstation` no exige autenticación y aparece en `/docs` y `/openapi.json`. Cualquiera puede reemplazar el catálogo en memoria y disparar llamadas salientes.                 | 3 | 2 | **6 Alta**  | Exigir un token de servicio en una cabecera, leído de una variable de entorno; sin token, responder 401                   | <u>(asignar)</u> | **Pendiente** | ADR-0011 (por escribir)                                                                 |
| A3  | D       | Backend / API → Steam, CheapShark, PlayStation, open.er-api | `GET /games/search` no tiene límite de tasa. Cada petición sale a hasta 4 fuentes externas, así que un abuso amplifica el tráfico y puede provocar bloqueos 429 (open.er-api bloquea 20 min). | 2 | 3 | **6 Alta**  | Limitar la tasa por IP en la API o en el proxy del despliegue                                                              | <u>(asignar)</u> | **Pendiente** | ADR-0012 (por escribir)                                                                 |
| A11 | S, I    | Backend / API → fuentes externas (TLS)                      | `certifi` 2026.7.22 confía en una raíz con intermedias comprometidas, lo que permite suplantar a una fuente externa                                                                             | 1 | 3 | **3 Media** | Actualizar `certifi` a ≥ 2026.10.18 en el backend y en Vercel                                                            | JerryDBM         | **Hecha**     | PR #34, PR #35                                                                          |
| A8  | S, E    | Pipeline CI/CD                                                | Robo de `SONAR_TOKEN` o de la identidad de Azure, o una acción de terceros comprometida                                                                                                          | 1 | 3 | **3 Media** | Acciones fijadas por SHA, OIDC sin contraseñas, `permissions: contents: read`, Dependabot para `github-actions`           | JerryDBM         | **Hecha**     | `.github/workflows/*.yml`, `.github/dependabot.yml`                                     |
| A5  | I       | Backend / API (`/metrics`)                                    | Las métricas de latencia y degradación de fuentes son públicas                                                                                                                                 | 2 | 1 | **2 Baja**  | Restringir `/metrics` con el mismo token de A2, o aceptarlo                                                                | <u>(asignar)</u> | **Pendiente** | —                                                                                     |
| A9  | T       | Backend / API (CORS)                                          | `allow_credentials=True` y `allow_methods=["*"]` aunque DRIFT no usa cookies: la configuración es más abierta de lo necesario                                                                   | 2 | 1 | **2 Baja**  | `allow_credentials=False`, `allow_methods=["GET", "POST"]`                                                                 | <u>(asignar)</u> | **Pendiente** | —                                                                                     |
| A10 | R       | Backend / API (sincronización)                               | No queda registro de quién lanzó una sincronización del catálogo                                                                                                                              | 2 | 1 | **2 Baja**  | Registrar en el log estructurado el origen y el resultado de cada sincronización (junto con A2)                           | <u>(asignar)</u> | **Pendiente** | —                                                                                     |
| A7  | T       | Almacén del navegador → Backend                            | El usuario manipula su perfil de PC guardado en `localStorage`                                                                                                                                    | 2 | 1 | **2 Baja**  | El frontend descarta formatos inválidos (`createPcProfile`) y el backend valida con `StrictInt`                           | JerryDBM         | **Hecha**     | `BrowserPcProfileRepository.js`, `CompatibilityRequest` en `main.py`                    |
| A4  | T, S    | Fuentes externas → Frontend (tarjetas de juego)             | Una fuente devuelve enlaces manipulados hacia sitios maliciosos                                                                                                                                   | 1 | 2 | **2 Baja**  | Ya existen `rel="noopener noreferrer"` y el bloqueo de URLs `javascript:` de React 19. No se valida el dominio de destino. | <u>(asignar)</u> | **Aceptada**  | arc42 §11.9                                                                            |
| A6  | I       | Configuración del despliegue                                 | Se filtran las URLs privadas (gist secreto) de los puntajes de hardware                                                                                                                           | 1 | 1 | **1 Baja**  | No se versionan (`.env.example` vacío); viven en el panel de Dokploy y Azure                                              | <u>(asignar)</u> | **Aceptada**  | arc42 §11.9                                                                            |


## 4. Plan de mitigación (orden de ataque)


| Orden | Amenaza                                          | Prioridad | Estado                         |
|-------|--------------------------------------------------|-----------|--------------------------------|
| 1     | A1: dependencias vulnerables del frontend        | 9 Alta    | Hecha (PR #33 y #36)           |
| 2     | A2: sincronización sin autenticación           | 6 Alta    | Pendiente: siguiente cambio    |
| 3     | A3: búsqueda sin límite de tasa                | 6 Alta    | Pendiente                      |
| 4     | A5, A9, A10: ajustes de configuración de la API | 2 Baja    | Pendiente, después de A2 y A3 |


A11 (prioridad Media) se corrigió en la misma jornada que A1, antes que A2 y A3. Salió del mismo análisis de dependencias y era un cambio de una línea sin efecto en la estructura. A8 y A7 ya estaban mitigadas por decisiones anteriores.

## 5. Componente generativo

DRIFT **no incorpora un componente de IA generativa** ([ADR-0007](../adr/0007-evaluacion-incorporacion-componente-generativo.md)), así que hoy no aplican la inyección de prompt, la fuga de datos por el modelo ni el envenenamiento del contexto. El uso de IA que registra [`docs/ia.md`](../ia.md) es una herramienta de desarrollo y no forma parte del sistema desplegado.

Si una versión futura lo incorpora, el nuevo ADR deberá añadir a esta tabla esas tres amenazas sobre el nuevo contenedor:

- **Inyección de prompt:** desde la consulta del usuario y desde los datos de las tiendas.
- **Fuga de datos:** el perfil del PC y las consultas enviadas al proveedor del modelo.
- **Envenenamiento del contexto:** descripciones de juegos manipuladas en las fuentes externas.

 
