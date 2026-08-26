from datetime import date, timedelta
from decimal import Decimal

from psycopg import Connection

from configuracion.base_datos import conexion

# La base guarda la tasa de cada pedido y la vista entrega el valor neto y lo
# pagado; con eso servicios/impuestos.py calcula iva, total y saldo restante.
CAMPOS_PEDIDO = """
    vp.id_pedido, vp.id_cliente, vp.fecha_registro,
    vp.fecha_entrega, vp.descripcion, vp.estado, vp.prioridad, vp.complejidad,
    ROUND((EXTRACT(EPOCH FROM vp.tiempo_estimado) / 3600)::numeric, 2) AS tiempo_estimado_horas,
    vp.tasa_iva, vp.valor_base, vp.descuento, vp.recargo,
    vp.valor_neto, vp.total_pagado,
    c.nombre AS cliente_nombre, c.telefono AS cliente_telefono,
    a.id_trabajador,
    TRIM(CONCAT_WS(' ', u.nombre, u.apellido)) AS trabajador_nombre
"""


def _consulta_base() -> str:
    return f"""SELECT {CAMPOS_PEDIDO}
               FROM vista_pedidos vp
               JOIN cliente c ON c.id_cliente = vp.id_cliente
               LEFT JOIN asignacion a ON a.id_pedido = vp.id_pedido
               LEFT JOIN usuario u ON u.id_usuario = a.id_trabajador"""


def _obtener(conn: Connection, id_pedido: int) -> dict | None:
    """Relee el pedido reutilizando la conexión de la operación en curso."""
    return conn.execute(
        f"{_consulta_base()} WHERE vp.id_pedido = %s", (id_pedido,)
    ).fetchone()


# La urgencia se ordena por su gravedad, no alfabéticamente: de otro modo
# "ALTA" quedaría antes que "URGENTE" por simple orden de letras.
ORDEN_URGENCIA = """
    CASE vp.prioridad
        WHEN 'URGENTE' THEN 1
        WHEN 'ALTA' THEN 2
        WHEN 'MEDIA' THEN 3
        WHEN 'BAJA' THEN 4
        ELSE 5
    END
"""

# Columnas por las que se puede ordenar. Es una whitelist porque el nombre
# se interpola en el SQL y no puede venir parametrizado.
COLUMNAS_ORDEN = {
    "id_pedido": "vp.id_pedido",
    "fecha_entrega": "vp.fecha_entrega",
    "fecha_registro": "vp.fecha_registro",
    "cliente": "c.nombre",
    "estado": "vp.estado",
    "prioridad": ORDEN_URGENCIA,
}


def listar(
    buscar: str = "",
    estado: str = "",
    trabajador: int | None = None,
    orden: str = "fecha_entrega",
    descendente: bool = False,
    desde: date | None = None,
    hasta: date | None = None,
) -> list[dict]:
    condiciones = []
    parametros: list = []
    if buscar:
        condiciones.append(
            "(vp.id_pedido::text ILIKE %s OR c.nombre ILIKE %s OR vp.descripcion ILIKE %s)"
        )
        patron = f"%{buscar}%"
        parametros.extend((patron, patron, patron))
    if estado:
        condiciones.append("vp.estado = %s")
        parametros.append(estado)
    if trabajador is not None:
        condiciones.append("a.id_trabajador = %s")
        parametros.append(trabajador)
    if desde is not None:
        condiciones.append("vp.fecha_entrega >= %s")
        parametros.append(desde)
    if hasta is not None:
        condiciones.append("vp.fecha_entrega <= %s")
        parametros.append(hasta)
    filtro = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""

    columna = COLUMNAS_ORDEN.get(orden, COLUMNAS_ORDEN["fecha_entrega"])
    direccion = "DESC" if descendente else "ASC"
    with conexion() as conn:
        return conn.execute(
            f"""{_consulta_base()} {filtro}
                ORDER BY {columna} {direccion}, vp.id_pedido {direccion}""",
            parametros,
        ).fetchall()


def obtener(id_pedido: int) -> dict | None:
    with conexion() as conn:
        return _obtener(conn, id_pedido)


