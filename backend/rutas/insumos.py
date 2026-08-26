from flask import Blueprint

from rutas.comunes import cuerpo_json, requiere_dueno, respuesta
from servicios import insumos

insumos_bp = Blueprint("insumos", __name__)


@insumos_bp.get("/api/insumos/opciones")
def opciones_insumo():
    """Unidades de medida admitidas."""
    return respuesta(insumos.opciones())


@insumos_bp.get("/api/insumos")
def listar_insumos():
    requiere_dueno()
    return respuesta(insumos.listar())


@insumos_bp.get("/api/insumos/<int:id_insumo>")
def obtener_insumo(id_insumo: int):
    requiere_dueno()
    return respuesta(insumos.obtener(id_insumo))


@insumos_bp.post("/api/insumos")
def crear_insumo():
    requiere_dueno()
    return respuesta(insumos.crear(cuerpo_json()), 201)


@insumos_bp.put("/api/insumos/<int:id_insumo>")
def modificar_insumo(id_insumo: int):
    requiere_dueno()
    return respuesta(insumos.modificar(id_insumo, cuerpo_json()))


@insumos_bp.delete("/api/insumos/<int:id_insumo>")
def eliminar_insumo(id_insumo: int):
    requiere_dueno()
    return respuesta(insumos.eliminar(id_insumo))


@insumos_bp.patch("/api/insumos/<int:id_insumo>/ajuste")
def ajustar_stock(id_insumo: int):
    """Corrige el stock tras un recuento, dejando el ajuste asentado."""
    requiere_dueno()
    return respuesta(insumos.ajustar(id_insumo, cuerpo_json()))


@insumos_bp.get("/api/insumos/<int:id_insumo>/movimientos")
def movimientos_insumo(id_insumo: int):
    """Historial de entradas y salidas del material."""
    requiere_dueno()
    return respuesta(insumos.movimientos(id_insumo))


@insumos_bp.get("/api/pedidos/<int:id_pedido>/insumos")
def listar_insumos_pedido(id_pedido: int):
    requiere_dueno()
    return respuesta(insumos.listar_por_pedido(id_pedido))


@insumos_bp.post("/api/pedidos/<int:id_pedido>/insumos")
def agregar_insumo_pedido(id_pedido: int):
    requiere_dueno()
    return respuesta(insumos.agregar_a_pedido(id_pedido, cuerpo_json()), 201)


@insumos_bp.put("/api/pedidos/<int:id_pedido>/insumos/<int:id_insumo>")
def modificar_insumo_pedido(id_pedido: int, id_insumo: int):
    requiere_dueno()
    return respuesta(insumos.modificar_detalle(id_pedido, id_insumo, cuerpo_json()))


@insumos_bp.delete("/api/pedidos/<int:id_pedido>/insumos/<int:id_insumo>")
def eliminar_insumo_pedido(id_pedido: int, id_insumo: int):
    requiere_dueno()
    return respuesta(insumos.eliminar_detalle(id_pedido, id_insumo))
