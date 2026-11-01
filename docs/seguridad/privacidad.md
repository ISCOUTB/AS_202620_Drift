# Privacidad: datos personales que trata DRIFT y con qué base

- **Commit de referencia:** `06fe18c` (merge del PR #49, 1 de noviembre de 2026)
- **Dueño:** JerryDBM
- **Marco aplicado:** Ley 1581 de 2012 de Colombia (protección de datos personales) y su decreto reglamentario 1377 de 2013, hoy compilado en el Decreto 1074 de 2015. Esta sección es la interpretación del equipo para un proyecto académico; no es una opinión jurídica.
- **Relacionado con:** [modelo de amenazas](modelo-amenazas.md), [arc42 §8.16](../arc42/arc42_8_conceptos_transversales.md) y [arc42 §11.9](../arc42/arc42-11-riesgos-y-deuda-tecnica.md)

## 1. Conclusión

DRIFT **sí trata datos personales**, aunque pocos: no tiene cuentas, formularios de registro, cookies ni analítica. El dato personal que trata es la **dirección IP** del visitante y, junto con ella en los registros de acceso, **lo que buscó**. El perfil del PC que el usuario guarda no lo identifica y no se conserva en el servidor.

## 2. Contraste con el modelo de datos

Antes de concluir se revisó qué datos guarda o recibe el sistema, no solo lo que dice la documentación.

- **Búsqueda de campos personales en el código** (excluye `docs/`):
  ```
  git grep -nIE '(email|correo|telefono|teléfono|cedula|cédula|documento|direccion|dirección|nombre_completo)' HEAD -- . ':!docs'
  ```
  Solo aparecen la palabra «dirección» en comentarios (direcciones URL de los catálogos de hardware) y «documento» en `correcciones.md`. **No hay** campos de nombre, correo, teléfono, documento de identidad ni dirección física.
- **Modelos del backend:** `Game`, `NormalizedGame`, `GameRequirements` y `HardwareBenchmark` describen videojuegos y hardware, no personas. `CompatibilityRequest` recibe solo números y nombres de componentes (RAM, puntaje y nombre de GPU y CPU, almacenamiento).
- **Modelo del frontend:** `PcProfile` (RAM, GPU, CPU, almacenamiento) se guarda en `localStorage` con la clave `drift.pcProfile` (`BrowserPcProfileRepository.js`).
- **Persistencia:** no hay base de datos (ADR-0008, ADR-0010). Todo lo que vive en el servidor está en la memoria del proceso y se pierde al reiniciar.
- **Lo que sí aparece al revisar la ejecución:**
  - la IP del cliente en el limitador de tasa (ADR-0012) y en el evento `admin_catalog_sync_requested` (ADR-0011);
  - la IP y la URL completa (con `?q=`) en el registro de acceso de uvicorn, que está activo por defecto (`backend/Dockerfile`);
  - los registros que guardan las plataformas de despliegue.

## 3. Inventario de datos

| Dato | ¿Es dato personal? | Dónde está | Para qué | Cuánto tiempo | Quién lo ve |
|---|---|---|---|---|---|
| **Dirección IP** del visitante | **Sí.** Combinada con los registros del proveedor de internet, puede identificar a una persona. | (a) Memoria del limitador de tasa. (b) Registro de acceso de uvicorn y registros de Azure App Service, Vercel y Traefik (Dokploy). (c) Evento `admin_catalog_sync_requested`. | Seguridad: limitar el abuso (A3) y auditar operaciones administrativas (A10). Operación: diagnosticar fallos. | (a) Como máximo 60 s, solo en memoria. (b) y (c) Según la retención de cada plataforma. DRIFT no los exporta ni los copia a otro lugar. | El equipo DRIFT y los proveedores de alojamiento como encargados. |
| **Término de búsqueda** | **Sí, cuando va junto a la IP** en el registro de acceso (la URL incluye `?q=`). Por sí solo, no. | Registro de acceso de uvicorn y de las plataformas. Los registros propios de DRIFT **no** guardan la consulta, solo su longitud. | Operación de la búsqueda. | Según la retención de cada plataforma. | El equipo y los proveedores. |
| **Perfil del PC** (RAM, GPU, CPU, almacenamiento) | **No:** describe un equipo y no identifica a nadie. | `localStorage` del navegador del usuario. Viaja en el cuerpo de `POST /games/{id}/compatibility` en cada consulta. | Estimar la compatibilidad. | En el navegador, hasta que el usuario borre los datos del sitio. En el servidor, solo mientras dura la petición: no se guarda ni se registra. | Solo el usuario, en su navegador. |
| Datos de videojuegos, precios y requisitos | No | Memoria del backend (cachés) | Funcionalidad principal | TTL de cada caché (arc42 §8.14) | Público |

**No se tratan:** nombres, correos, teléfonos, documentos de identidad, direcciones físicas, datos de pago, cuentas de usuario, cookies, identificadores de publicidad ni herramientas de analítica. Tampoco datos sensibles (art. 5) ni datos de menores (art. 7).

## 4. Base del tratamiento

- **Regla general (Ley 1581, art. 9):** el tratamiento requiere la autorización previa, expresa e informada del titular. El Decreto 1377 de 2013 (art. 7) admite obtenerla mediante **conductas inequívocas** del titular. Así se plantea para DRIFT: el visitante que usa el sitio después de ver el aviso de privacidad autoriza el tratamiento mínimo descrito arriba.
- **Finalidades informadas:** prestar la búsqueda y la estimación de compatibilidad, proteger el servicio contra el abuso y diagnosticar fallos. Ninguna otra. La IP no se usa para perfilar, ni para publicidad, ni se cede a terceros.
- **Principios aplicados (Ley 1581, art. 4):**
  - **Finalidad y libertad:** solo para lo dicho y con autorización.
  - **Necesidad y minimización:** no hay cuentas; los registros propios no guardan la consulta; el limitador olvida la IP a los 60 s.
  - **Seguridad:** HTTPS, sin base de datos y operaciones administrativas con token.
  - **Acceso restringido:** solo el equipo y los encargados del alojamiento.
- **Encargados del tratamiento:** Microsoft Azure (App Service, región `mexicocentral`), Vercel y el servidor del laboratorio de la universidad (Dokploy). Azure y Vercel están fuera de Colombia, así que hay **transferencia internacional** (Ley 1581, art. 26). Se asume bajo las condiciones contractuales de esos proveedores y se declara aquí para que sea visible.
- **Derechos del titular (consultar, actualizar, suprimir):** DRIFT no puede asociar una IP con una persona concreta, ni tiene cuentas donde consultar datos. Una solicitud se atiende a través del canal de contacto del aviso de privacidad, en la medida en que sea posible localizar los registros.

## 5. Medidas de protección

| Medida | Dónde |
|---|---|
| No hay base de datos ni datos de usuario en el servidor | ADR-0008, ADR-0010 |
| El perfil del PC se queda en el navegador del usuario | `BrowserPcProfileRepository.js` |
| Los registros propios no guardan la consulta, solo su longitud | `main.py` (`search_completed`, `search_failed`), prueba `test_logs_report_retries_and_failures_without_the_user_query` |
| El limitador guarda la IP solo en memoria y como máximo 60 s | `SlidingWindowRateLimiter`, ADR-0012 |
| Las operaciones administrativas y `/metrics` exigen token | ADR-0011 |
| HTTPS obligatorio y TLS 1.2 como mínimo en Azure | `infra/azure/main.bicep` (`httpsOnly`, `minTlsVersion`) |
| CORS sin credenciales y sin cookies | ADR-0012 |

## 6. Pendientes

| # | Pendiente | Dueño | Estado |
|---|---|---|---|
| P1 | Publicar el aviso de privacidad (§7) en el pie de página del frontend, con un canal de contacto del equipo | JerryDBM | **Hecha:** enlace «Privacidad» en el pie (`DriftHome.js`); el contacto son los *issues* del repositorio |
| P2 | Decidir si se desactiva el registro de acceso de uvicorn (`--no-access-log`) para no guardar la URL con la consulta. Los registros estructurados de DRIFT ya cubren la operación; las plataformas seguirán registrando la IP. | JerryDBM | Pendiente |

## 7. Texto del aviso de privacidad (publicado en el pie de página)

> **Privacidad.** DRIFT no pide registro ni usa cookies. Para funcionar y protegerse contra el abuso, el servicio y sus proveedores de alojamiento (Microsoft Azure, Vercel y el servidor de la Universidad Tecnológica de Bolívar) registran tu dirección IP y las búsquedas que haces, solo para operar y diagnosticar el servicio. El perfil de tu PC se guarda únicamente en tu navegador. Al usar el sitio aceptas este tratamiento, conforme a la Ley 1581 de 2012. Consultas sobre tus datos: abre un caso en el repositorio del proyecto (https://github.com/ISCOUTB/AS_202620_Drift/issues).
