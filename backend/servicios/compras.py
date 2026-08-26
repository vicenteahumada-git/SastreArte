"""Reglas de negocio de las compras (capa modelo).

Una lista de compra es un documento: una vez generada deja de depender de los
pedidos que la originaron. Por eso las cantidades se copian al generarla y
borrar un pedido ya no la altera.
"""

from decimal import Decimal

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
        raise ErrorDominio(
            "No falta ningún material: lo requerido está en bodega o ya fue pedido."
        )
    return lista


def _cantidades_recibidas(datos: dict) -> dict[int, Decimal]:
    """Lee el detalle de la recepción, cuando llegó distinto de lo pedido."""
    crudas = datos.get("recibidas") or {}
    if not isinstance(crudas, dict):
        raise ErrorDominio("El campo 'recibidas' debe ser un objeto.")
    recibidas: dict[int, Decimal] = {}
    for clave, valor in crudas.items():
        try:
            id_insumo, cantidad = int(clave), Decimal(str(valor))
        except (ValueError, TypeError, ArithmeticError):
            raise ErrorDominio(
                "Las cantidades recibidas deben ser numéricas."
            ) from None
        if cantidad < 0:
            raise ErrorDominio("Una cantidad recibida no puede ser negativa.")
        recibidas[id_insumo] = cantidad
    return recibidas


def recibir(id_lista: int, datos: dict) -> dict:
    """Marca la llegada de la compra y hace entrar el material a bodega."""
    lista = obtener(id_lista)
    if lista["estado"] != "ABIERTA":
        raise ErrorDominio(
            f"La lista ya está {lista['estado'].lower()}; no se puede recibir de nuevo.",
            409,
        )
    esperados = {detalle["id_insumo"] for detalle in lista["detalles"]}
    recibidas = _cantidades_recibidas(datos)
    ajenos = set(recibidas) - esperados
    if ajenos:
        raise ErrorDominio(
            "Se indicaron materiales que no están en la lista.",
            detalles={"id_insumo": sorted(ajenos)},
        )
    return repositorio.recibir(id_lista, recibidas)


def anular(id_lista: int) -> dict:
    lista = obtener(id_lista)
    if lista["estado"] != "ABIERTA":
        raise ErrorDominio("Sólo se puede anular una lista abierta.", 409)
    return repositorio.anular(id_lista)
