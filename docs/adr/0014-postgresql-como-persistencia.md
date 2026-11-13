# ADR-0014: Adoptar PostgreSQL como persistencia de DRIFT

- **Estado:** Propuesto
- **Fecha:** 2026-11-12
- **Decisores:** Equipo de desarrollo de DRIFT
- **Sustituye a:** [ADR-0008](0008-persistencia-ejecucion-y-degradacion-de-fuentes.md), solo en su decisión de persistencia («todo en memoria»). La ejecución síncrona y la degradación controlada de fuentes siguen vigentes.
- **Modifica a:** [ADR-0010](0010-costo-de-reversion-de-las-decisiones-de-datos.md), en su conclusión de no añadir infraestructura de datos: la condición que él mismo fijó para revisarla ya se cumple (ver «Contexto»).
- **Relacionado con:** [ADR-0015](0015-copia-de-respaldo-de-las-fuentes.md), que es el primer uso de esta base de datos.

## Contexto

ADR-0008 eligió guardar todo en memoria con este argumento: «DRIFT no guarda datos propios del usuario ni histórico». ADR-0010 dejó escrito cuándo habría que revisarlo: cuando «se planea una función que guarde datos propios del usuario en el servidor (favoritos, alertas, historial de precios, cuentas)».

Ese momento llegó por dos razones:

1. **Disponibilidad.** El peor caso para DRIFT es que alguien busque un juego y una tienda no devuelva nada. Para evitarlo hace falta guardar la última respuesta de cada fuente (ADR-0015). En memoria, esa copia se pierde en cada despliegue: hay uno por cada push a `master`, y es justo después de un despliegue cuando el respaldo arranca vacío.
2. **La ficha del problema.** Pide «registrar los dispositivos del usuario». El equipo decidió hacerlo con cuentas (inicio de sesión con Google, que se registrará en su propio ADR). Cuentas y dispositivos son datos que ninguna tienda puede reponer si se pierden.

Restricciones que pesan en la decisión:

- El laboratorio da 512 MB en total. `api` y `web` usan 192 MB cada uno: quedan 128 MB.
- Las reglas del laboratorio prohíben los *bind mounts*. No dicen nada de los volúmenes con nombre.
- Azure App Service y Vercel no tienen base de datos y no se va a pagar una.

## Alternativas

1. **PostgreSQL.** Base relacional. Sirve para los datos propios (usuarios, dispositivos) y también para la copia de respaldo. Un solo servicio. Costo: unos 64 a 96 MB, migraciones y un secreto más.
2. **Redis.** Hecho para cachés: vencimiento incluido y muy poca memoria. Pero no es adecuado como fuente de verdad de datos que no se pueden reconstruir, así que para las cuentas haría falta otra base más adelante.
3. **PostgreSQL y Redis.** Cada uno en lo suyo. No cabe con holgura en los 128 MB libres y son dos servicios que operar.
4. **MySQL** (lo que proponía ADR-0004). Equivalente a PostgreSQL para este uso. El profesor recomendó Redis o PostgreSQL, y PostgreSQL tiene `jsonb`, que simplifica guardar las copias.
5. **SQLite en un volumen.** Lo más liviano, pero un solo proceso escribe a la vez y no sirve si algún día hay más de una instancia de la API.
6. **Seguir en memoria.** No resuelve ninguna de las dos razones del contexto.

## Decisión

Se adopta la **alternativa 1: PostgreSQL**, como único servicio de datos.

