from configuracion.errores import ErrorDominio
from repositorios import compras as repositorio


def pendientes() -> list[dict]:
    return repositorio.pendientes()


def listar() -> list[dict]:
    return repositorio.listar()


def obtener(id_lista: int) -> dict:
    lista = repositorio.obtener(id_lista)
    if not lista:
        raise ErrorDominio("Lista de compra no encontrada.", 404)
    return lista


def generar() -> dict:
    lista = repositorio.generar()
    if not lista:
        raise ErrorDominio("No hay insumos pendientes sin una lista de compra.")
    return lista

