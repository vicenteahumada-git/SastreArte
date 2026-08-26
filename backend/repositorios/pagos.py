from configuracion.base_datos import conexion


def listar(id_pedido: int) -> list[dict]:
    with conexion() as conn:
        return conn.execute(
            """SELECT id_pago, id_pedido, monto, fecha, metodo_pago
               FROM pago WHERE id_pedido = %s
               ORDER BY fecha DESC, id_pago DESC""",
            (id_pedido,),
        ).fetchall()


def crear(id_pedido: int, monto: int, metodo_pago: str) -> dict:
    with conexion() as conn:
        return conn.execute(
            """INSERT INTO pago (id_pedido, monto, metodo_pago)
               VALUES (%s, %s, %s)
               RETURNING id_pago, id_pedido, monto, fecha, metodo_pago""",
            (id_pedido, monto, metodo_pago),
        ).fetchone()

