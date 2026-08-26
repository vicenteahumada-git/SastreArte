from flask import Blueprint

from rutas.comunes import requiere_dueno, respuesta
from servicios import compras

compras_bp = Blueprint("compras", __name__, url_prefix="/api/listas-compra")


@compras_bp.get("")
def listar_listas():
    requiere_dueno()
    return respuesta(compras.listar())


@compras_bp.get("/pendientes")
def listar_pendientes():
    requiere_dueno()
    return respuesta(compras.pendientes())


@compras_bp.get("/<int:id_lista>")
def obtener_lista(id_lista: int):
    requiere_dueno()
    return respuesta(compras.obtener(id_lista))


@compras_bp.post("")
def generar_lista():
    requiere_dueno()
    return respuesta(compras.generar(), 201)
