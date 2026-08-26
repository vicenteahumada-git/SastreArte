from flask import Blueprint

from rutas.comunes import respuesta
from servicios import resumen

resumen_bp = Blueprint("resumen", __name__, url_prefix="/api/resumen")


@resumen_bp.get("")
def obtener_resumen():
    return respuesta(resumen.obtener())
