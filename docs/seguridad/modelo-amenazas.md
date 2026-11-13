# Modelo de amenazas de DRIFT (STRIDE)

- **Commit de referencia:** `7d045f9` (1 de noviembre de 2026); estados actualizados con las mitigaciones de ADR-0011 y ADR-0012
- **Base del modelo:** vista vigente de contenedores del [C4](../c4/contenedores.md), actualizada el 20 de octubre de 2026
- **Método:** STRIDE aplicado a cada elemento del C4 y a cada flujo entre elementos
- **Documentos relacionados:** [privacidad](privacidad.md), [arc42 §8.16 — arquitectura de seguridad](../arc42/arc42_8_conceptos_transversales.md) y [arc42 §11.9 — amenazas aceptadas](../arc42/arc42-11-riesgos-y-deuda-tecnica.md)

## 1. Elementos del C4 analizados y límites de confianza


| Elemento del C4                                                                       | Límite de confianza                                                                           |
|---------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------|
| **Usuario** → **Frontend web (Next.js)**                                            | Internet → frontend (Dokploy)                                                       |
| **Almacén del navegador** (`localStorage`, clave `drift.pcProfile`)                  | En el dispositivo del usuario; el usuario lo controla                                          |
| **Frontend** → **Backend / API (FastAPI)**                                          | Internet → API (Dokploy). Los endpoints de la API son públicos. |
| **Backend** → **Steam**, **CheapShark**, **PlayStation Store**, **open.er-api.com** | API → terceros por HTTPS. DRIFT no controla sus respuestas.                                  |
| **Pipeline CI/CD** (GitHub Actions)                                         | Repositorio → pruebas y análisis; el despliegue lo hace Dokploy al leer `master`                                        |
| **Configuración del despliegue** (variables de Dokploy)                      | Contiene las URLs privadas de los puntajes de hardware                                         |


## 2. Escala de priorización

- **Probabilidad (P):** 1 = baja (requiere condiciones poco comunes), 2 = media (requiere un atacante con intención), 3 = alta (trivial o ya conocida públicamente).
- **Impacto (I):** 1 = bajo (molestia o fuga de información operativa), 2 = medio (degrada el servicio o altera datos mostrados), 3 = alto (ejecución de código, caída del servicio o suplantación).
- **Prioridad = P × I:** 6–9 **Alta**, 3–4 **Media**, 1–2 **Baja**.

## 3. Tabla de amenazas (ordenada por prioridad)

Estados posibles: **Hecha**, **Pendiente** o **Aceptada**. Los riesgos aceptados se justifican en [arc42 §11.9](../arc42/arc42-11-riesgos-y-deuda-tecnica.md).


