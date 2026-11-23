# Privacidad: datos personales que trata DRIFT y con qué base

- **Estado que describe:** `master` en `a0e18f9` (16 de noviembre de 2026), con cuentas de Google, PostgreSQL, favoritos y alertas. Reemplaza la versión de S13, que partía de un sistema sin cuentas ni base de datos (commit de referencia `06fe18c`).
- **Dueño:** JerryDBM
- **Marco aplicado:** Ley 1581 de 2012 de Colombia (protección de datos personales) y su decreto reglamentario 1377 de 2013, hoy compilado en el Decreto 1074 de 2015. Esta sección es la interpretación del equipo para un proyecto académico; no es una opinión jurídica.
- **Relacionado con:** [modelo de amenazas](modelo-amenazas.md), [arc42 §8.16](../arc42/arc42_8_conceptos_transversales.md), [arc42 §11.9](../arc42/arc42-11-riesgos-y-deuda-tecnica.md), [ADR-0014](../adr/0014-postgresql-como-persistencia.md), [ADR-0017](../adr/0017-inicio-de-sesion-con-google-y-dispositivos.md), [ADR-0020](../adr/0020-juegos-favoritos.md) y [ADR-0021](../adr/0021-alertas-de-precio.md)

## 1. Conclusión

DRIFT **trata datos personales en dos niveles**:

- **Quien usa el sitio sin iniciar sesión** deja su **dirección IP** y, junto con ella en los registros de acceso, **lo que buscó**. Su perfil de PC se queda en su navegador.
- **Quien inicia sesión con Google es identificable.** DRIFT guarda en PostgreSQL su nombre, su correo, la dirección de su foto, sus dispositivos, sus favoritos y la huella de su sesión.

DRIFT no pide contraseñas, no guarda los tokens de Google, no trata datos de pago y no usa cookies de analítica ni de publicidad.

## 2. Contraste con el modelo de datos

Se revisó qué datos guarda o recibe el sistema, no solo lo que dice la documentación.

- **Esquema de PostgreSQL** (`backend/app/infrastructure/persistence/postgres_database.py`): `app_user`, `user_session`, `user_device`, `user_favorite`, `source_snapshot`, `hardware_benchmark_set` y `hardware_benchmark`. Las cuatro primeras están ligadas a una persona; las de sesión, dispositivos y favoritos se borran en cascada con su cuenta (`ON DELETE CASCADE`).
- **`source_snapshot`** guarda el texto de las búsquedas y la respuesta de cada tienda. No tiene columna de IP, sesión ni usuario.
- **Modelo de cuentas:** `backend/app/domain/model/account.py`.
- **Modelo del frontend:** sin sesión, `PcProfile` se guarda en `localStorage` con la clave `drift.pcProfile` (`BrowserPcProfileRepository.js`).
- **Lo que aparece al revisar la ejecución:**
  - la IP del cliente en el limitador de tasa (ADR-0012) y en el evento `admin_catalog_sync_requested` (ADR-0011);
  - la IP y la URL completa (con `?q=`) en el registro de acceso de uvicorn, que está activo por defecto (`backend/Dockerfile`);
  - los registros que guardan las plataformas de despliegue.

## 3. Inventario de datos

