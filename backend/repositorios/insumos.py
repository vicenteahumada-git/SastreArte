from decimal import Decimal

from psycopg import Connection

from configuracion.base_datos import conexion

# El stock siempre se lee de la vista, que lo suma desde los movimientos.
# Ninguna consulta de este archivo escribe un stock: para eso está registrar().
CAMPOS = "id_insumo, nombre, unidad_medida, stock_actual"


def listar() -> list[dict]:
    with conexion() as conn:
        return conn.execute(
            f"SELECT {CAMPOS} FROM vista_insumos ORDER BY nombre"
        ).fetchall()


def _obtener(conn: Connection, id_insumo: int) -> dict | None:
    return conn.execute(
        f"SELECT {CAMPOS} FROM vista_insumos WHERE id_insumo = %s", (id_insumo,)
    ).fetchone()


def obtener(id_insumo: int) -> dict | None:
    with conexion() as conn:
        return _obtener(conn, id_insumo)


def buscar_por_nombre(nombre: str, excluir: int | None = None) -> dict | None:
    condicion = "AND id_insumo <> %s" if excluir else ""
    parametros = [nombre] + ([excluir] if excluir else [])
    with conexion() as conn:
        return conn.execute(
            f"SELECT id_insumo FROM insumo WHERE lower(nombre) = lower(%s) {condicion} LIMIT 1",
            parametros,
        ).fetchone()


def crear(nombre: str, stock_inicial: Decimal, unidad: str) -> dict:
    """Da de alta el material y, si arranca con existencias, las asienta.

    El stock inicial no es una columna sino un movimiento: así el saldo de
    cualquier material se explica siempre por su historia, sin excepciones.
    """
    with conexion() as conn:
        id_insumo = conn.execute(
            """INSERT INTO insumo (nombre, unidad_medida) VALUES (%s, %s)
               RETURNING id_insumo""",
            (nombre, unidad),
        ).fetchone()["id_insumo"]
        if stock_inicial:
            conn.execute(
                """INSERT INTO movimiento_insumo (id_insumo, cantidad, motivo, observacion)
                   VALUES (%s, %s, 'INVENTARIO_INICIAL', 'Alta del material')""",
                (id_insumo, stock_inicial),
            )
        return _obtener(conn, id_insumo)


def modificar(id_insumo: int, nombre: str, unidad: str) -> dict | None:
    """Sólo los datos del material. El stock se corrige con un ajuste."""
    with conexion() as conn:
        fila = conn.execute(
            """UPDATE insumo SET nombre = %s, unidad_medida = %s
               WHERE id_insumo = %s RETURNING id_insumo""",
            (nombre, unidad, id_insumo),
        ).fetchone()
        return _obtener(conn, id_insumo) if fila else None


