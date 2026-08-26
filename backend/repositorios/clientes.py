from configuracion.base_datos import conexion

CAMPOS = "id_cliente, nombre, telefono"


def listar(nombre: str = "", telefono: str = "", general: str = "") -> list[dict]:
    condiciones = []
    parametros: list[str] = []
    if nombre:
        condiciones.append("nombre ILIKE %s")
        parametros.append(f"%{nombre}%")
    if telefono:
        condiciones.append("telefono ILIKE %s")
        parametros.append(f"%{telefono}%")
    if general:
        condiciones.append("(nombre ILIKE %s OR telefono ILIKE %s)")
        parametros.extend((f"%{general}%", f"%{general}%"))
    filtro = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""
    with conexion() as conn:
        return conn.execute(
            f"""SELECT {CAMPOS}
                 FROM cliente {filtro}
                 ORDER BY nombre LIMIT 100""",
            parametros,
        ).fetchall()


def obtener(id_cliente: int) -> dict | None:
    with conexion() as conn:
        return conn.execute(
            f"SELECT {CAMPOS} FROM cliente WHERE id_cliente = %s",
            (id_cliente,),
        ).fetchone()


def crear(nombre: str, telefono: str) -> dict:
    with conexion() as conn:
        return conn.execute(
            f"""INSERT INTO cliente (nombre, telefono) VALUES (%s, %s)
               RETURNING {CAMPOS}""",
            (nombre, telefono),
        ).fetchone()


def modificar(id_cliente: int, nombre: str, telefono: str) -> dict | None:
    with conexion() as conn:
        return conn.execute(
            f"""UPDATE cliente SET nombre = %s, telefono = %s
               WHERE id_cliente = %s
               RETURNING {CAMPOS}""",
            (nombre, telefono, id_cliente),
        ).fetchone()


def contar_pedidos(id_cliente: int) -> int:
    """Pedidos asociados al cliente; bloquean su eliminación."""
    with conexion() as conn:
        return conn.execute(
            "SELECT COUNT(*) AS total FROM pedido WHERE id_cliente = %s",
            (id_cliente,),
        ).fetchone()["total"]


def eliminar(id_cliente: int) -> bool:
    with conexion() as conn:
        return (
            conn.execute(
                "DELETE FROM cliente WHERE id_cliente = %s", (id_cliente,)
            ).rowcount
            > 0
        )
