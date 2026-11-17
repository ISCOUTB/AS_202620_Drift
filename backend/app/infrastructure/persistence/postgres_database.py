from contextlib import contextmanager
from threading import Lock

from psycopg_pool import ConnectionPool

# Cada migración se aplica una sola vez y en orden. Para cambiar el esquema
# se agrega una nueva al final; las ya aplicadas no se editan.
MIGRATIONS = [
    (
        1,
        """
        CREATE TABLE source_snapshot (
            source      text        NOT NULL,
            query_key   text        NOT NULL,
            payload     jsonb       NOT NULL,
            captured_at timestamptz NOT NULL,
            PRIMARY KEY (source, query_key)
        );
        CREATE INDEX source_snapshot_captured_at
            ON source_snapshot (captured_at);
        """,
    ),
    (
        2,
        # Cuentas, sesiones y dispositivos (ADR-0017). Borrar una cuenta
        # borra en cascada sus sesiones y sus dispositivos.
        """
        CREATE TABLE app_user (
            id             uuid        PRIMARY KEY,
            google_subject text        NOT NULL UNIQUE,
            email          text        NOT NULL,
            name           text        NOT NULL,
            picture        text,
            created_at     timestamptz NOT NULL DEFAULT now()
        );
        CREATE TABLE user_session (
            token_hash text        PRIMARY KEY,
            user_id    uuid        NOT NULL REFERENCES app_user (id) ON DELETE CASCADE,
            expires_at timestamptz NOT NULL
        );
        CREATE INDEX user_session_expires_at ON user_session (expires_at);
        CREATE TABLE user_device (
            id         uuid        PRIMARY KEY,
            user_id    uuid        NOT NULL REFERENCES app_user (id) ON DELETE CASCADE,
            name       text        NOT NULL,
            kind       text        NOT NULL CHECK (kind IN ('pc', 'playstation', 'xbox')),
            specs      jsonb,
            created_at timestamptz NOT NULL
        );
        CREATE INDEX user_device_user_id ON user_device (user_id);
        """,
    ),
    (
        3,
        # Puntajes de gráficas y procesadores (ADR-0018). `position`
        # conserva el orden de la lista original.
        """
        CREATE TABLE hardware_benchmark_set (
            kind         text        PRIMARY KEY CHECK (kind IN ('gpu', 'cpu')),
            source       text,
            benchmark    text,
            retrieved_at text,
            loaded_at    timestamptz NOT NULL
        );
        CREATE TABLE hardware_benchmark (
            kind     text    NOT NULL CHECK (kind IN ('gpu', 'cpu')),
            position integer NOT NULL,
            name     text    NOT NULL,
            score    integer NOT NULL CHECK (score > 0),
            laptop   boolean NOT NULL DEFAULT false,
            PRIMARY KEY (kind, position)
        );
        """,
    ),
    (
        4,
        # Juegos favoritos (ADR-0020). Borrar una cuenta borra sus favoritos.
        """
        CREATE TABLE user_favorite (
            user_id  uuid        NOT NULL REFERENCES app_user (id) ON DELETE CASCADE,
            game_id  text        NOT NULL,
            name     text        NOT NULL,
            image    text,
            price    numeric(14, 2),
            store    text,
            saved_at timestamptz NOT NULL,
            PRIMARY KEY (user_id, game_id)
        );
        """,
    ),
    (
        5,
        # Precio al que la persona quiere que le avisen (ADR-0021).
        """
        ALTER TABLE user_favorite ADD COLUMN target_price numeric(14, 2);
        """,
    ),
]

# Clave del candado que impide que dos procesos migren a la vez.
_MIGRATION_LOCK_ID = 20261112

_shared = {}
_shared_lock = Lock()


def shared_database(conninfo: str) -> "PostgresDatabase":
    """Un solo pool de conexiones por base de datos para todo el proceso."""

    with _shared_lock:
        if conninfo not in _shared:
            _shared[conninfo] = PostgresDatabase(conninfo)

        return _shared[conninfo]


DEFAULT_ACQUIRE_TIMEOUT_SECONDS = 0.25
DEFAULT_STATEMENT_TIMEOUT_MS = 500
DEFAULT_MAX_CONNECTIONS = 4


class PostgresDatabase:
    """
    Conexiones a PostgreSQL con plazos cortos (ADR-0014).

    La base de datos es un respaldo de la búsqueda, no un requisito para
    responder. Por eso:

    - el pool se abre sin esperar a la base: la API arranca aunque
      PostgreSQL esté caído, y el pool sigue reintentando por su cuenta;
    - pedir una conexión espera como máximo `acquire_timeout_seconds`;
    - cada sentencia tiene un tope de `statement_timeout_ms`.

    El esquema se crea en la primera conexión que funcione, no al arrancar.
    """

    def __init__(
        self,
        conninfo: str,
        acquire_timeout_seconds: float = DEFAULT_ACQUIRE_TIMEOUT_SECONDS,
        statement_timeout_ms: int = DEFAULT_STATEMENT_TIMEOUT_MS,
        max_connections: int = DEFAULT_MAX_CONNECTIONS,
    ):
        self._pool = ConnectionPool(
            conninfo,
            min_size=1,
            max_size=max_connections,
            timeout=acquire_timeout_seconds,
            open=False,
            name="drift",
            kwargs={
                "autocommit": True,
                "connect_timeout": 2,
                "options": f"-c statement_timeout={int(statement_timeout_ms)}",
            },
        )
        self._pool.open(wait=False)
        self._schema_ready = False
        self._schema_lock = Lock()

    @contextmanager
    def connection(self):
        with self._pool.connection() as connection:
            self._ensure_schema(connection)
            yield connection

    def close(self) -> None:
        self._pool.close()

    def _ensure_schema(self, connection) -> None:
        if self._schema_ready:
            return

        with self._schema_lock:
            if self._schema_ready:
                return

            with connection.transaction():
                # Crear tablas puede tardar más que una consulta normal.
                connection.execute("SET LOCAL statement_timeout = 10000")
                connection.execute(
                    "SELECT pg_advisory_xact_lock(%s)",
                    (_MIGRATION_LOCK_ID,),
                )
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        version    integer     PRIMARY KEY,
                        applied_at timestamptz NOT NULL DEFAULT now()
                    )
                    """
                )
                applied = {
                    row[0]
                    for row in connection.execute(
                        "SELECT version FROM schema_migrations"
                    )
                }

                for version, statements in MIGRATIONS:
                    if version in applied:
                        continue

                    connection.execute(statements)
                    connection.execute(
                        "INSERT INTO schema_migrations (version) VALUES (%s)",
                        (version,),
                    )

            self._schema_ready = True