| Dato | ¿Es dato personal? | De quién | Dónde está | Para qué | Cuánto tiempo | Quién lo ve |
|---|---|---|---|---|---|---|
| **Dirección IP** | **Sí.** Combinada con los registros del proveedor de internet, puede identificar a una persona. | Todo visitante | Memoria del limitador; registro de acceso de uvicorn y de Traefik (Dokploy); evento `admin_catalog_sync_requested` | Limitar el abuso (A3), auditar operaciones administrativas (A10) y diagnosticar fallos | Limitador: máximo 60 s, en memoria. Registros: según la retención de cada plataforma | El equipo y el alojamiento como encargado |
| **Término de búsqueda en el registro de acceso** | **Sí, cuando va junto a la IP** | Todo visitante | Registro de acceso de uvicorn y de las plataformas. Los registros propios de DRIFT solo guardan su longitud | Operar la búsqueda | Según la retención de cada plataforma | El equipo y el alojamiento |
| **Término de búsqueda en la copia de respaldo** | No por sí solo: se guarda sin IP, sesión ni usuario | Todo visitante | PostgreSQL (`source_snapshot`) | Responder cuando una fuente falla (ADR-0015) | 72 horas | El equipo |
| **Perfil del PC sin sesión** | No: describe un equipo | Todo visitante | `localStorage`. Viaja en el cuerpo de `POST /games/{id}/compatibility` y no se guarda en el servidor | Estimar la compatibilidad | Hasta que el usuario borre los datos del sitio | Solo el usuario |
| **Identificador de Google, correo, nombre y dirección de la foto** | **Sí** | Quien inicia sesión | PostgreSQL (`app_user`) | Reconocer a la persona cuando vuelve | Hasta que borre su cuenta | La persona y el equipo |
| **Huella de la sesión y su vencimiento** | **Sí, ligada a la cuenta.** Solo se guarda su SHA-256 | Quien inicia sesión | PostgreSQL (`user_session`) | Mantener la sesión | 30 días o hasta cerrar sesión | Nadie la usa directamente |
| **Dispositivos**: nombre, tipo y, en un PC, sus componentes | **Sí, por estar ligados a la cuenta** | Quien inicia sesión | PostgreSQL (`user_device`) | Filtrar tiendas, estimar compatibilidad y recomendar | Hasta que los borre o borre su cuenta | La persona y el equipo |
| **Favoritos**: juego, imagen, precio y tienda al guardarlo, y precio objetivo | **Sí, por estar ligados a la cuenta** | Quien inicia sesión | PostgreSQL (`user_favorite`) | Mostrar su lista y avisar cambios de precio | Hasta que los quite o borre su cuenta | La persona y el equipo |
| **Cookies** `drift_session`, `drift_login_state` y `drift_login_nonce` | Identifican una sesión o un intento de inicio | Quien inicia sesión | Navegador | Mantener la sesión y proteger el inicio de sesión | Sesión: 30 días. Las otras dos: 10 minutos | La persona y la API |
| Datos de videojuegos, precios y requisitos | No | — | Memoria y PostgreSQL | Funcionalidad principal | TTL de cada caché (arc42 §8.14) | Público |

**No se tratan:** contraseñas, tokens de Google, teléfonos, documentos de identidad, direcciones físicas, datos de pago, identificadores de publicidad ni herramientas de analítica. No se recogen datos sensibles (art. 5). DRIFT no verifica la edad de quien inicia sesión y no está dirigido a menores (art. 7).

## 4. Base del tratamiento

- **Regla general (Ley 1581, art. 9):** el tratamiento requiere la autorización previa, expresa e informada del titular. El Decreto 1377 de 2013 (art. 7) admite obtenerla mediante **conductas inequívocas**.
  - **Sin sesión:** quien usa el sitio después de ver el aviso autoriza el tratamiento mínimo descrito.
  - **Con sesión:** la persona decide iniciar sesión y Google le muestra qué datos comparte.
- **Finalidades informadas:** prestar la búsqueda, la compatibilidad, la recomendación, los favoritos y las alertas; proteger el servicio contra el abuso y diagnosticar fallos. Ninguna otra.
- **Principios aplicados (Ley 1581, art. 4):**
  - **Finalidad y libertad:** solo para lo dicho; usar DRIFT no exige cuenta.
  - **Necesidad y minimización:** solo se piden los permisos `openid`, `email` y `profile`. Los registros propios no guardan la consulta y el limitador olvida la IP a los 60 s.
  - **Seguridad:** HTTPS, cookies `HttpOnly` y `SameSite=Lax`, huella de sesión en lugar del identificador y operaciones administrativas con token.
  - **Acceso restringido:** solo el equipo y el encargado del alojamiento.
- **Encargado del tratamiento:** el servidor del laboratorio de la universidad (Dokploy). Desde el 13 de noviembre de 2026 DRIFT ya no usa Microsoft Azure ni Vercel ([ADR-0022](../adr/0022-desplegar-solo-en-el-laboratorio.md)).
- **Terceros:**
  - **Google**, como proveedor de identidad: sabe que la persona inició sesión en DRIFT.
  - **Steam, CheapShark, PlayStation, IsThereAnyDeal y la tienda de Xbox** reciben el texto de las búsquedas. No reciben la IP ni la identidad del visitante.
  - Para las alertas de precio (ADR-0021), Steam e IsThereAnyDeal reciben los identificadores de los juegos favoritos, sin decir de quién son.

### Derechos del titular

