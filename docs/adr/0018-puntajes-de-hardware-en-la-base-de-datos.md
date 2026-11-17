# ADR-0018: Guardar en PostgreSQL los puntajes de gráficas y procesadores

- **Estado:** Propuesto
- **Fecha:** 2026-11-12
- **Decisores:** Equipo de desarrollo de DRIFT
- **Relacionado con:** [ADR-0014](0014-postgresql-como-persistencia.md) (PostgreSQL), [ADR-0011](0011-autenticacion-operaciones-administrativas.md) (token administrativo) y [evidencia E4](../evidencias/e4-compatibilidad.md)

## Contexto

La compatibilidad compara la gráfica y el procesador del usuario contra los requisitos del juego usando puntajes de 3DMark (UL Solutions): hoy 183 gráficas y 200 procesadores.

Esos puntajes no se versionan, porque son datos de un tercero que se usan con fines académicos. Viven en dos copias JSON que el backend carga así:

1. un archivo local, generado con `scripts/actualizar_benchmarks.py`;
2. si no existe, una dirección privada indicada en `DRIFT_GPU_BENCHMARKS_URL` y `DRIFT_CPU_BENCHMARKS_URL`.

Problemas de ese esquema:

- **Depende de un servicio externo al arrancar.** En el laboratorio la copia se descarga de un gist privado en el primer uso. Si esa descarga falla, la compatibilidad baja a comparar por niveles aproximados y se reintenta cada 5 minutos.
- **Un entorno sin el archivo ni las variables queda casi vacío**, sin ningún aviso. Pasó en un equipo de desarrollo: la API devolvía 0 gráficas y el laboratorio 183.
- Ahora que DRIFT tiene base de datos (ADR-0014), es el único dato de referencia que sigue fuera de ella.

## Alternativas

1. **Guardar los puntajes en PostgreSQL**, cargados desde la copia privada, y dejar la copia como respaldo.
2. **Versionar los JSON en el repositorio.** Es lo más simple, pero publica datos de UL Solutions, que es justo lo que el proyecto decidió no hacer.
3. **Dejarlo como está.** No resuelve la dependencia del gist ni los entornos vacíos.
4. **Consultar a UL en cada petición.** Lento, frágil y contrario a las condiciones de uso de un sitio que no ofrece una API.

## Decisión

Se adopta la **alternativa 1**.

- **Tablas:** `hardware_benchmark` (tipo, posición, nombre, puntaje, si es de portátil) y `hardware_benchmark_set` (fuente, benchmark, fecha de consulta y fecha de carga, por tipo). Son la migración 3.
- **Lectura:** el catálogo lee primero de PostgreSQL. Si la base no tiene la lista o no responde, usa la copia JSON como antes. **La compatibilidad no depende de que la base esté disponible.**
- **Migración automática:** si la base responde pero está vacía y la copia trae datos, se guardan en la base en ese mismo momento. No hace falta ningún paso manual después del despliegue.
- **Actualización:** `POST /hardware/benchmarks/sync`, protegido con el token administrativo (ADR-0011), vuelve a leer la copia y reemplaza las dos listas. Queda registrado quién lo pidió.
- **Los datos siguen sin entrar al repositorio:** la base se llena desde la copia privada, nunca desde un archivo versionado.
- El dominio no conoce PostgreSQL: define el puerto `HardwareBenchmarkStore`. La lógica que reconoce un modelo dentro del texto de los requisitos no cambió.

### Reglas que protegen los datos guardados

- **Una copia vacía o con otra forma se rechaza** y se conserva lo que había (mismo criterio que la sincronización de PlayStation). La respuesta es 503 con `stored_data_preserved`.
- **Las dos listas se validan antes de guardar cualquiera:** o se cargan las dos o ninguna.
- **Cada lista se reemplaza dentro de una transacción:** nunca queda a medias.
- Las entradas sin nombre o con un puntaje que no sea un número positivo se descartan.

## Consecuencias

**A favor**

- Después de la primera carga, el laboratorio ya no depende del gist para arrancar.
- Los puntajes sobreviven a reinicios y despliegues junto con el resto de los datos.
- Actualizar los puntajes ya no exige reiniciar la API.

**En contra**

- Hay dos lugares con los mismos datos (la copia y la base). La base manda; si alguien actualiza la copia y no llama a la sincronización, la API sigue con los puntajes anteriores.
- La copia privada sigue siendo necesaria como origen: sin archivo ni variables, un entorno nuevo sigue quedando vacío hasta que alguien la configure.
- Con la base caída **y** sin copia, la compatibilidad compara por niveles, igual que hoy.
- Los puntajes se guardan en la base sin cifrar. Quien tenga acceso a la base tiene acceso a los datos de UL Solutions.

## Lo que se verificó y lo que no

- **Verificado de punta a punta en un equipo de desarrollo, con PostgreSQL 16.2 y las copias reales (183 gráficas y 200 procesadores):**
  1. primer arranque con la base vacía: el catálogo responde y las tablas quedan llenas;
  2. reinicio sin la copia: el catálogo responde igual, solo desde la base;
  3. sincronización administrativa con la copia: 200, las dos listas recargadas;
  4. sincronización sin la copia: 503 y las tablas intactas;
  5. base caída con la copia: el catálogo responde desde la copia.
- **Verificado con pruebas** (`backend/tests/test_puntajes_en_base_de_datos.py`): 21 pruebas, 4 de ellas contra PostgreSQL.
- **No verificado:** el comportamiento en el laboratorio, donde la copia se descarga de la dirección privada y no de un archivo.

## Cuándo revisar esta decisión

- UL Solutions cambia sus condiciones de uso.
- Se quiere actualizar los puntajes de forma programada: habría que añadir un proceso periódico, que DRIFT no tiene (ADR-0008).
