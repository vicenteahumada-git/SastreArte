from flask import Blueprint

from rutas.comunes import cuerpo_json, requiere_dueno, respuesta
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


@compras_bp.patch("/<int:id_lista>/recepcion")
def recibir_lista(id_lista: int):
    """Da la compra por recibida y hace entrar el material a bodega."""
    requiere_dueno()
    return respuesta(compras.recibir(id_lista, cuerpo_json()))


@compras_bp.patch("/<int:id_lista>/anulacion")
def anular_lista(id_lista: int):
    requiere_dueno()
    return respuesta(compras.anular(id_lista))
