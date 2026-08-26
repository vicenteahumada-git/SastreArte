from configuracion.errores import ErrorDominio
from repositorios import pagos as repositorio
from servicios import pedidos
from servicios.validaciones import entero, texto_requerido

METODOS = {"EFECTIVO", "TRANSFERENCIA", "TARJETA"}


def listar(id_pedido: int) -> dict:
    pedido = pedidos.obtener(id_pedido)
    return {"pedido": pedido, "pagos": repositorio.listar(id_pedido)}


def crear(id_pedido: int, datos: dict) -> dict:
    pedido = pedidos.obtener(id_pedido)

    saldo = int(pedido["saldo_restante"])
    if saldo <= 0:
        raise ErrorDominio(
            "El pedido ya está pagado por completo.",
            409,
            detalles={"total": pedido["total"], "total_pagado": pedido["total_pagado"]},
        )

    monto = entero(datos, "monto", 1) or 0
    if monto > saldo:
        raise ErrorDominio(
            f"El abono supera el saldo restante del pedido ({saldo}).",
            detalles={"monto": monto, "saldo_restante": saldo},
        )

    metodo = texto_requerido(datos, "metodo_pago", 20).upper()
    if metodo not in METODOS:
        raise ErrorDominio("El método debe ser EFECTIVO, TRANSFERENCIA o TARJETA.")

    pago = repositorio.crear(id_pedido, monto, metodo)
    return {"pago": pago, "pedido": pedidos.obtener(id_pedido)}
