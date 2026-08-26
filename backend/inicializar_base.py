"""Aplica el esquema en la base si todavía no está.

Docker corre schema.sql al crear el volumen, pero en un despliegue en la nube
la base llega vacía y nadie lo ejecuta. Este script cubre ese hueco y es
idempotente: si las tablas ya existen, no toca nada.

    python backend/inicializar_base.py            # sólo el esquema
    python backend/inicializar_base.py --con-seed # además datos de ejemplo
"""

import os
import sys
from pathlib import Path

import psycopg
from psycopg import ClientCursor

RAIZ = Path(__file__).resolve().parents[1]
SQL = RAIZ / "postgresql"

sys.path.insert(0, str(Path(__file__).resolve().parent))

from configuracion.base_datos import url_base_datos


def _esquema() -> str:
    return os.getenv("DB_SCHEMA", "public")


def _ya_aplicado(conn) -> bool:
    """Usa la tabla pedido como testigo de que el esquema está creado."""
    fila = conn.execute(
        "SELECT to_regclass(%s)", (f"{_esquema()}.pedido",)
    ).fetchone()
    return fila[0] is not None


def _ejecutar(conn, archivo: Path) -> None:
    conn.execute(archivo.read_text(encoding="utf-8"))
    print(f"    {archivo.name} aplicado.")


def main(con_seed: bool = False) -> int:
    # ClientCursor liga los parámetros del lado del cliente, que es lo que
    # permite mandar un archivo .sql con varias sentencias de una vez.
    with psycopg.connect(
        url_base_datos(), autocommit=True, cursor_factory=ClientCursor
    ) as conn:
        if _ya_aplicado(conn):
            print("    El esquema ya existe; la base queda intacta.")
            return 0

        print("    Base vacía: creando el esquema.")
        _ejecutar(conn, SQL / "schema.sql")
        if con_seed:
            _ejecutar(conn, SQL / "seed.sql")
    return 0


if __name__ == "__main__":
    raise SystemExit(main("--con-seed" in sys.argv))
