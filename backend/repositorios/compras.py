from configuracion.base_datos import conexion


def pendientes() -> list[dict]:
    """Lo que falta comprar, descontando lo que ya hay en bodega.

    Dos cuentas separadas a propósito:

    - `cantidad_total` es lo que todavía no entró en ninguna lista. Antes se
      sumaba todo lo pendiente, incluso lo ya listado, y el número quedaba
      inflado respecto de lo que iba a entrar en la lista siguiente.
    - `cantidad_a_comprar` le resta el stock disponible, porque pedir que se
      compre algo que está en el estante es el error más caro de los dos.
    """
    with conexion() as conn:
        return conn.execute(
            """SELECT i.id_insumo, i.nombre, i.unidad_medida, i.stock_actual,
                      SUM(di.cantidad) FILTER (WHERE di.id_lista_compra IS NULL)
                          AS cantidad_total,
                      GREATEST(
                          COALESCE(SUM(di.cantidad) FILTER (WHERE di.id_lista_compra IS NULL), 0)
                          - i.stock_actual, 0
                      ) AS cantidad_a_comprar,
                      COUNT(DISTINCT di.id_pedido) AS cantidad_pedidos,
                      STRING_AGG(DISTINCT p.id_pedido::text, ', ' ORDER BY p.id_pedido::text) AS pedidos,
                      BOOL_OR(di.id_lista_compra IS NULL) AS disponible_para_nueva_lista
               FROM detalle_insumo di
               JOIN insumo i ON i.id_insumo = di.id_insumo
               JOIN pedido p ON p.id_pedido = di.id_pedido
               WHERE di.estado_insumo = 'PENDIENTE_COMPRA'
               GROUP BY i.id_insumo, i.nombre, i.unidad_medida, i.stock_actual
               ORDER BY i.nombre"""
        ).fetchall()


def listar() -> list[dict]:
    with conexion() as conn:
        return conn.execute(
            """SELECT lc.id_lista_compra, lc.fecha_generacion,
                      COUNT(di.id_insumo) AS cantidad_items,
                      COUNT(DISTINCT di.id_pedido) AS cantidad_pedidos
               FROM lista_compra lc
               LEFT JOIN detalle_insumo di ON di.id_lista_compra = lc.id_lista_compra
               GROUP BY lc.id_lista_compra, lc.fecha_generacion
               ORDER BY lc.fecha_generacion DESC"""
        ).fetchall()


def _obtener(conn, id_lista: int) -> dict | None:
    cabecera = conn.execute(
        """SELECT id_lista_compra, fecha_generacion
           FROM lista_compra WHERE id_lista_compra = %s""",
        (id_lista,),
    ).fetchone()
    if not cabecera:
        return None
    cabecera["detalles"] = conn.execute(
        """SELECT di.id_pedido, di.id_insumo, i.nombre,
                  i.unidad_medida, di.cantidad, di.estado_insumo
           FROM detalle_insumo di
           JOIN insumo i ON i.id_insumo = di.id_insumo
           WHERE di.id_lista_compra = %s
           ORDER BY i.nombre, di.id_pedido""",
        (id_lista,),
    ).fetchall()
    return cabecera


def obtener(id_lista: int) -> dict | None:
    with conexion() as conn:
        return _obtener(conn, id_lista)


def generar() -> dict | None:
    with conexion() as conn:
        disponibles = conn.execute(
            """SELECT id_pedido, id_insumo
               FROM detalle_insumo
               WHERE estado_insumo = 'PENDIENTE_COMPRA' AND id_lista_compra IS NULL
               FOR UPDATE"""
        ).fetchall()
        if not disponibles:
            return None
        id_lista = conn.execute(
            "INSERT INTO lista_compra DEFAULT VALUES RETURNING id_lista_compra"
        ).fetchone()["id_lista_compra"]
        conn.execute(
            """UPDATE detalle_insumo SET id_lista_compra = %s
               WHERE estado_insumo = 'PENDIENTE_COMPRA' AND id_lista_compra IS NULL""",
            (id_lista,),
        )
        return _obtener(conn, id_lista)

