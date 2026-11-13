# ADR-0017: Iniciar sesión con Google y registrar los dispositivos del usuario

- **Estado:** Propuesto
- **Fecha:** 2026-11-12
- **Decisores:** Equipo de desarrollo de DRIFT
- **Modifica a:** [ADR-0012](0012-limitacion-de-tasa-en-la-api.md), en la configuración de CORS: los orígenes permitidos ahora pueden enviar credenciales. El límite de tasa no cambia.
- **Relacionado con:** [ADR-0011](0011-autenticacion-operaciones-administrativas.md) (el token administrativo sigue igual y es independiente), [ADR-0014](0014-postgresql-como-persistencia.md), [modelo de amenazas](../seguridad/modelo-amenazas.md) y [privacidad](../seguridad/privacidad.md)

## Contexto

La ficha del problema pide **«registrar los dispositivos del usuario»**. Hasta ahora DRIFT guardaba un solo PC, en el navegador: no había consolas, no se podía tener más de un equipo y nada pasaba de un navegador a otro.

Guardar dispositivos en el servidor exige saber de quién son. DRIFT no tenía usuarios: ADR-0011 solo cubre un token de servicio para dos operaciones administrativas.

## Alternativas

1. **Iniciar sesión con Google (OpenID Connect).** DRIFT no guarda contraseñas ni maneja su recuperación. Costo: depende de Google y de un cliente OAuth que alguien del equipo administra.
2. **Cuentas propias con correo y contraseña.** No depende de terceros, pero obliga a guardar contraseñas, verificar correos, recuperar cuentas y proteger el inicio de sesión contra fuerza bruta. Es la opción con más superficie de ataque.
3. **Varios dispositivos solo en el navegador, sin cuentas.** Cumple la letra de la ficha sin datos personales nuevos. No sirve entre navegadores y cierra el paso a alertas de precio o favoritos.
4. **Enlace mágico por correo.** Sin contraseñas, pero necesita un servicio de envío de correos que DRIFT no tiene.

## Decisión

Se adopta la **alternativa 1**. El equipo la eligió expresamente, y es la que menos secretos pone a cargo de DRIFT.

### Cómo funciona el inicio de sesión

1. La página lleva a la persona a `GET /auth/google/login`. La API genera un `state` y un `nonce` al azar, los deja en dos cookies de 10 minutos y la redirige a Google.
2. Google la devuelve a `GET /auth/google/callback` con un código. La API comprueba que el `state` coincide con el de la cookie y cambia el código por un `id_token`, hablando directamente con Google.
3. Con esa identidad crea o actualiza la cuenta, abre una sesión de 30 días y devuelve a la persona a la página.

Solo se piden los permisos `openid`, `email` y `profile`. De Google se guardan cuatro datos: su identificador de la cuenta, el correo, el nombre y la dirección de la foto.

### Decisiones de seguridad

| Decisión | Razón |
|---|---|
| La sesión es un identificador al azar en una cookie `HttpOnly`, `SameSite=Lax` y, por HTTPS, `Secure` | El código de la página no puede leerla, y el navegador no la envía en peticiones que inicia otro sitio |
| En la base de datos solo se guarda la huella (SHA-256) del identificador de sesión | Quien lea la base no obtiene sesiones utilizables |
| Toda petición que cambia datos debe traer un `Origin` de la lista permitida | Segunda barrera contra peticiones falsificadas desde otro sitio (CSRF) |
| `state` comparado contra la cookie del navegador | Nadie puede completar un inicio de sesión que esta persona no empezó |
| `nonce` dentro del `id_token` | La respuesta de Google pertenece a este intento y no a uno anterior |
| Se comprueban el emisor, el destinatario, el vencimiento y que el correo esté verificado | Un token de otro cliente o vencido no sirve |
| **No se verifica la firma del `id_token`** | El token llega directamente de Google por HTTPS, no a través del navegador. OpenID Connect permite omitir la firma en ese caso, y así no se añade una librería criptográfica |
| Después de iniciar sesión se vuelve siempre a `DRIFT_FRONTEND_URL` | La dirección de regreso no sale de la petición: no hay redirección abierta |
| Ni el código, ni los tokens, ni el secreto se registran | Los registros no pueden filtrar una sesión |
| El identificador interno del usuario y el de Google no salen de la API | La página solo recibe nombre, correo y foto |

