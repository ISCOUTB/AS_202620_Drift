from typing import Optional

from app.domain.ports.hardware_benchmark_store import KINDS, HardwareBenchmarkStore
from app.infrastructure.persistence.postgres_database import PostgresDatabase

MAX_ITEMS = 5000
MAX_NAME_LENGTH = 200


class PostgresHardwareBenchmarkStore(HardwareBenchmarkStore):
    """
    Puntajes de gráficas y procesadores en PostgreSQL (ADR-0018).

    Los datos son de UL Solutions y no se publican en el repositorio: llegan
    a la base desde una copia privada. Cada carga reemplaza la lista
    completa de un tipo dentro de una transacción, así que nunca queda una
    lista a medias.
    """

    def __init__(self, database: PostgresDatabase):
        self._database = database

    def load(self, kind: str) -> dict:
        with self._database.connection() as connection:
            header = connection.execute(
                """
                SELECT source, benchmark, retrieved_at
                  FROM hardware_benchmark_set
                 WHERE kind = %s
                """,
                (kind,),
            ).fetchone()

            if header is None:
                return {}

            rows = connection.execute(
                """
                SELECT name, score, laptop
                  FROM hardware_benchmark
                 WHERE kind = %s
                 ORDER BY position
                """,
                (kind,),
            ).fetchall()

        return {
            "source": header[0],
            "benchmark": header[1],
            "retrieved_at": header[2],
            "items": [
                {"name": name, "score": score, "laptop": laptop}
                for name, score, laptop in rows
            ],
        }

    def replace(self, kind: str, payload: dict) -> int:
        if kind not in KINDS:
            raise ValueError(f"tipo de componente desconocido: {kind}")

        items = _clean_items(payload.get("items"))

        if not items:
            raise ValueError("la lista de puntajes está vacía")

        with self._database.connection() as connection, connection.transaction():
            # Una carga completa tarda más que una consulta normal.
            connection.execute("SET LOCAL statement_timeout = 15000")
            connection.execute(
                "DELETE FROM hardware_benchmark WHERE kind = %s",
                (kind,),
            )

            with connection.cursor() as cursor:
                cursor.executemany(
                    """
                    INSERT INTO hardware_benchmark
                                (kind, position, name, score, laptop)
                         VALUES (%s, %s, %s, %s, %s)
                    """,
                    [
                        (kind, position, name, score, laptop)
                        for position, (name, score, laptop) in enumerate(items)
                    ],
                )

            connection.execute(
                """
                INSERT INTO hardware_benchmark_set
                            (kind, source, benchmark, retrieved_at, loaded_at)
                     VALUES (%s, %s, %s, %s, now())
                ON CONFLICT (kind) DO UPDATE
                        SET source = EXCLUDED.source,
                            benchmark = EXCLUDED.benchmark,
                            retrieved_at = EXCLUDED.retrieved_at,
                            loaded_at = EXCLUDED.loaded_at
                """,
                (
                    kind,
                    _text(payload.get("source")),
                    _text(payload.get("benchmark")),
                    _text(payload.get("retrieved_at")),
                ),
            )

        return len(items)


def _clean_items(items) -> list:
    """Solo las entradas con nombre y puntaje válidos; las demás se descartan."""

    clean = []

    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue

        name = item.get("name")
        score = item.get("score")

        if (
            not isinstance(name, str)
            or not name.strip()
            or len(name) > MAX_NAME_LENGTH
            or isinstance(score, bool)
            or not isinstance(score, (int, float))
            or score <= 0
        ):
            continue

        clean.append((name, int(score), bool(item.get("laptop"))))

        if len(clean) >= MAX_ITEMS:
            break

    return clean


def _text(value) -> Optional[str]:
    return str(value)[:300] if value is not None else None
