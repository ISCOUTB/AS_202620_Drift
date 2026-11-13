import uuid
from dataclasses import asdict
from datetime import datetime
from typing import List, Optional

from psycopg.types.json import Jsonb

from app.domain.model.account import (
    Device,
    Favorite,
    GoogleIdentity,
    PcSpecs,
    User,
)
from app.domain.ports.account_repository import AccountRepository
from app.infrastructure.persistence.postgres_database import PostgresDatabase


class PostgresAccountRepository(AccountRepository):
    """
    Cuentas, sesiones y dispositivos en PostgreSQL (ADR-0014 y ADR-0017).

    Los errores de la base de datos se propagan: la API responde que las
    cuentas no están disponibles en lugar de fingir que guardó algo. La
    búsqueda de juegos no depende de este adaptador.

    Borrar un usuario borra en cascada sus sesiones, dispositivos y
    favoritos.
    """

    def __init__(self, database: PostgresDatabase):
        self._database = database

    def save_user(self, identity: GoogleIdentity) -> User:
        with self._database.connection() as connection:
            row = connection.execute(
                """
                INSERT INTO app_user (id, google_subject, email, name, picture)
                     VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (google_subject) DO UPDATE
                        SET email = EXCLUDED.email,
                            name = EXCLUDED.name,
                            picture = EXCLUDED.picture
                  RETURNING id, google_subject, email, name, picture
                """,
                (
                    str(uuid.uuid4()),
                    identity.subject,
                    identity.email,
                    identity.name,
                    identity.picture,
                ),
            ).fetchone()

        return _user(row)

    def delete_user(self, user_id: str) -> None:
        with self._database.connection() as connection:
            connection.execute("DELETE FROM app_user WHERE id = %s", (user_id,))

    def create_session(
        self,
        token_hash: str,
        user_id: str,
        expires_at: datetime,
    ) -> None:
        with self._database.connection() as connection:
            connection.execute(
                """
                INSERT INTO user_session (token_hash, user_id, expires_at)
                     VALUES (%s, %s, %s)
                """,
                (token_hash, user_id, expires_at),
            )
            # Las sesiones vencidas no se acumulan.
            connection.execute("DELETE FROM user_session WHERE expires_at <= now()")

    def find_user_by_session(
        self,
        token_hash: str,
        now: datetime,
    ) -> Optional[User]:
        with self._database.connection() as connection:
            row = connection.execute(
                """
                SELECT u.id, u.google_subject, u.email, u.name, u.picture
                  FROM user_session s
                  JOIN app_user u ON u.id = s.user_id
                 WHERE s.token_hash = %s AND s.expires_at > %s
                """,
                (token_hash, now),
            ).fetchone()

        return _user(row) if row else None

    def delete_session(self, token_hash: str) -> None:
        with self._database.connection() as connection:
            connection.execute(
                "DELETE FROM user_session WHERE token_hash = %s",
                (token_hash,),
            )

    def list_devices(self, user_id: str) -> List[Device]:
        with self._database.connection() as connection:
            rows = connection.execute(
                """
                SELECT id, user_id, name, kind, specs, created_at
                  FROM user_device
                 WHERE user_id = %s
                 ORDER BY created_at, id
                """,
                (user_id,),
            ).fetchall()

        return [_device(row) for row in rows]

    def save_device(self, device: Device) -> None:
        specs = Jsonb(asdict(device.specs)) if device.specs else None

        with self._database.connection() as connection:
            connection.execute(
                """
                INSERT INTO user_device (id, user_id, name, kind, specs, created_at)
                     VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE
                        SET name = EXCLUDED.name,
                            kind = EXCLUDED.kind,
                            specs = EXCLUDED.specs
                      WHERE user_device.user_id = EXCLUDED.user_id
                """,
                (
                    device.id,
                    device.user_id,
                    device.name,
                    device.kind,
                    specs,
                    device.created_at,
                ),
            )

    def delete_device(self, user_id: str, device_id: str) -> bool:
        with self._database.connection() as connection:
            deleted = connection.execute(
                "DELETE FROM user_device WHERE user_id = %s AND id = %s",
                (user_id, device_id),
            )

            return deleted.rowcount > 0

    def list_favorites(self, user_id: str) -> List[Favorite]:
        with self._database.connection() as connection:
            rows = connection.execute(
                """
                SELECT user_id, game_id, name, image, price, store, saved_at,
                       target_price
                  FROM user_favorite
                 WHERE user_id = %s
                 ORDER BY saved_at DESC, game_id DESC
                """,
                (user_id,),
            ).fetchall()

        return [_favorite(row) for row in rows]

    def save_favorite(self, favorite: Favorite) -> None:
        with self._database.connection() as connection:
            connection.execute(
                """
                INSERT INTO user_favorite
                            (user_id, game_id, name, image, price, store,
                             saved_at, target_price)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (user_id, game_id) DO UPDATE
                        SET name = EXCLUDED.name,
                            image = EXCLUDED.image,
                            price = EXCLUDED.price,
                            store = EXCLUDED.store,
                            saved_at = EXCLUDED.saved_at,
                            target_price = EXCLUDED.target_price
                """,
                (
                    favorite.user_id,
                    favorite.game_id,
                    favorite.name,
                    favorite.image,
                    favorite.price,
                    favorite.store,
                    favorite.saved_at,
                    favorite.target_price,
                ),
            )

    def delete_favorite(self, user_id: str, game_id: str) -> bool:
        with self._database.connection() as connection:
            deleted = connection.execute(
                "DELETE FROM user_favorite WHERE user_id = %s AND game_id = %s",
                (user_id, game_id),
            )

            return deleted.rowcount > 0


def _user(row) -> User:
    return User(
        id=str(row[0]),
        google_subject=row[1],
        email=row[2],
        name=row[3],
        picture=row[4],
    )


def _device(row) -> Device:
    return Device(
        id=str(row[0]),
        user_id=str(row[1]),
        name=row[2],
        kind=row[3],
        specs=PcSpecs(**row[4]) if row[4] else None,
        created_at=row[5],
    )


def _favorite(row) -> Favorite:
    return Favorite(
        user_id=str(row[0]),
        game_id=row[1],
        name=row[2],
        image=row[3],
        price=float(row[4]) if row[4] is not None else None,
        store=row[5],
        saved_at=row[6],
        target_price=float(row[7]) if row[7] is not None else None,
    )