| ID  | STRIDE  | Elemento del C4                                               | Amenaza                                                                                                                                                                                           | P | I | Prioridad   | Mitigación                                                                                                                | Dueño           | Estado        | Evidencia                                                                               |
|-----|---------|---------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---|---|-------------|----------------------------------------------------------------------------------------------------------------------------|------------------|---------------|-----------------------------------------------------------------------------------------|
| A1  | T, E    | Frontend web (Next.js)                                        | Dependencias con RCE crítica conocida (`next` 16.3.2, `sharp`) y versiones `latest` que cambian sin control                                                                                      | 3 | 3 | **9 Alta**  | Actualizar a `next` 16.4.3, fijar versiones exactas y auditar dependencias en el CI                                        | JerryDBM         | **Hecha**     | PR #33, PR #36, [análisis de dependencias](../evidencias/s13-analisis-dependencias.md) |
| A2 | E, T, D | Backend / API → PlayStation Store | `POST /games/sync/playstation` no exige autenticación y aparece en `/docs` y `/openapi.json`. Cualquiera puede reemplazar el catálogo en memoria y disparar llamadas salientes. | 3 | 2 | **6 Alta** | Token de servicio `Authorization: Bearer` leído de `DRIFT_ADMIN_TOKEN`; sin token, 401; sin token configurado en el servidor, 403 (falla cerrado) | JerryDBM | **Hecha** | ADR-0011, `security.py`, `test_s13_seguridad_api.py` |
| A3 | D | Backend / API → Steam, CheapShark, PlayStation, open.er-api | `GET /games/search` no tiene límite de tasa. Cada petición sale a hasta 4 fuentes externas, así que un abuso amplifica el tráfico y puede provocar bloqueos 429 (open.er-api bloquea 20 min). | 2 | 3 | **6 Alta** | Límite de 60 peticiones/min por IP en búsqueda y compatibilidad (`SlidingWindowRateLimiter`), 429 con `Retry-After` | JerryDBM | **Hecha** | ADR-0012, `security.py`, `test_s13_seguridad_api.py` |
| A11 | S, I    | Backend / API → fuentes externas (TLS)                      | `certifi` 2026.7.22 confía en una raíz con intermedias comprometidas, lo que permite suplantar a una fuente externa                                                                             | 1 | 3 | **3 Media** | Actualizar `certifi` a ≥ 2026.10.18 en el backend                                                            | JerryDBM         | **Hecha**     | PR #34, PR #35                                                                          |
| A8  | S, E    | Pipeline CI/CD                                                | Robo de `SONAR_TOKEN`, o una acción de terceros comprometida                                                                                                          | 1 | 3 | **3 Media** | Acciones fijadas por SHA, sin credenciales de despliegue en el pipeline (ADR-0022), `permissions: contents: read`, Dependabot para `github-actions`           | JerryDBM         | **Hecha**     | `.github/workflows/*.yml`, `.github/dependabot.yml`                                     |
| A5 | I | Backend / API (`/metrics`) | Las métricas de latencia y degradación de fuentes son públicas | 2 | 1 | **2 Baja** | `/metrics` exige el mismo token administrativo de A2 | JerryDBM | **Hecha** | ADR-0011, `test_metrics_require_the_admin_token` |
| A9 | T | Backend / API (CORS) | `allow_credentials=True` y `allow_methods=["*"]` aunque DRIFT no usa cookies: la configuración es más abierta de lo necesario | 2 | 1 | **2 Baja** | `allow_credentials=False`, solo `GET`/`POST` y solo la cabecera `Content-Type` | JerryDBM | **Hecha** | ADR-0012, `test_cors_*` |
| A10 | R | Backend / API (sincronización) | No queda registro de quién lanzó una sincronización del catálogo | 2 | 1 | **2 Baja** | Eventos `admin_catalog_sync_requested` (con IP de origen) y `admin_catalog_sync_completed` en el log estructurado | JerryDBM | **Hecha** | ADR-0011, `test_authorized_sync_is_logged_with_its_origin` |
| A7  | T       | Almacén del navegador → Backend                            | El usuario manipula su perfil de PC guardado en `localStorage`                                                                                                                                    | 2 | 1 | **2 Baja**  | El frontend descarta formatos inválidos (`createPcProfile`) y el backend valida con `StrictInt`                           | JerryDBM         | **Hecha**     | `BrowserPcProfileRepository.js`, `CompatibilityRequest` en `main.py`                    |
| A4  | T, S    | Fuentes externas → Frontend (tarjetas de juego)             | Una fuente devuelve enlaces manipulados hacia sitios maliciosos                                                                                                                                   | 1 | 2 | **2 Baja**  | Ya existen `rel="noopener noreferrer"` y el bloqueo de URLs `javascript:` de React 19. No se valida el dominio de destino. | JerryDBM | **Aceptada**  | arc42 §11.9                                                                            |
| A6  | I       | Configuración del despliegue                                 | Se filtran las URLs privadas (gist secreto) de los puntajes de hardware                                                                                                                           | 1 | 1 | **1 Baja**  | No se versionan (`.env.example` vacío); viven en el panel de Dokploy                                              | JerryDBM | **Aceptada**  | arc42 §11.9                                                                            |


## 4. Plan de mitigación (orden de ataque)