| Derecho | Cómo se ejerce |
|---|---|
| **Consultar** | «Mi cuenta» muestra el nombre, el correo y los dispositivos; la pestaña «Favoritos», los juegos guardados |
| **Actualizar** | El nombre, el correo y la foto se actualizan desde Google en cada inicio de sesión; dispositivos y favoritos se editan en DRIFT |
| **Suprimir** | «Eliminar mi cuenta» (`DELETE /auth/me`) borra la cuenta, sus sesiones, sus dispositivos y sus favoritos |
| **Sin cuenta** | Una solicitud se atiende por el canal del aviso, en la medida en que se puedan localizar los registros: DRIFT no puede asociar por sí solo una IP con una persona |

Una copia de seguridad de PostgreSQL contiene estos datos personales: se guarda fuera del repositorio y una cuenta borrada puede seguir en una copia anterior hasta que esa copia se elimine.

## 5. Medidas de protección

| Medida | Dónde |
|---|---|
| Solo se guarda la huella SHA-256 del identificador de sesión | `test_only_the_hash_of_the_session_token_is_stored` |
| Cookies `HttpOnly`, `SameSite=Lax` y, por HTTPS, `Secure` | ADR-0017 |
| Comprobación del `Origin` en toda petición que cambia datos | `test_changes_from_another_site_are_refused`, `test_favorite_changes_from_another_site_are_refused` |
| Cada usuario solo accede a sus dispositivos y favoritos | `test_one_user_cannot_touch_the_devices_of_another`, `test_one_user_does_not_see_the_favorites_of_another` |
| Borrar la cuenta borra sus datos en cascada | `postgres_database.py`, `test_deleting_an_account_removes_its_favorites` |
| CORS con credenciales solo para orígenes configurados | `test_cors_allows_credentials_only_for_the_configured_origin` |
| Sin sesión, el perfil del PC se queda en el navegador | `BrowserPcProfileRepository.js` |
| Los registros propios no guardan la consulta, solo su longitud | `main.py`, `test_logs_report_retries_and_failures_without_the_user_query` |
| El limitador guarda la IP solo en memoria y como máximo 60 s | `SlidingWindowRateLimiter`, ADR-0012 |
| Las operaciones administrativas y `/metrics` exigen token | ADR-0011 |
| HTTPS: lo termina el proxy Traefik del laboratorio | `deploy/compose.lab.yaml` |

## 6. Pendientes

| # | Pendiente | Dueño | Estado |
|---|---|---|---|
| P1 | Publicar el aviso de privacidad en el pie de página, con un canal de contacto | JerryDBM | **Hecha:** enlace «Privacidad» en el pie (`DriftHome.js`); el contacto son los *issues* del repositorio |
| P2 | Decidir si se desactiva el registro de acceso de uvicorn (`--no-access-log`) para no guardar la URL con la consulta | JerryDBM | Pendiente |
| P3 | Copias de seguridad de PostgreSQL | Equipo | **Parcial:** procedimiento en [verificaciones pendientes](../evidencias/verificaciones-pendientes-google-y-laboratorio.md), sección 3; todavía no se ha ejecutado en el laboratorio |
| P4 | Registrar la fecha en que la persona aceptó el tratamiento | Equipo | Pendiente |
| P5 | Probar con una cuenta real en el laboratorio el borrado de la cuenta (casillas G1 a G10 de la misma guía) | Equipo | Pendiente |

## 7. Texto del aviso de privacidad (publicado en el pie de página)

> **Privacidad.** Puedes usar DRIFT sin registrarte. Para funcionar y protegerse contra el abuso, el servicio y sus proveedores de alojamiento (el servidor de la Universidad Tecnológica de Bolívar) registran tu dirección IP y las búsquedas que haces, solo para operar y diagnosticar el servicio. El texto de las búsquedas se conserva hasta 72 horas, sin asociarlo a ti, como copia de respaldo de las tiendas. Sin sesión, el perfil de tu PC se guarda únicamente en tu navegador.
>
> Si inicias sesión con Google, DRIFT guarda tu nombre, tu correo y tu foto de perfil, los dispositivos que registres y los juegos que guardes en favoritos, para mostrarlos cuando vuelvas. Solo usa las cookies necesarias para iniciar y mantener tu sesión. Puedes borrar tu cuenta y todos esos datos desde «Mi cuenta». Al usar el sitio aceptas este tratamiento, conforme a la Ley 1581 de 2012.
>
> Consultas sobre tus datos: abre un caso en el repositorio del proyecto (https://github.com/ISCOUTB/AS_202620_Drift/issues).
