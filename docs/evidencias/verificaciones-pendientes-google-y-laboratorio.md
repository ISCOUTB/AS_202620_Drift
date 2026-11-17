# Verificaciones pendientes: inicio de sesión con Google y laboratorio con PostgreSQL

**Estado (13 de noviembre de 2026):** el inicio de sesión con Google **funcionó en local** con una cuenta real del equipo (sección 1, prueba en tu computador). Faltan la prueba en el laboratorio y la del compose con PostgreSQL.

Estas dos pruebas necesitan algo que el entorno de desarrollo automatizado no tiene: una cuenta real de Google y Docker. Esta guía dice qué hacer, qué se espera ver y dónde dejar el resultado. Al terminar, marca cada casilla y anota la fecha, el commit probado y lo que falló.

## 1. Inicio de sesión con Google (ADR-0017)

### Qué ya está verificado

- Las pruebas automáticas (`backend/tests/test_cuentas.py`) usan un proveedor de identidad simulado: cubren el `state`, el `nonce`, las cookies, la sesión, el origen y el borrado de la cuenta.
- El contrato de las rutas `/auth/*` está en `docs/api/drift/openapi.yaml` y pasa schemathesis sin el inicio de sesión configurado.

### Qué falta

Que Google entregue un token real y que DRIFT lo acepte: firma, emisor, audiencia y `nonce` contra los servidores de Google.

### Preparación (una vez)

1. En [Google Cloud Console](https://console.cloud.google.com/) → Credenciales → **ID de cliente de OAuth**, tipo «Aplicación web».
2. En «URI de redireccionamiento autorizados» agrega, letra por letra:
   - en tu computador: `http://localhost:8000/auth/google/callback`
   - en el laboratorio: `https://drift.iscoutb.dev/api/auth/google/callback`
3. Si la pantalla de consentimiento está en modo «Prueba», agrega tu correo como usuario de prueba.
4. Copia `deploy/.env.example` a `deploy/.env` y llena `DRIFT_GOOGLE_CLIENT_ID` y `DRIFT_GOOGLE_CLIENT_SECRET`. **No los subas al repositorio.**

### Prueba en tu computador

```bash
cd backend
python -m uvicorn app.main:app --env-file ../deploy/.env --port 8000
```

`--env-file` necesita `python-dotenv` (`pip install python-dotenv`), que no está en `requirements.txt`. En otra terminal, el frontend con `NEXT_PUBLIC_DRIFT_API_URL=http://localhost:8000` (`npm run dev` en `frontend/`). Sin `DRIFT_DATABASE_URL`, las cuentas viven en memoria y se borran al reiniciar la API.

| # | Paso | Resultado esperado | ✔ |
|---|---|---|---|
| G1 | Abrir `http://localhost:8000/auth/me` | `login_available: true`, `authenticated: false` | ☐ |
| G2 | En DRIFT, pulsar «Iniciar sesión con Google» y elegir tu cuenta | Vuelves a DRIFT con `?login=ok` y ves tu nombre | ☐ |
| G3 | Abrir `/auth/me` en el mismo navegador | `authenticated: true` con tu nombre y correo; nada más de Google | ☐ |
| G4 | Herramientas del navegador → Cookies | `drift_session` con `HttpOnly` y `SameSite=Lax`; ya no existen `drift_login_state` ni `drift_login_nonce` | ☐ |
| G5 | Guardar un dispositivo y un favorito, recargar la página | Siguen ahí | ☐ |
| G6 | Cerrar sesión | `/auth/me` vuelve a `authenticated: false` | ☐ |
| G7 | Empezar el inicio de sesión, esperar más de 10 minutos en la pantalla de Google y continuar | Vuelves con `?login=error` (venció el intento) | ☐ |
| G8 | Borrar la cuenta desde DRIFT | Desaparecen sesión, dispositivos y favoritos | ☐ |

Si G2 falla con `redirect_uri_mismatch`, la URI del paso 2 no coincide con `DRIFT_GOOGLE_REDIRECT_URI`. Si vuelve con `?login=error`, el registro de la API trae `login_rejected` con el motivo (nunca el token).

### Prueba en el laboratorio

Repite G1 a G8 en `https://drift.iscoutb.dev`, con `/api/auth/me` en lugar de `/auth/me`. Además:

| # | Paso | Resultado esperado | ✔ |
|---|---|---|---|
| G9 | Revisar la cookie `drift_session` | También tiene `Secure` | ☐ |
| G10 | Reiniciar la API desde Dokploy y recargar DRIFT | La sesión sigue (vive en PostgreSQL) | ☐ |

## 2. Laboratorio con PostgreSQL (`deploy/compose.lab.yaml`, ADR-0014)

### Qué ya está verificado

- El adaptador de PostgreSQL y sus migraciones se prueban en CI contra un PostgreSQL 17 desechable (`DRIFT_TEST_DATABASE_URL` en `.github/workflows/ci.yml`).
- El archivo es YAML válido. No se ha ejecutado con Docker.

### Qué falta

Que el compose arranque los tres servicios dentro de los límites de memoria (480 MB en total) y que la API use PostgreSQL de verdad.

### Prueba en tu computador (necesita Docker Desktop)

```bash
docker compose -p drift-prueba --env-file deploy/.env -f deploy/compose.lab.yaml config --quiet
```

```bash
docker compose -p drift-prueba --env-file deploy/.env -f deploy/compose.lab.yaml up -d --build
```

`deploy/.env` debe tener `DRIFT_DB_PASSWORD` (genérala con `python -c "import secrets; print(secrets.token_urlsafe(32))"`). Como el compose no publica puertos, la API se prueba desde dentro de su contenedor.

| # | Paso | Resultado esperado | ✔ |
|---|---|---|---|
| L1 | `config --quiet` sin `DRIFT_DB_PASSWORD` | Falla con «Define DRIFT_DB_PASSWORD en Dokploy» | ☐ |
| L2 | `config --quiet` con la contraseña | Termina sin errores | ☐ |
| L3 | `docker compose -p drift-prueba ps` tras 1 minuto | `api`, `web` y `postgres` en estado `healthy` | ☐ |
| L4 | `docker compose -p drift-prueba logs api` | Aparecen `snapshot_store_configured` y `account_store_configured` con `backend: postgres` | ☐ |
| L5 | `docker compose -p drift-prueba exec api python -c "import urllib.request as u; print(u.urlopen('http://localhost:8000/games/search?q=portal').status)"` | `200` | ☐ |
| L6 | `docker stats --no-stream` | Ningún servicio pasa su límite (api 192 MB, web 192 MB, postgres 96 MB) | ☐ |
| L7 | `docker compose -p drift-prueba restart api` y repetir L5 | `200`; las copias de respaldo siguen en PostgreSQL | ☐ |
| L8 | `docker compose -p drift-prueba stop postgres` y repetir L5 | `200`: la búsqueda funciona sin la base de datos (las cuentas responden 503) | ☐ |

Para limpiar: `docker compose -p drift-prueba down -v` (borra también el volumen de prueba).

## Dónde dejar el resultado

Anota fecha, commit y casillas en este archivo, y actualiza la fila correspondiente de [arc42 §11.11](../arc42/arc42-11-riesgos-y-deuda-tecnica.md). Si algo falla, deja el mensaje de error sin secretos.
