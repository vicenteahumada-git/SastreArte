from flask import Blueprint

from rutas.comunes import cuerpo_json, requiere_dueno, respuesta
from servicios import pagos

pagos_bp = Blueprint("pagos", __name__, url_prefix="/api/pedidos/<int:id_pedido>/pagos")


@pagos_bp.get("")
def listar_pagos(id_pedido: int):
    requiere_dueno()
    return respuesta(pagos.listar(id_pedido))


@pagos_bp.post("")
def crear_pago(id_pedido: int):
    requiere_dueno()
    return respuesta(pagos.crear(id_pedido, cuerpo_json()), 201)