- **Servicio:** `postgres:17-alpine` en `deploy/compose.lab.yaml`, con límite de 96 MB, ajustes de memoria mínimos (`shared_buffers=16MB`, `max_connections=12`) y un volumen con nombre (`drift_pgdata`). No publica puertos: solo la API lo alcanza por la red interna del compose.
- **Acceso:** `psycopg` 3 con un pool de conexiones (`backend/app/infrastructure/persistence/postgres_database.py`). No se usa un ORM: hoy hay una sola tabla y SQL directo es más simple y gasta menos memoria.
- **Esquema:** migraciones numeradas en el mismo archivo. Se aplican solas en la primera conexión que funcione, protegidas por un candado de PostgreSQL para que dos procesos no migren a la vez.
- **Configuración:** `DRIFT_DATABASE_URL`. Sin ella no se usa PostgreSQL y todo funciona en memoria, como antes.
- **Arquitectura:** el dominio no conoce PostgreSQL. Define el puerto `SourceSnapshotStore`; PostgreSQL es un adaptador más, igual que cada tienda.

### La base de datos no puede tumbar la búsqueda

Añadir una base de datos no debe crear un punto de falla nuevo. Por eso:

| Situación | Qué hace DRIFT |
|---|---|
| PostgreSQL caído al arrancar | La API arranca igual. El pool se abre sin esperar y reintenta por su cuenta. |
| PostgreSQL deja de responder | La operación espera como máximo 0,25 s por una conexión y 0,5 s por sentencia. Después se deja de llamar a la base durante 30 s y se usa la copia en memoria. |
| PostgreSQL vuelve | Pasados los 30 s se intenta de nuevo y se sigue con normalidad. |
| No hay `DRIFT_DATABASE_URL` (Azure, Vercel, desarrollo) | Solo copia en memoria. El controlador de PostgreSQL ni siquiera se importa. |

Esto lo hace `ResilientSourceSnapshotStore`, que escribe cada copia en PostgreSQL y en memoria.

## Consecuencias

**A favor**

- Las copias de respaldo sobreviven a reinicios y despliegues.
- Queda lista la base para usuarios y dispositivos sin añadir otro servicio.
- El costo de volver atrás es bajo mientras solo guarde copias: se quita `DRIFT_DATABASE_URL` y DRIFT vuelve a funcionar en memoria, sin cambiar código.

**En contra**

- El laboratorio pasa de 384 MB a 480 MB de los 512 MB. Queda poco margen.
- Un secreto más (`DRIFT_DB_PASSWORD`). Sin él, el despliegue del laboratorio se detiene con un mensaje claro.
- El CI necesita un PostgreSQL de servicio para probar el adaptador.
- **A partir del primer dato propio del usuario, esta pasa a ser la decisión de datos más cara de revertir** (ADR-0010, punto 3): harán falta copias de seguridad y migraciones cuidadosas. Hoy no hay copias de seguridad del volumen.
- Azure y Vercel se quedan sin persistencia: allí el respaldo dura lo que dure el proceso.

## Lo que se verificó y lo que no

- **Verificado:** las pruebas de `backend/tests/test_postgres_snapshot_store.py` pasaron contra un PostgreSQL 16.2 real en un equipo de desarrollo (guardar, leer con otro pool, reemplazar, limpiar, migrar una sola vez). También se comprobó de punta a punta que, tras reiniciar la API con las fuentes caídas, los precios de Steam y PlayStation salen de PostgreSQL.
- **Verificado:** con la base caída, la búsqueda responde y no espera más de una vez (`test_with_the_database_down_...`).
- **No verificado:** el servicio `postgres:17-alpine` del compose no se levantó (el equipo de desarrollo no tiene Docker). Falta comprobar en el laboratorio que arranca dentro de 96 MB y que Dokploy acepta el volumen con nombre.
- **No verificado:** el efecto en el escenario E1 (p95 ≤ 3 s) con PostgreSQL en el laboratorio. Cada búsqueda añade una lectura por fuente; hay que volver a medir.

## Cuándo revisar esta decisión

- El laboratorio no permite el volumen con nombre, o PostgreSQL no cabe en 96 MB.
- La medición de E1 empeora de forma apreciable por las lecturas a la base.
- Se despliega más de una instancia de la API y hace falta un contador compartido muy rápido: ahí Redis vuelve a ser candidato, como complemento.
