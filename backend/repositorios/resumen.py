from configuracion.base_datos import conexion


def obtener() -> dict:
    """Datos crudos del panel. El saldo pendiente lo calcula el servicio,
    porque depende de la tasa de cada pedido y esa regla vive en el modelo."""
    with conexion() as conn:
        metricas = conn.execute(
            """SELECT
                   (SELECT COUNT(*) FROM pedido) AS pedidos_totales,
                   (SELECT COUNT(*) FROM pedido WHERE estado NOT IN ('ENTREGADO', 'CANCELADO')) AS pedidos_activos,
                   (SELECT COUNT(*) FROM pedido
                    WHERE fecha_entrega BETWEEN CURRENT_DATE AND CURRENT_DATE + 7
                      AND estado NOT IN ('ENTREGADO', 'CANCELADO')) AS entregas_semana,
                   (SELECT COUNT(*) FROM cliente) AS clientes,
                   (SELECT COUNT(*) FROM usuario
                    WHERE tipo_usuario = 'TRABAJADOR' AND estado_usuario = 'ACTIVO') AS trabajadores_activos,
                   (SELECT COUNT(*) FROM detalle_insumo
                    WHERE estado_insumo = 'PENDIENTE_COMPRA') AS insumos_pendientes"""
        ).fetchone()
        estados = conn.execute(
            """SELECT estado, COUNT(*) AS cantidad
               FROM pedido GROUP BY estado ORDER BY cantidad DESC, estado"""
        ).fetchall()
        proximos = conn.execute(
            """SELECT vp.id_pedido, vp.fecha_entrega, vp.descripcion,
                      vp.estado, vp.prioridad, c.nombre AS cliente_nombre,
                      vp.tasa_iva, vp.valor_neto, vp.total_pagado
               FROM vista_pedidos vp JOIN cliente c ON c.id_cliente = vp.id_cliente
               WHERE vp.estado NOT IN ('ENTREGADO', 'CANCELADO')
               ORDER BY vp.fecha_entrega, vp.id_pedido LIMIT 6"""
        ).fetchall()
        return {"metricas": metricas, "estados": estados, "proximos": proximos}
