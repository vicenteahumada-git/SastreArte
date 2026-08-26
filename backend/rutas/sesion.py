"""Ruta de inicio de sesión."""

from flask import Blueprint

from rutas.comunes import cuerpo_json, respuesta
from servicios import sesion as svc_sesion

sesion_bp = Blueprint("sesion", __name__, url_prefix="/api/sesion")


@sesion_bp.post("")
def iniciar_sesion():
    return respuesta(svc_sesion.iniciar(cuerpo_json()))
