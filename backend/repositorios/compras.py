from decimal import Decimal

from psycopg import Connection

from configuracion.base_datos import conexion

# Lo que falta comprar de cada material, en una sola cuenta:
#
#     requerido no consumido − stock disponible − ya pedido en listas abiertas
#
# Los tres términos son necesarios. Sin el stock se compra lo que está en el
# estante; sin lo ya pedido se compra dos veces lo mismo cada vez que se
# genera una lista.
FALTANTES = """
    SELECT i.id_insumo, i.nombre, i.unidad_medida,
           COALESCE(vi.stock_actual, 0) AS stock_actual,
           COALESCE(req.requerido, 0) AS requerido,
           COALESCE(ped.en_camino, 0) AS en_camino,
           GREATEST(
               COALESCE(req.requerido, 0)
               - COALESCE(vi.stock_actual, 0)
               - COALESCE(ped.en_camino, 0), 0
           ) AS cantidad_a_comprar,
           COALESCE(req.cantidad_pedidos, 0) AS cantidad_pedidos,
           req.pedidos
    FROM insumo i
    JOIN vista_insumos vi ON vi.id_insumo = i.id_insumo
    LEFT JOIN (
        SELECT di.id_insumo,
               SUM(di.cantidad) AS requerido,
               COUNT(DISTINCT di.id_pedido) AS cantidad_pedidos,
               STRING_AGG(DISTINCT di.id_pedido::text, ', ' ORDER BY di.id_pedido::text) AS pedidos
        FROM detalle_insumo di
        JOIN pedido p ON p.id_pedido = di.id_pedido
        WHERE di.estado_insumo = 'REQUERIDO'
          AND p.estado NOT IN ('ENTREGADO', 'CANCELADO')
        GROUP BY di.id_insumo
    ) req ON req.id_insumo = i.id_insumo
    LEFT JOIN (
        SELECT dlc.id_insumo, SUM(dlc.cantidad_solicitada) AS en_camino
        FROM detalle_lista_compra dlc
        JOIN lista_compra lc ON lc.id_lista_compra = dlc.id_lista_compra
        WHERE lc.estado = 'ABIERTA'
        GROUP BY dlc.id_insumo
    ) ped ON ped.id_insumo = i.id_insumo
"""


def pendientes() -> list[dict]:
    """Materiales con faltante, o sea los que hay que salir a comprar."""
    with conexion() as conn:
        return conn.execute(
            f"""SELECT * FROM ({FALTANTES}) f
                WHERE f.cantidad_a_comprar > 0
                ORDER BY f.nombre"""
        ).fetchall()


def listar() -> list[dict]:
    with conexion() as conn:
        return conn.execute(
            """SELECT lc.id_lista_compra, lc.fecha_generacion, lc.fecha_recepcion,
                      lc.estado,
                      COUNT(dlc.id_insumo) AS cantidad_items,
                      COALESCE(SUM(dlc.cantidad_solicitada), 0) AS total_solicitado
               FROM lista_compra lc
               LEFT JOIN detalle_lista_compra dlc
                      ON dlc.id_lista_compra = lc.id_lista_compra
               GROUP BY lc.id_lista_compra, lc.fecha_generacion,
                        lc.fecha_recepcion, lc.estado
               ORDER BY lc.fecha_generacion DESC"""
        ).fetchall()


def _obtener(conn: Connection, id_lista: int) -> dict | None:
    cabecera = conn.execute(
        """SELECT id_lista_compra, fecha_generacion, fecha_recepcion, estado
           FROM lista_compra WHERE id_lista_compra = %s""",
        (id_lista,),
    ).fetchone()
    if not cabecera:
        return None
    cabecera["detalles"] = conn.execute(
        """SELECT dlc.id_insumo, i.nombre, i.unidad_medida,
                  dlc.cantidad_solicitada, dlc.cantidad_recibida
           FROM detalle_lista_compra dlc
           JOIN insumo i ON i.id_insumo = dlc.id_insumo
           WHERE dlc.id_lista_compra = %s
           ORDER BY i.nombre""",
        (id_lista,),
    ).fetchall()
    return cabecera


def obtener(id_lista: int) -> dict | None:
    with conexion() as conn:
        return _obtener(conn, id_lista)


def generar() -> dict | None:
    """Congela los faltantes actuales en un documento de compra.

    Las cantidades se copian: a partir de acá la lista es un hecho y ya no
    depende de los pedidos que la originaron.
    """
    with conexion() as conn:
        faltantes = conn.execute(
            f"SELECT id_insumo, cantidad_a_comprar FROM ({FALTANTES}) f "
            "WHERE f.cantidad_a_comprar > 0"
        ).fetchall()
        if not faltantes:
            return None
        id_lista = conn.execute(
            "INSERT INTO lista_compra DEFAULT VALUES RETURNING id_lista_compra"
        ).fetchone()["id_lista_compra"]
        for fila in faltantes:
            conn.execute(
                """INSERT INTO detalle_lista_compra
                       (id_lista_compra, id_insumo, cantidad_solicitada)
                   VALUES (%s, %s, %s)""",
                (id_lista, fila["id_insumo"], fila["cantidad_a_comprar"]),
            )
        return _obtener(conn, id_lista)


def recibir(id_lista: int, recibidas: dict[int, Decimal]) -> dict | None:
    """Da la lista por recibida y asienta la entrada de cada material.

    Todo en una transacción: si algo falla, ni la lista queda recibida ni el
    stock queda movido a medias.
    """
    with conexion() as conn:
        detalles = conn.execute(
            """SELECT id_insumo, cantidad_solicitada
               FROM detalle_lista_compra WHERE id_lista_compra = %s""",
            (id_lista,),
        ).fetchall()
        if not detalles:
            return None

        for detalle in detalles:
            id_insumo = detalle["id_insumo"]
            # Sin dato explícito se asume que llegó lo pedido, que es el caso
            # normal; el parcial se indica material por material.
            cantidad = recibidas.get(id_insumo, detalle["cantidad_solicitada"])
            conn.execute(
                """UPDATE detalle_lista_compra SET cantidad_recibida = %s
                   WHERE id_lista_compra = %s AND id_insumo = %s""",
                (cantidad, id_lista, id_insumo),
            )
            if cantidad > 0:
                conn.execute(
                    """INSERT INTO movimiento_insumo
                           (id_insumo, cantidad, motivo, id_lista_compra, observacion)
                       VALUES (%s, %s, 'COMPRA', %s, %s)""",
                    (id_insumo, cantidad, id_lista, f"Recepción de la lista #{id_lista}"),
                )

        conn.execute(
            """UPDATE lista_compra
               SET estado = 'RECIBIDA', fecha_recepcion = CURRENT_TIMESTAMP
               WHERE id_lista_compra = %s""",
            (id_lista,),
        )
        return _obtener(conn, id_lista)


def anular(id_lista: int) -> dict | None:
    """Cancela una lista abierta; sus faltantes vuelven a estar disponibles."""
    with conexion() as conn:
        fila = conn.execute(
            """UPDATE lista_compra SET estado = 'ANULADA'
               WHERE id_lista_compra = %s AND estado = 'ABIERTA'
               RETURNING id_lista_compra""",
            (id_lista,),
        ).fetchone()
        return _obtener(conn, id_lista) if fila else None