def registrar_movimiento(
    id_insumo: int,
    cantidad: Decimal,
    motivo: str,
    id_pedido: int | None = None,
    id_lista_compra: int | None = None,
    observacion: str | None = None,
    conn: Connection | None = None,
) -> dict:
    """Asienta una entrada o salida y devuelve el material con su saldo nuevo.

    Acepta una conexión ya abierta para poder participar de la transacción de
    quien llama: mover stock y cambiar el documento que lo motiva tienen que
    cerrar juntos o no cerrar.
    """
    def _hacer(conn: Connection) -> dict:
        conn.execute(
            """INSERT INTO movimiento_insumo
                   (id_insumo, cantidad, motivo, id_pedido, id_lista_compra, observacion)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (id_insumo, cantidad, motivo, id_pedido, id_lista_compra, observacion),
        )
        return _obtener(conn, id_insumo)

    if conn is not None:
        return _hacer(conn)
    with conexion() as propia:
        return _hacer(propia)


def movimientos(id_insumo: int, limite: int = 50) -> list[dict]:
    """Historial del material, del más reciente al más viejo."""
    with conexion() as conn:
        return conn.execute(
            """SELECT id_movimiento, cantidad, motivo, id_pedido,
                      id_lista_compra, observacion, fecha
               FROM movimiento_insumo
               WHERE id_insumo = %s
               ORDER BY fecha DESC, id_movimiento DESC
               LIMIT %s""",
            (id_insumo, limite),
        ).fetchall()


def tiene_movimientos(id_insumo: int) -> bool:
    with conexion() as conn:
        return bool(
            conn.execute(
                "SELECT 1 FROM movimiento_insumo WHERE id_insumo = %s LIMIT 1",
                (id_insumo,),
            ).fetchone()
        )


def esta_en_uso(id_insumo: int) -> bool:
    """Si algún pedido o alguna compra lo menciona, no se puede borrar."""
    with conexion() as conn:
        return bool(
            conn.execute(
                """SELECT 1 FROM detalle_insumo WHERE id_insumo = %s
                   UNION ALL
                   SELECT 1 FROM detalle_lista_compra WHERE id_insumo = %s
                   LIMIT 1""",
                (id_insumo, id_insumo),
            ).fetchone()
        )


def eliminar(id_insumo: int) -> bool:
    with conexion() as conn:
        conn.execute("DELETE FROM movimiento_insumo WHERE id_insumo = %s", (id_insumo,))
        return (
            conn.execute(
                "DELETE FROM insumo WHERE id_insumo = %s", (id_insumo,)
            ).rowcount
            > 0
        )


# --- Materiales que requiere un pedido ------------------------------------

CONSULTA_DETALLE = """
    SELECT di.id_pedido, di.id_insumo, i.nombre, i.unidad_medida,
           di.cantidad, di.estado_insumo, vi.stock_actual
    FROM detalle_insumo di
    JOIN insumo i ON i.id_insumo = di.id_insumo
    JOIN vista_insumos vi ON vi.id_insumo = di.id_insumo
"""


def listar_por_pedido(id_pedido: int) -> list[dict]:
    with conexion() as conn:
        return conn.execute(
            f"{CONSULTA_DETALLE} WHERE di.id_pedido = %s ORDER BY i.nombre",
            (id_pedido,),
        ).fetchall()


def _obtener_detalle(conn: Connection, id_pedido: int, id_insumo: int) -> dict | None:
    return conn.execute(
        f"{CONSULTA_DETALLE} WHERE di.id_pedido = %s AND di.id_insumo = %s",
        (id_pedido, id_insumo),
    ).fetchone()


def obtener_detalle(id_pedido: int, id_insumo: int) -> dict | None:
    with conexion() as conn:
        return _obtener_detalle(conn, id_pedido, id_insumo)


def agregar_a_pedido(id_pedido: int, id_insumo: int, cantidad: Decimal) -> dict:
    """Anota lo que el pedido necesita. No toca el stock todavía."""
    with conexion() as conn:
        conn.execute(
            """INSERT INTO detalle_insumo (id_pedido, id_insumo, cantidad)
               VALUES (%s, %s, %s)""",
            (id_pedido, id_insumo, cantidad),
        )
        return _obtener_detalle(conn, id_pedido, id_insumo)


def modificar_cantidad(id_pedido: int, id_insumo: int, cantidad: Decimal) -> dict | None:
    with conexion() as conn:
        fila = conn.execute(
            """UPDATE detalle_insumo SET cantidad = %s
               WHERE id_pedido = %s AND id_insumo = %s AND estado_insumo = 'REQUERIDO'
               RETURNING id_pedido""",
            (cantidad, id_pedido, id_insumo),
        ).fetchone()
        return _obtener_detalle(conn, id_pedido, id_insumo) if fila else None


def consumir(id_pedido: int, id_insumo: int, cantidad: Decimal) -> dict:
    """Saca el material del estante para el pedido, en una sola transacción."""
    with conexion() as conn:
        conn.execute(
            """UPDATE detalle_insumo SET estado_insumo = 'CONSUMIDO'
               WHERE id_pedido = %s AND id_insumo = %s""",
            (id_pedido, id_insumo),
        )
        registrar_movimiento(
            id_insumo, -cantidad, "CONSUMO", id_pedido=id_pedido,
            observacion=f"Consumo del pedido #{id_pedido}", conn=conn,
        )
        return _obtener_detalle(conn, id_pedido, id_insumo)


def devolver(id_pedido: int, id_insumo: int, cantidad: Decimal) -> dict:
    """Deshace el consumo: el material vuelve al estante."""
    with conexion() as conn:
        conn.execute(
            """UPDATE detalle_insumo SET estado_insumo = 'REQUERIDO'
               WHERE id_pedido = %s AND id_insumo = %s""",
            (id_pedido, id_insumo),
        )
        registrar_movimiento(
            id_insumo, cantidad, "DEVOLUCION", id_pedido=id_pedido,
            observacion=f"Devolución del pedido #{id_pedido}", conn=conn,
        )
        return _obtener_detalle(conn, id_pedido, id_insumo)


def eliminar_detalle(id_pedido: int, id_insumo: int) -> bool:
    with conexion() as conn:
        return (
            conn.execute(
                "DELETE FROM detalle_insumo WHERE id_pedido = %s AND id_insumo = %s",
                (id_pedido, id_insumo),
            ).rowcount
            > 0
        )