### Dispositivos

- Un dispositivo es un PC (con memoria, gráfica y, opcionales, procesador y espacio libre) o una consola (PlayStation o Xbox), con un nombre.
- Máximo 10 por cuenta.
- Rutas: `GET` y `POST /devices`, `PUT` y `DELETE /devices/{id}`. Cada una actúa solo sobre los dispositivos de quien tiene la sesión.
- `DELETE /auth/me` borra la cuenta con sus sesiones y dispositivos, en cascada.

### Dónde se guardan

- Con `DRIFT_DATABASE_URL`: PostgreSQL (tablas `app_user`, `user_session` y `user_device`).
- Sin ella: en memoria, solo para desarrollo y pruebas.
- **Si PostgreSQL falla, las cuentas responden «no disponible» (503).** No hay un segundo almacén en memoria como en la copia de respaldo de las fuentes: guardar un dispositivo y perderlo después sería peor que avisar. La búsqueda de juegos no depende de las cuentas y sigue funcionando.

### Sin configuración, DRIFT sigue igual

Sin `DRIFT_GOOGLE_CLIENT_ID` y `DRIFT_GOOGLE_CLIENT_SECRET`, el inicio de sesión queda deshabilitado: la página no muestra el botón y todo lo demás funciona como antes, con el perfil del PC en el navegador.

## Consecuencias

**A favor**

- Se cumple el punto de los dispositivos de la ficha, con varios equipos y consolas por persona.
- DRIFT no guarda contraseñas.
- Queda la base para alertas de precio, favoritos y la recomendación por dispositivo.

**En contra**

- **DRIFT pasa a guardar datos personales identificables** (nombre, correo, foto). Cambia lo que dice [privacidad](../seguridad/privacidad.md) y exige atender solicitudes de borrado: por eso existe `DELETE /auth/me`.
- **CORS ahora permite credenciales.** Sigue acotado a los orígenes configurados; un comodín (`*`) en `CORS_ALLOWED_ORIGINS` sería ahora un error grave.
- **A partir de aquí PostgreSQL guarda datos que nadie puede reponer.** El volumen no tiene copias de seguridad (ADR-0014). Es la decisión de datos más cara de revertir del proyecto (ADR-0010, punto 3).
- Si Google no responde, nadie puede iniciar sesión; quien ya tiene sesión no se ve afectado.
- Mientras el cliente OAuth esté en modo «Prueba», solo pueden entrar los correos que el equipo agregue en Google Cloud, hasta 100.
- **Solo funciona donde la página y la API están en el mismo sitio** (el laboratorio y `localhost`). Entre Vercel y Azure, que son dominios distintos, el navegador no envía la cookie; además allí no hay base de datos.
- Una sesión robada sirve hasta 30 días o hasta que la persona cierre sesión. No hay una pantalla para ver ni cerrar las sesiones de otros navegadores.

## Lo que se verificó y lo que no

- **Verificado con pruebas** (`backend/tests/test_cuentas.py`): el recorrido completo con un proveedor simulado; el rechazo sin `state`, con un `state` ajeno, con un código inválido y con Google caído; los seis casos en que el `id_token` no cuadra; que un usuario no puede ver, cambiar ni borrar dispositivos de otro; el rechazo de cambios desde otro origen; el borrado de la cuenta en cascada; y el almacén caído.
- **Verificado contra un PostgreSQL 16.2 real:** las mismas pruebas del almacén de cuentas, y la migración 2 aplicada sobre una base que ya tenía la 1.
- **Verificado en un equipo de desarrollo:** con el cliente real, `GET /auth/google/login` redirige a Google con los parámetros y las cookies esperados.
- **No verificado: un inicio de sesión real de punta a punta.** Requiere que una persona entre con su cuenta de Google, y que la URI de regreso esté registrada en el cliente.
- **No verificado:** el comportamiento de las cookies detrás de Traefik en el laboratorio (`/api` con *Strip Path*).

## Cuándo revisar esta decisión

- Se quiere que el inicio de sesión funcione entre Vercel y Azure: habría que cambiar la cookie por otro mecanismo o poner ambos bajo un mismo dominio.
- Google cambia las condiciones de su inicio de sesión.
- Se agregan funciones con datos más sensibles: verificar la firma del `id_token` y acortar la sesión.