| Orden | Amenaza | Prioridad | Estado |
|---|---|---|---|
| 1 | A1: dependencias vulnerables del frontend | 9 Alta | Hecha (PR #33 y #36) |
| 2 | A2: sincronización sin autenticación | 6 Alta | Hecha (ADR-0011) |
| 3 | A3: búsqueda sin límite de tasa | 6 Alta | Hecha (ADR-0012) |
| 4 | A5, A9, A10: ajustes de configuración de la API | 2 Baja | Hecha, en el mismo cambio que A2 y A3 |
| — | A4, A6: riesgos aceptados | 2 y 1 Baja | Aceptadas, con motivo en arc42 §11.9 |

A11 (prioridad Media) se corrigió en la misma jornada que A1, antes que A2 y A3. Salió del mismo análisis de dependencias y era un cambio de una línea sin efecto en la estructura. A8 y A7 ya estaban mitigadas por decisiones anteriores.

## 5. Componente generativo

DRIFT **no incorpora un componente de IA generativa** ([ADR-0007](../adr/0007-evaluacion-incorporacion-componente-generativo.md)), así que hoy no aplican la inyección de prompt, la fuga de datos por el modelo ni el envenenamiento del contexto. El uso de IA que registra [`docs/ia.md`](../ia.md) es una herramienta de desarrollo y no forma parte del sistema desplegado.

Si una versión futura lo incorpora, el nuevo ADR deberá añadir a esta tabla esas tres amenazas sobre el nuevo contenedor:

- **Inyección de prompt:** desde la consulta del usuario y desde los datos de las tiendas.
- **Fuga de datos:** el perfil del PC y las consultas enviadas al proveedor del modelo.
- **Envenenamiento del contexto:** descripciones de juegos manipuladas en las fuentes externas.

## 6. Amenazas nuevas por cuentas y base de datos (propuesto, 12 de noviembre de 2026)

> Corresponden a cambios que todavía no están en `master` (ADR-0014 a ADR-0017). No se revisaron entre pares ni se probaron en el laboratorio; la prioridad es la estimación de quien las escribió y debe confirmarla el equipo. Elementos nuevos del C4: la base de datos PostgreSQL, Google como proveedor de identidad, y las fuentes IsThereAnyDeal y tienda de Xbox.

| ID | STRIDE | Elemento | Amenaza | P | I | Prioridad | Mitigación | Estado | Evidencia |
|---|---|---|---|---|---|---|---|---|---|
| A12 | S, E | Backend / API (sesión) | Otro sitio hace que el navegador de la víctima cambie o borre sus dispositivos o su cuenta (CSRF) | 2 | 3 | **6 Alta** | Cookie `SameSite=Lax` y comprobación del `Origin` en toda petición que cambia datos | Hecha | ADR-0017, `test_changes_from_another_site_are_refused` |
| A13 | S | Backend / API (inicio de sesión) | Un atacante completa en el navegador de la víctima un inicio de sesión que ella no empezó | 2 | 3 | **6 Alta** | `state` al azar comparado con la cookie del navegador; `nonce` dentro del `id_token` | Hecha | `test_login_is_rejected_without_the_state_this_browser_received` |
| A14 | E, I | Backend / API (dispositivos) | Un usuario lee, cambia o borra dispositivos de otro adivinando su identificador | 2 | 3 | **6 Alta** | Toda consulta filtra por el dueño de la sesión; al guardar, la base no reemplaza una fila de otro dueño | Hecha | `test_one_user_cannot_touch_the_devices_of_another`, `test_devices_belong_to_their_owner` |
| A15 | I | Base de datos | Quien lee la base o una copia obtiene sesiones utilizables | 1 | 3 | **3 Media** | Solo se guarda la huella SHA-256 del identificador de sesión | Hecha | `test_only_the_hash_of_the_session_token_is_stored` |
| A16 | I, S | Navegador | Robo de la cookie de sesión por un script inyectado (XSS) | 1 | 3 | **3 Media** | Cookie `HttpOnly`; por HTTPS, `Secure`. Sigue pendiente una política CSP | Parcial | ADR-0017 |
| A17 | S | Backend / API → Google | Se acepta un `id_token` de otro cliente, vencido o con correo sin verificar | 1 | 3 | **3 Media** | Se comprueban emisor, destinatario, vencimiento, `nonce` y correo verificado. La firma no se verifica porque el token llega directo de Google por TLS | Hecha, con riesgo aceptado | `test_google_token_that_does_not_match_is_rejected` |
| A18 | I, D | Base de datos | Pérdida de las cuentas por borrado del volumen o fallo del servidor | 2 | 2 | **4 Media** | Ninguna todavía: no hay copias de seguridad | **Pendiente** | ADR-0014 |
| A19 | D | Backend / API (copia de respaldo) | Búsquedas inventadas llenan la tabla de copias | 2 | 2 | **4 Media** | Límite de tasa (ADR-0012), máximo de 5.000 filas, 72 horas y 256 KB por respuesta | Hecha | ADR-0015, `test_cleanup_keeps_only_the_newest_rows` |
| A20 | I | Configuración | Fuga de la llave de IsThereAnyDeal o del secreto del cliente de Google | 1 | 3 | **3 Media** | Solo en variables de entorno; la llave viaja en una cabecera y no se registra | Hecha | ADR-0016, `test_search_returns_pc_stores_in_pesos_with_discount_and_link` |
| A21 | T | Configuración | `CORS_ALLOWED_ORIGINS` con un origen de más: ahora ese origen podría actuar con la sesión del usuario | 1 | 3 | **3 Media** | Lista explícita, sin comodín; revisar la variable en cada entorno | Parcial: depende de la configuración | `test_cors_allows_credentials_only_for_the_configured_origin` |
