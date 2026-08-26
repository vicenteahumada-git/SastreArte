from flask import Blueprint, request

from rutas.comunes import cuerpo_json, requiere_dueno, respuesta
from servicios import pedidos

pedidos_bp = Blueprint("pedidos", __name__, url_prefix="/api/pedidos")


@pedidos_bp.get("")
def listar_pedidos():
    return respuesta(
        pedidos.listar(
            request.args.get("buscar", ""),
            request.args.get("estado", ""),
            request.args.get("id_trabajador", ""),
            request.args.get("orden", ""),
            request.args.get("direccion", ""),
            request.args.get("desde", ""),
            request.args.get("hasta", ""),
        )
    )


@pedidos_bp.get("/opciones")
def opciones_pedido():
    """Dominios válidos de estado, prioridad y complejidad."""
    return respuesta(pedidos.opciones())


@pedidos_bp.get("/<int:id_pedido>")
def obtener_pedido(id_pedido: int):
    return respuesta(pedidos.obtener(id_pedido))


@pedidos_bp.post("")
def crear_pedido():
    return respuesta(pedidos.crear(cuerpo_json()), 201)


@pedidos_bp.put("/<int:id_pedido>")
def modificar_pedido(id_pedido: int):
    return respuesta(pedidos.modificar(id_pedido, cuerpo_json()))


@pedidos_bp.patch("/<int:id_pedido>/estado")
def actualizar_estado(id_pedido: int):
    return respuesta(pedidos.actualizar_estado(id_pedido, cuerpo_json()))


@pedidos_bp.patch("/<int:id_pedido>/prioridad")
def actualizar_prioridad(id_pedido: int):
    requiere_dueno()
    return respuesta(pedidos.actualizar_prioridad(id_pedido, cuerpo_json()))


@pedidos_bp.patch("/<int:id_pedido>/precio")
def actualizar_precio(id_pedido: int):
    requiere_dueno()
    return respuesta(pedidos.actualizar_precio(id_pedido, cuerpo_json()))


@pedidos_bp.post("/<int:id_pedido>/asignacion")
def asignar_pedido(id_pedido: int):
    """Asigna o reasigna el responsable del pedido."""
    return respuesta(pedidos.asignar(id_pedido, cuerpo_json()), 201)


@pedidos_bp.delete("/<int:id_pedido>/asignacion")
def desasignar_pedido(id_pedido: int):
    return respuesta(pedidos.desasignar(id_pedido))


@pedidos_bp.delete("/<int:id_pedido>")
def eliminar_pedido(id_pedido: int):
    requiere_dueno()
    return respuesta(pedidos.eliminar({"ids": [id_pedido]}))


@pedidos_bp.post("/eliminar")
def eliminar_pedidos():
    """Eliminación múltiple: recibe {"ids": [...]} y borra todo o nada."""
    requiere_dueno()
    return respuesta(pedidos.eliminar(cuerpo_json()))
