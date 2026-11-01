# ADR-0011: Autenticación de las operaciones administrativas de la API

- **Estado:** Aceptado
- **Fecha:** 2026-11-01
- **Decisores:** Equipo de desarrollo de DRIFT
- **Mitiga:** amenazas A2, A5 y A10 del [modelo de amenazas](../seguridad/modelo-amenazas.md)
- **Relacionado con:** [ADR-0008](0008-persistencia-ejecucion-y-degradacion-de-fuentes.md) (catálogo en memoria) y [arc42 §8](../arc42/arc42_8_conceptos_transversales.md)

## Contexto

Todos los endpoints del contenedor **Backend / API** del C4 eran públicos. Dos de ellos no son para el usuario final:

- `POST /games/sync/playstation` reemplaza por completo el catálogo de PlayStation en memoria y hace llamadas salientes a la tienda. Aparecía en `/docs` y en `/openapi.json`, así que cualquiera podía descubrirlo y llamarlo en bucle (amenaza A2: P3 × I2 = **6, Alta**).
- `GET /metrics` expone la latencia y la degradación de las fuentes (amenaza A5, Baja).

Además, no quedaba registro de quién lanzaba una sincronización (amenaza A10, Baja).

DRIFT no tiene usuarios registrados, sesiones ni base de datos (ADR-0008). El único que necesita estas operaciones es el equipo, desde la terminal, un script o una tarea programada.

## Alternativas

1. **Token de servicio compartido** en la cabecera `Authorization: Bearer`, leído de una variable de entorno secreta. Sin dependencias nuevas; encaja con la gestión de secretos que ya existe (Dokploy → Environment, configuración de Azure).
2. **Sacar los endpoints de la API pública:** exponerlos en otro puerto o protegerlos en el proxy (Traefik). Depende de cada plataforma: Azure App Service y Vercel no ofrecen el mismo mecanismo, así que habría tres configuraciones distintas.
3. **Autenticación de usuarios (OAuth/OIDC con cuentas y roles).** Desproporcionada: no hay usuarios ni base de datos donde guardarlos, y obligaría a añadir ambos.
4. **Eliminar el endpoint de sincronización.** El catálogo quedaría vacío hasta un reinicio con carga automática, lo que cambia el comportamiento descrito en arc42 §8.13 (O1).

## Decisión

Se adopta la **alternativa 1**.

- Nueva dependencia de FastAPI `require_admin_token` en `backend/app/infrastructure/api/security.py`, aplicada a `POST /games/sync/playstation` y a `GET /metrics`.
- **Sin cabecera, o con un token incorrecto:** 401 con `WWW-Authenticate: Bearer`. La comparación usa `hmac.compare_digest` para no filtrar el token por tiempo de respuesta.
- **Falla cerrado:** si `DRIFT_ADMIN_TOKEN` no está configurada en el servidor, las operaciones responden 403 `admin_operation_disabled`. Nunca quedan abiertas por olvido.
- **Registro (A10):** cada sincronización autorizada deja los eventos `admin_catalog_sync_requested` (con la IP de origen) y `admin_catalog_sync_completed` en el log estructurado.
- **Contrato:** `docs/api/drift/openapi.yaml` (versión 1.5.0) declara el esquema `adminToken` y las respuestas 401 y 403.

## Consecuencias

**Positivas**

- Un tercero ya no puede vaciar ni recargar el catálogo, ni usar la API como amplificador de llamadas hacia PlayStation.
- El cambio queda dentro del adaptador de entrada: el dominio y los casos de uso no cambian (lo comprueba `test_architecture.py`).
- Las pruebas `test_s13_seguridad_api.py` cubren el rechazo sin token, con token incorrecto, sin token configurado, el acceso correcto y el registro.

**Negativas y riesgos**

- Es un único secreto compartido por el equipo: no distingue quién de los integrantes hizo la llamada (el registro guarda la IP, no la persona). Si se filtra, hay que rotarlo en Dokploy y Azure.
- Quien consulte `/metrics` (por ejemplo, para repetir las mediciones de E6 en producción) necesita el token.
- El despliegue serverless de Vercel (ADR-0006) no tiene estos endpoints, así que no le afecta.

## Cambio estructural

Se añade al contenedor **Backend / API** un componente de control de acceso en el adaptador de entrada (`infrastructure/api/security.py`) y una variable secreta nueva en cada entorno de despliegue (`DRIFT_ADMIN_TOKEN` en `deploy/compose.lab.yaml`, `infra/azure/main.bicep` y `deploy/.env.example`).
