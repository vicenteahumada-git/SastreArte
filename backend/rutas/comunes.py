from flask import jsonify, request

from configuracion.errores import ErrorDominio


def cuerpo_json() -> dict:
    if not request.is_json:
        raise ErrorDominio("La solicitud debe usar contenido JSON.")
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        raise ErrorDominio("Se esperaba un objeto JSON.")
    return datos


def respuesta(datos=None, estado: int = 200):
    return jsonify({"datos": datos}), estado


def requiere_dueno() -> None:
    """Control operativo sin login; no sustituye autenticación."""
    if request.headers.get("X-Rol-Operativo", "DUENO").upper() != "DUENO":
        raise ErrorDominio("Esta operación corresponde a la dueña del taller.", 403)
