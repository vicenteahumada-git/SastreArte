from flask import Blueprint, request

from rutas.comunes import cuerpo_json, requiere_dueno, respuesta
from servicios import trabajadores

trabajadores_bp = Blueprint("trabajadores", __name__, url_prefix="/api/trabajadores")


@trabajadores_bp.get("")
def listar_trabajadores():
    return respuesta(trabajadores.listar(request.args.get("estado", "")))


@trabajadores_bp.get("/<int:id_trabajador>")
def obtener_trabajador(id_trabajador: int):
    return respuesta(trabajadores.obtener(id_trabajador))


@trabajadores_bp.post("")
def crear_trabajador():
    requiere_dueno()
    return respuesta(trabajadores.crear(cuerpo_json()), 201)


@trabajadores_bp.put("/<int:id_trabajador>")
def modificar_trabajador(id_trabajador: int):
    requiere_dueno()
    return respuesta(trabajadores.modificar(id_trabajador, cuerpo_json()))


@trabajadores_bp.delete("/<int:id_trabajador>")
def eliminar_trabajador(id_trabajador: int):
    """Saca al trabajador del taller.

    Es DELETE por lo que significa para quien usa la API —la persona deja de
    estar disponible—, aunque por dentro sea una baja lógica: los pedidos que
    hizo conservan quién los hizo.
    """
    requiere_dueno()
    return respuesta(trabajadores.eliminar(id_trabajador))
