# ADR-0022: Desplegar DRIFT solo en el servidor del laboratorio

- **Estado:** Propuesto
- **Fecha:** 2026-11-13
- **Decisores:** Equipo DRIFT
- **Sustituye a:** ADR-0005 (estrategia de despliegue) y ADR-0006 (API de búsqueda sin servidor en Vercel)

## Contexto

DRIFT tenía tres despliegues:

| Entorno | Qué publicaba | Cómo se desplegaba |
|---|---|---|
| Servidor del laboratorio (Dokploy) | Frontend, API y PostgreSQL | Docker Compose, `deploy/compose.lab.yaml`, al cambiar `master` |
| Azure App Service | API | Workflow de GitHub Actions en cada push a `master` |
| Vercel | Frontend y una API de búsqueda sin servidor | A mano, con la línea de comandos de Vercel |

Con los últimos cambios, solo el laboratorio sirve para todo lo que DRIFT hace hoy:

- Azure y Vercel **no tienen base de datos**: no guardan copias de respaldo (ADR-0014) ni cuentas, favoritos o alertas (ADR-0017, ADR-0020).
- El inicio de sesión necesita que la página y la API estén en el mismo sitio (ADR-0017). Entre Vercel y Azure, que son dominios distintos, el navegador no envía la cookie de sesión.
- La API de Vercel era otra aplicación (`deployment/vercel/api/index.py`) que no tenía límite de tasa (arc42 §11.9, S13-R1) ni las rutas nuevas.
- Mantener tres entornos duplicaba la configuración, los secretos y la documentación, y dos de ellos ya estaban «en retiro» en el C4.

## Decisión

DRIFT se despliega **solo en el servidor del laboratorio**. Se quita del repositorio todo lo que desplegaba en Azure y en Vercel:

| Se elimina | Qué era |
|---|---|
| `.github/workflows/master_drift-utb-202620.yml` | Despliegue a Azure con inicio de sesión OIDC |
| `infra/azure/` (`main.bicep`, `main.parameters.json`, `README.md`) | Infraestructura como código de Azure |
| `backend/startup.sh` | Comando de arranque de Azure App Service (gunicorn) |
| `deployment/vercel/` | API de búsqueda sin servidor y la configuración del proyecto de Vercel |
| `.vercel` en `frontend/.gitignore` y `frontend/.dockerignore` | Carpeta local de la herramienta de Vercel |

Se actualizan los comentarios, el texto de privacidad de la página, el README, arc42 (§2, §7, §8, §9 y §11), el C4, el modelo de amenazas y el documento de privacidad. **Se conserva** la lógica que quita el puerto de la IP (`client_ip`): es genérica y está probada.

Lo que **no** se toca, porque es historia: ADR-0005 y ADR-0006 (pasan a «Reemplazado»), los demás ADR, `docs/ia.md` y la carpeta `docs/evidencias/`, que registran lo que se midió o decidió cuando esos entornos existían.

## Consecuencias

**A favor**

- Un solo entorno que mantener y una sola fuente de verdad: `deploy/compose.lab.yaml`.
- El pipeline de GitHub Actions deja de tener credenciales de despliegue: la amenaza A8 (robo de la identidad de Azure) desaparece. Solo queda `SONAR_TOKEN`.
- Se cierra el riesgo S13-R1 (Vercel sin límite de tasa) y la transferencia internacional de datos por alojamiento (privacidad §4).
- La documentación deja de decir que el inicio de sesión no funciona «en algunos entornos».

**En contra**

- **Un solo punto de falla:** si el servidor del laboratorio cae, DRIFT no tiene respaldo. Antes, Azure y Vercel podían seguir atendiendo búsquedas sin cuentas.
- **Sin otra URL pública** para probar: la única es `https://drift.iscoutb.dev`.
- El despliegue depende de que Dokploy tome `master`; el pipeline de GitHub ya no despliega nada.

**Cosas fuera del repositorio que quedan por hacer a mano** (no se pueden hacer desde el código):

- En GitHub → Settings → Secrets: borrar `AZUREAPPSERVICE_CLIENTID_…`, `AZUREAPPSERVICE_TENANTID_…` y `AZUREAPPSERVICE_SUBSCRIPTIONID_…`.
- En Azure: borrar el grupo de recursos y la credencial federada de GitHub, para no seguir gastando el crédito de Azure for Students.
- En Vercel: borrar los proyectos `drift-frontend-as202620` y `drift-serverless`.

## Reversibilidad

Todo se puede recuperar del historial de git: el último commit que contiene estos archivos es el anterior a este cambio. Volver a Azure o a Vercel exigiría además recrear los recursos y los secretos, y repetir el trabajo que ADR-0017 y ADR-0014 evitan en esos entornos (cuentas y base de datos).

## Lo que se verificó y lo que no

- **Verificado:** que ningún archivo del código, de la integración continua ni del compose del laboratorio dependiera de lo eliminado (búsqueda por `startup.sh`, `deployment/`, `infra/`, `azure` y `vercel`); que el frontend compila y que las pruebas del backend siguen pasando.
- **No verificado:** que Dokploy despliegue bien tras el cambio (no cambia nada de lo que usa, pero no se probó en el servidor).

## Cuándo revisar esta decisión

- El laboratorio deja de estar disponible o su capacidad (512 MB) no alcanza.
- El equipo necesita un segundo entorno de respaldo o de pruebas.
