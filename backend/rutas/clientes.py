from flask import Blueprint, request

from rutas.comunes import cuerpo_json, requiere_dueno, respuesta
from servicios import clientes

clientes_bp = Blueprint("clientes", __name__, url_prefix="/api/clientes")


@clientes_bp.get("")
def listar_clientes():
    return respuesta(
        clientes.listar(
            request.args.get("nombre", ""),
            request.args.get("telefono", ""),
            request.args.get("buscar", ""),
        )
    )


@clientes_bp.get("/<int:id_cliente>")
def obtener_cliente(id_cliente: int):
    return respuesta(clientes.obtener(id_cliente))


@clientes_bp.post("")
def crear_cliente():
    return respuesta(clientes.crear(cuerpo_json()), 201)


@clientes_bp.put("/<int:id_cliente>")
def modificar_cliente(id_cliente: int):
    """Corregir el nombre o el teléfono es parte de la operación diaria."""
    return respuesta(clientes.modificar(id_cliente, cuerpo_json()))


@clientes_bp.delete("/<int:id_cliente>")
def eliminar_cliente(id_cliente: int):
    """Eliminar es destructivo, así que queda reservado a la dueña."""
    requiere_dueno()
    return respuesta(clientes.eliminar(id_cliente))