def listar_montos() -> list[dict]:
    """Valor neto, pagos y tasa de cada pedido, para los agregados del resumen.

    La tasa viaja con cada fila porque el saldo total es la suma de saldos
    individuales, y cada uno se calcula con la alícuota de su propio pedido.
    """
    with conexion() as conn:
        return conn.execute(
            "SELECT tasa_iva, valor_neto, total_pagado FROM vista_pedidos"
        ).fetchall()


def crear(
    id_cliente: int,
    fecha_entrega: date,
    descripcion: str,
    estado: str,
    prioridad: str | None,
    complejidad: str | None,
    horas: Decimal | None,
    tasa_iva: Decimal,
    valor_base: int,
    descuento: int,
    recargo: int,
) -> dict:
    """Inserta el pedido. La identidad de la tabla asigna el número de guía.

    La tasa se graba junto al resto: a partir de acá el pedido queda atado a
    esa alícuota, sin importar cómo cambie la configuración después.
    """
    intervalo = timedelta(hours=float(horas)) if horas is not None else None
    with conexion() as conn:
        id_pedido = conn.execute(
            """INSERT INTO pedido (
                   id_cliente, fecha_entrega, descripcion, estado,
                   prioridad, complejidad, tiempo_estimado, tasa_iva,
                   valor_base, descuento, recargo
               ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               RETURNING id_pedido""",
            (
                id_cliente,
                fecha_entrega,
                descripcion,
                estado,
                prioridad,
                complejidad,
                intervalo,
                tasa_iva,
                valor_base,
                descuento,
                recargo,
            ),
        ).fetchone()["id_pedido"]
        return _obtener(conn, id_pedido)


def modificar(
    id_pedido: int,
    descripcion: str,
    fecha_entrega: date,
    complejidad: str | None,
    horas: Decimal | None,
) -> dict | None:
    intervalo = timedelta(hours=float(horas)) if horas is not None else None
    with conexion() as conn:
        fila = conn.execute(
            """UPDATE pedido
               SET descripcion = %s, fecha_entrega = %s, complejidad = %s, tiempo_estimado = %s
               WHERE id_pedido = %s RETURNING id_pedido""",
            (descripcion, fecha_entrega, complejidad, intervalo, id_pedido),
        ).fetchone()
        return _obtener(conn, id_pedido) if fila else None


def actualizar_estado(id_pedido: int, estado: str) -> dict | None:
    with conexion() as conn:
        fila = conn.execute(
            "UPDATE pedido SET estado = %s WHERE id_pedido = %s RETURNING id_pedido",
            (estado, id_pedido),
        ).fetchone()
        return _obtener(conn, id_pedido) if fila else None


def actualizar_prioridad(id_pedido: int, prioridad: str | None) -> dict | None:
    with conexion() as conn:
        fila = conn.execute(
            "UPDATE pedido SET prioridad = %s WHERE id_pedido = %s RETURNING id_pedido",
            (prioridad, id_pedido),
        ).fetchone()
        return _obtener(conn, id_pedido) if fila else None


def actualizar_precio(
    id_pedido: int, valor_base: int, descuento: int, recargo: int
) -> dict | None:
    with conexion() as conn:
        fila = conn.execute(
            """UPDATE pedido
               SET valor_base = %s, descuento = %s, recargo = %s
               WHERE id_pedido = %s RETURNING id_pedido""",
            (valor_base, descuento, recargo, id_pedido),
        ).fetchone()
        return _obtener(conn, id_pedido) if fila else None


def eliminar(ids: list[int]) -> list[int]:
    """Borra los pedidos indicados en una sola transacción.

    Las asignaciones, pagos y detalles de insumo caen por ON DELETE CASCADE.
    Devuelve los identificadores efectivamente eliminados.
    """
    if not ids:
        return []
    with conexion() as conn:
        filas = conn.execute(
            "DELETE FROM pedido WHERE id_pedido = ANY(%s) RETURNING id_pedido",
            (ids,),
        ).fetchall()
        return [fila["id_pedido"] for fila in filas]


def contar_pagos(ids: list[int]) -> int:
    """Cuántos pagos se perderían al borrar estos pedidos."""
    if not ids:
        return 0
    with conexion() as conn:
        return conn.execute(
            "SELECT COUNT(*) AS total FROM pago WHERE id_pedido = ANY(%s)", (ids,)
        ).fetchone()["total"]
