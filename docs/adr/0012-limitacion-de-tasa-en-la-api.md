# ADR-0012: Limitación de tasa en las rutas que llaman a fuentes externas

- **Estado:** Aceptado
- **Fecha:** 2026-11-01
- **Decisores:** Equipo de desarrollo de DRIFT
- **Mitiga:** amenaza A3 del [modelo de amenazas](../seguridad/modelo-amenazas.md); incluye el ajuste de CORS de la amenaza A9
- **Relacionado con:** [ADR-0008](0008-persistencia-ejecucion-y-degradacion-de-fuentes.md) (estado en memoria, un proceso) y [ADR-0009](0009-decision-extraccion-integracion-steam.md) (resiliencia frente a Steam)

## Contexto

Cada `GET /games/search` puede consultar hasta cuatro fuentes externas (Steam, CheapShark, PlayStation y open.er-api), y cada `POST /games/{id}/compatibility` puede consultar Steam. Ninguna ruta limitaba cuántas peticiones hacía un mismo cliente.

Un abuso tiene dos efectos (amenaza A3: P2 × I3 = **6, Alta**):

- **Agota los recursos:** los contenedores del laboratorio tienen 192 MB y medio CPU.
- **Hace que bloqueen a DRIFT:** open.er-api bloquea 20 minutos ante abuso (arc42 §8.14) y Steam responde 429. El daño lo pagan todos los usuarios.

La caché de 60 s (`SingleFlightCache`) protege frente a la misma consulta repetida, pero no frente a consultas distintas.

## Alternativas

1. **Limitador propio en memoria**, por IP de cliente, como middleware de FastAPI. Sin dependencias nuevas; usa el mismo modelo que las cachés (estado en un proceso, ADR-0008).
2. **Librería `slowapi`.** Agrega una dependencia más (y su cadena de dependencias al análisis del pipeline) para la misma ventana en memoria.
3. **Límite en el proxy** (middleware `RateLimit` de Traefik en Dokploy). Solo cubre el servidor del laboratorio: Azure App Service en plan F1 no ofrece un equivalente, y el frontend de Vercel llama a Azure.
4. **Almacén compartido (Redis)** para contar entre instancias. Hoy hay una instancia por entorno y ADR-0010 descarta añadir infraestructura de datos sin necesidad.

## Decisión

Se adopta la **alternativa 1**.

- `SlidingWindowRateLimiter` (`backend/app/infrastructure/api/security.py`): ventana deslizante de 60 s por clave de cliente, protegida con `Lock`. Olvida a los clientes inactivos para que la tabla no crezca sin límite.
- **Se aplica solo** a `GET /games/search` y `POST /games/{id}/compatibility`. `/health`, el catálogo de hardware y las rutas administrativas no se limitan.
- **Límite:** `DRIFT_RATE_LIMIT_PER_MINUTE`, 60 por defecto; `0` lo desactiva (así lo usa el experimento E6 en `scripts/e6_corrida.py`).
- **Respuesta al superar el límite:** 429 con `Retry-After` y el evento `rate_limited` en el log estructurado. Está documentada en el contrato OpenAPI 1.5.0.
- **IP del cliente detrás de un proxy:** con `DRIFT_TRUST_FORWARDED_FOR=true` se usa la **última** entrada de `X-Forwarded-For`, que es la que escribe el proxy de confianza (las anteriores las puede inventar el cliente). Se quita el puerto que añade Azure. Está activada en Dokploy (Traefik) y en Azure.
- **CORS (A9), en el mismo cambio de middleware:** `allow_credentials=False` (DRIFT no usa cookies), solo `GET` y `POST`, y solo la cabecera `Content-Type`. El middleware de CORS queda por fuera del limitador para que el navegador pueda leer también las respuestas 429.

## Consecuencias

**Positivas**

- Un solo cliente ya no puede generar más de 60 búsquedas o estimaciones por minuto, ni las llamadas salientes que generan.
- El cambio no toca el dominio ni los casos de uso.
- Pruebas en `test_s13_seguridad_api.py`: límite, ventana, separación por cliente, 429 con `Retry-After`, rutas no limitadas, `X-Forwarded-For` y CORS.

**Negativas y riesgos aceptados**

- **La cuenta es por proceso:** con varias instancias, cada una permite 60 por minuto. Es la misma limitación de consistencia que las cachés (arc42 §8.13).
- **Varias personas detrás de una misma IP** (por ejemplo, la red de la universidad) comparten el límite. 60 por minuto es holgado para un uso normal, y se ajusta con la variable sin desplegar código.
- **El despliegue serverless de Vercel** (`deployment/vercel/api/index.py`) es otra aplicación y no incluye el limitador. Su escala la controla la plataforma; se registra como riesgo en arc42 §11.
- **Las pruebas de carga** desde una sola máquina deben desactivar el límite (`DRIFT_RATE_LIMIT_PER_MINUTE=0`); de lo contrario medirían respuestas 429.

## Cambio estructural

Se añade al contenedor **Backend / API** un middleware de entrada que corta las peticiones antes de que lleguen a los casos de uso. También se añaden dos variables de configuración por entorno (`DRIFT_RATE_LIMIT_PER_MINUTE` y `DRIFT_TRUST_FORWARDED_FOR`).
