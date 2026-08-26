from configuracion.base_datos import conexion

CONSULTA = """
    SELECT a.id_pedido, a.id_trabajador, a.fecha_asignacion,
           TRIM(CONCAT_WS(' ', u.nombre, u.apellido)) AS trabajador_nombre
    FROM asignacion a JOIN usuario u ON u.id_usuario = a.id_trabajador
    WHERE a.id_pedido = %s
"""


def _obtener(conn, id_pedido: int) -> dict | None:
    return conn.execute(CONSULTA, (id_pedido,)).fetchone()


def obtener_por_pedido(id_pedido: int) -> dict | None:
    with conexion() as conn:
        return _obtener(conn, id_pedido)


def asignar(id_pedido: int, id_trabajador: int) -> dict:
    """Asigna o reasigna el pedido.

    La clave primaria de asignacion es id_pedido, así que el ON CONFLICT
    permite cambiar de responsable sin borrar y volver a insertar.
    """
    with conexion() as conn:
        conn.execute(
            """INSERT INTO asignacion (id_pedido, id_trabajador)
               VALUES (%s, %s)
               ON CONFLICT (id_pedido) DO UPDATE
                   SET id_trabajador = EXCLUDED.id_trabajador,
                       fecha_asignacion = CURRENT_TIMESTAMP""",
            (id_pedido, id_trabajador),
        )
        return _obtener(conn, id_pedido)


def desasignar(id_pedido: int) -> bool:
    with conexion() as conn:
        return (
            conn.execute(
                "DELETE FROM asignacion WHERE id_pedido = %s", (id_pedido,)
            ).rowcount
            > 0
        )
