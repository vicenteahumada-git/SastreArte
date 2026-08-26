from decimal import Decimal

from configuracion.errores import ErrorDominio
from repositorios import insumos as repositorio
from servicios import pedidos
from servicios.validaciones import decimal_numero, entero, opcion, texto_requerido

ESTADOS_DETALLE = {"PENDIENTE_COMPRA", "COMPRADO"}

# Unidades en que el taller mide sus materiales. "UNIDADES" cubre lo que se
# cuenta de a uno —botones, cierres, conos de hilo— y no se mide en largo.
UNIDADES_MEDIDA = {"MM", "CM", "METROS", "UNIDADES"}


def opciones() -> dict:
    return {"unidades_medida": sorted(UNIDADES_MEDIDA)}


def listar() -> list[dict]:
    return repositorio.listar()


def obtener(id_insumo: int) -> dict:
    insumo = repositorio.obtener(id_insumo)
    if not insumo:
        raise ErrorDominio("Insumo no encontrado.", 404)
    return insumo


def _campos(datos: dict) -> tuple[str, Decimal, str]:
    return (
        texto_requerido(datos, "nombre", 150),
        decimal_numero(datos, "stock_actual") or Decimal(0),
        opcion(datos, "unidad_medida", UNIDADES_MEDIDA) or "",
    )


def crear(datos: dict) -> dict:
    return repositorio.crear(*_campos(datos))


def modificar(id_insumo: int, datos: dict) -> dict:
    obtener(id_insumo)
    actualizado = repositorio.modificar(id_insumo, *_campos(datos))
    if not actualizado:
        raise ErrorDominio("Insumo no encontrado.", 404)
    return actualizado


def eliminar(id_insumo: int) -> dict:
    obtener(id_insumo)
    if repositorio.esta_en_uso(id_insumo):
        raise ErrorDominio("No se puede eliminar un insumo asociado a pedidos.", 409)
    repositorio.eliminar(id_insumo)
    return {"eliminado": True, "id_insumo": id_insumo}


def listar_por_pedido(id_pedido: int) -> list[dict]:
    pedidos.obtener(id_pedido)
    return repositorio.listar_por_pedido(id_pedido)


def _campos_detalle(datos: dict) -> tuple[int, Decimal, str]:
    id_insumo = entero(datos, "id_insumo", 1) or 0
    obtener(id_insumo)
    cantidad = decimal_numero(datos, "cantidad", Decimal("0.01")) or Decimal(0)
    estado = str(datos.get("estado_insumo", "PENDIENTE_COMPRA")).strip().upper()
    if estado not in ESTADOS_DETALLE:
        raise ErrorDominio("El estado del insumo debe ser PENDIENTE_COMPRA o COMPRADO.")
    return id_insumo, cantidad, estado


def agregar_a_pedido(id_pedido: int, datos: dict) -> dict:
    pedidos.obtener(id_pedido)
    id_insumo, cantidad, estado = _campos_detalle(datos)
    if repositorio.obtener_detalle(id_pedido, id_insumo):
        raise ErrorDominio("El insumo ya está asociado a este pedido.", 409)
    return repositorio.agregar_a_pedido(id_pedido, id_insumo, cantidad, estado)


def modificar_detalle(id_pedido: int, id_insumo: int, datos: dict) -> dict:
    pedidos.obtener(id_pedido)
    obtener(id_insumo)
    cantidad = decimal_numero(datos, "cantidad", Decimal("0.01")) or Decimal(0)
    estado = texto_requerido(datos, "estado_insumo", 30).upper()
    if estado not in ESTADOS_DETALLE:
        raise ErrorDominio("El estado del insumo debe ser PENDIENTE_COMPRA o COMPRADO.")
    actualizado = repositorio.modificar_detalle(id_pedido, id_insumo, cantidad, estado)
    if not actualizado:
        raise ErrorDominio("El insumo no está asociado a este pedido.", 404)
    return actualizado


def eliminar_detalle(id_pedido: int, id_insumo: int) -> dict:
    pedidos.obtener(id_pedido)
    if not repositorio.eliminar_detalle(id_pedido, id_insumo):
        raise ErrorDominio("El insumo no está asociado a este pedido.", 404)
    return {"eliminado": True, "id_pedido": id_pedido, "id_insumo": id_insumo}
