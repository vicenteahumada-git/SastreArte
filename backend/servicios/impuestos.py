"""Regla de negocio del IVA.

Cada pedido guarda la tasa que regía cuando se registró. El cálculo usa
**esa** tasa, no la vigente hoy: si mañana el IVA pasa del 19 % al 21 %, los
pedidos ya tomados siguen valiendo lo que decía su boleta, y sólo los nuevos
nacen con la tasa nueva. Sin eso, un cambio de alícuota reescribiría el
pasado y dejaría los totales sin cuadrar contra lo que el cliente ya pagó.

La tasa para los pedidos nuevos se configura con la variable de entorno
TASA_IVA. El cálculo sigue viviendo acá y no en la base porque es regla de
negocio: la tabla guarda el dato, el modelo decide qué hacer con él.
"""

import os
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

TASA_POR_DEFECTO = Decimal("0.19")


def tasa_vigente() -> Decimal:
    """Alícuota que se aplicará a los pedidos nuevos (0.19 = 19 %)."""
    try:
        valor = Decimal(os.getenv("TASA_IVA", str(TASA_POR_DEFECTO)))
    except (InvalidOperation, TypeError):
        return TASA_POR_DEFECTO
    # Una tasa fuera de rango sería un error de configuración; se ignora en
    # vez de reventar, para no dejar la aplicación inservible por un typo.
    return valor if Decimal(0) <= valor <= Decimal(1) else TASA_POR_DEFECTO


def _como_tasa(valor) -> Decimal:
    """Normaliza a Decimal, cayendo en la vigente si no viene nada usable."""
    if valor is None:
        return tasa_vigente()
    try:
        return Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError):
        return tasa_vigente()


def calcular_iva(valor_neto: int, tasa=None) -> int:
    """IVA en pesos, redondeado al entero más cercano."""
    return int(
        (Decimal(valor_neto) * _como_tasa(tasa)).quantize(
            Decimal(1), rounding=ROUND_HALF_UP
        )
    )


def totales(valor_neto: int, total_pagado: int = 0, tasa=None) -> dict:
    """Calcula IVA, total y saldo restante a partir del valor neto.

    Sin `tasa` se usa la vigente, que es lo correcto para un pedido que
    todavía no existe (una simulación de precio, por ejemplo).
    """
    alicuota = _como_tasa(tasa)
    iva = calcular_iva(valor_neto, alicuota)
    total = valor_neto + iva
    return {
        "tasa_iva": float(alicuota),
        "iva": iva,
        "total": total,
        "saldo_restante": max(total - total_pagado, 0),
    }


def aplicar(pedido: dict | None) -> dict | None:
    """Agrega tasa_iva, iva, total y saldo_restante a una fila de pedido.

    La tasa sale de la propia fila: es la que quedó congelada al registrarla.
    """
    if pedido is None:
        return None
    return pedido | totales(
        int(pedido["valor_neto"]),
        int(pedido.get("total_pagado") or 0),
        pedido.get("tasa_iva"),
    )
