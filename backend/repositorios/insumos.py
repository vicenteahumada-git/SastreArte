from decimal import Decimal

from configuracion.base_datos import conexion


def listar() -> list[dict]:
    with conexion() as conn:
        return conn.execute(
            """SELECT id_insumo, nombre, stock_actual, unidad_medida
               FROM insumo ORDER BY nombre"""
        ).fetchall()


def obtener(id_insumo: int) -> dict | None:
    with conexion() as conn:
        return conn.execute(
            """SELECT id_insumo, nombre, stock_actual, unidad_medida
               FROM insumo WHERE id_insumo = %s""",
            (id_insumo,),
        ).fetchone()


def crear(nombre: str, stock: Decimal, unidad: str) -> dict:
    with conexion() as conn:
        return conn.execute(
            """INSERT INTO insumo (nombre, stock_actual, unidad_medida)
               VALUES (%s, %s, %s)
               RETURNING id_insumo, nombre, stock_actual, unidad_medida""",
            (nombre, stock, unidad),
        ).fetchone()


def modificar(id_insumo: int, nombre: str, stock: Decimal, unidad: str) -> dict | None:
    with conexion() as conn:
        return conn.execute(
            """UPDATE insumo SET nombre = %s, stock_actual = %s, unidad_medida = %s
               WHERE id_insumo = %s
               RETURNING id_insumo, nombre, stock_actual, unidad_medida""",
            (nombre, stock, unidad, id_insumo),
        ).fetchone()


def esta_en_uso(id_insumo: int) -> bool:
    with conexion() as conn:
        return bool(
            conn.execute(
                "SELECT 1 FROM detalle_insumo WHERE id_insumo = %s LIMIT 1", (id_insumo,)
            ).fetchone()
        )


def eliminar(id_insumo: int) -> bool:
    with conexion() as conn:
        return conn.execute(
            "DELETE FROM insumo WHERE id_insumo = %s", (id_insumo,)
        ).rowcount > 0


def listar_por_pedido(id_pedido: int) -> list[dict]:
    with conexion() as conn:
        return conn.execute(
            """SELECT di.id_pedido, di.id_insumo, i.nombre, i.unidad_medida,
                      di.cantidad, di.estado_insumo, di.id_lista_compra
               FROM detalle_insumo di
               JOIN insumo i ON i.id_insumo = di.id_insumo
               WHERE di.id_pedido = %s ORDER BY i.nombre""",
            (id_pedido,),
        ).fetchall()


CONSULTA_DETALLE = """
    SELECT di.id_pedido, di.id_insumo, i.nombre, i.unidad_medida,
           di.cantidad, di.estado_insumo, di.id_lista_compra
    FROM detalle_insumo di JOIN insumo i ON i.id_insumo = di.id_insumo
    WHERE di.id_pedido = %s AND di.id_insumo = %s
"""


def _obtener_detalle(conn, id_pedido: int, id_insumo: int) -> dict | None:
    """Relee el detalle sin pedir otra conexión al pool."""
    return conn.execute(CONSULTA_DETALLE, (id_pedido, id_insumo)).fetchone()


def agregar_a_pedido(
    id_pedido: int, id_insumo: int, cantidad: Decimal, estado: str
) -> dict:
    with conexion() as conn:
        conn.execute(
            """INSERT INTO detalle_insumo (id_pedido, id_insumo, cantidad, estado_insumo)
               VALUES (%s, %s, %s, %s)""",
            (id_pedido, id_insumo, cantidad, estado),
        )
        return _obtener_detalle(conn, id_pedido, id_insumo)


def obtener_detalle(id_pedido: int, id_insumo: int) -> dict | None:
    with conexion() as conn:
        return _obtener_detalle(conn, id_pedido, id_insumo)


def modificar_detalle(
    id_pedido: int, id_insumo: int, cantidad: Decimal, estado: str
) -> dict | None:
    """Actualiza el detalle y, si vuelve a pendiente, lo suelta de su lista.

    Sin ese `id_lista_compra = NULL` el material queda trabado: sigue
    apareciendo como pendiente pero arrastra la lista vieja, así que ninguna
    lista nueva lo toma y no hay forma de volver a comprarlo.
    """
    with conexion() as conn:
        fila = conn.execute(
            """UPDATE detalle_insumo
               SET cantidad = %s,
                   estado_insumo = %s,
                   id_lista_compra = CASE
                       WHEN %s = 'PENDIENTE_COMPRA' THEN NULL
                       ELSE id_lista_compra
                   END
               WHERE id_pedido = %s AND id_insumo = %s
               RETURNING id_pedido""",
            (cantidad, estado, estado, id_pedido, id_insumo),
        ).fetchone()
        return _obtener_detalle(conn, id_pedido, id_insumo) if fila else None


def eliminar_detalle(id_pedido: int, id_insumo: int) -> bool:
    with conexion() as conn:
        return conn.execute(
            "DELETE FROM detalle_insumo WHERE id_pedido = %s AND id_insumo = %s",
            (id_pedido, id_insumo),
        ).rowcount > 0

