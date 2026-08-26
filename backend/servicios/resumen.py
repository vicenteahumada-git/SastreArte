"""Panel de resumen (capa modelo).

Existe para que la ruta no llame directamente al repositorio y para aplicar
acá la regla de IVA, que es negocio y no persistencia.
"""

from repositorios import pedidos as repositorio_pedidos
from repositorios import resumen as repositorio
from servicios import impuestos


def obtener() -> dict:
    datos = repositorio.obtener()

    # Cada pedido aporta su saldo calculado con su propia tasa: si conviven
    # encargos tomados con alícuotas distintas, el agregado igual cuadra.
    saldo_pendiente = sum(
        impuestos.totales(
            int(monto["valor_neto"]),
            int(monto["total_pagado"] or 0),
            monto["tasa_iva"],
        )["saldo_restante"]
        for monto in repositorio_pedidos.listar_montos()
    )

    return {
        "metricas": {**datos["metricas"], "saldo_pendiente": saldo_pendiente},
        "estados": datos["estados"],
        "proximos": [impuestos.aplicar(fila) for fila in datos["proximos"]],
    }
