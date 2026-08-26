import os
from collections.abc import Iterator
from contextlib import contextmanager
from threading import Lock

from psycopg import Connection, sql
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

_pool: ConnectionPool | None = None
_candado = Lock()


def url_base_datos() -> str:
    return os.getenv(
        "DATABASE_URL",
        "postgresql://sastrearte:sastrearte_local@localhost:5432/sastrearte",
    )


def _obtener_pool() -> ConnectionPool:
    """Crea el pool la primera vez que se necesita y lo reutiliza."""
    global _pool
    if _pool is None:
        with _candado:
            if _pool is None:
                _pool = ConnectionPool(
                    url_base_datos(),
                    min_size=int(os.getenv("DB_POOL_MIN", "1")),
                    max_size=int(os.getenv("DB_POOL_MAX", "10")),
                    kwargs={"row_factory": dict_row},
                    open=True,
                )
    return _pool


def cerrar_pool() -> None:
    """Libera las conexiones del pool (se usa al terminar las pruebas)."""
    global _pool
    with _candado:
        if _pool is not None:
            _pool.close()
            _pool = None


@contextmanager
def conexion() -> Iterator[Connection]:
    """Entrega una conexión del pool dentro de una transacción.

    El search_path se fija en cada préstamo porque las conexiones se
    reutilizan y las pruebas trabajan sobre un esquema propio.
    """
    with _obtener_pool().connection() as conn:
        esquema = os.getenv("DB_SCHEMA", "public")
        conn.execute(
            sql.SQL("SET search_path TO {}, public").format(sql.Identifier(esquema))
        )
        yield conn
