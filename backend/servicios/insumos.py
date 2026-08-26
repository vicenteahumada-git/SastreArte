"""Reglas de negocio de los materiales (capa modelo).

El stock no es un dato que se edite: es el saldo del libro de movimientos.
Todo lo que lo cambia pasa por acá y deja su asiento, de modo que cualquier
existencia se puede explicar hacia atrás.
"""

from decimal import Decimal

from configuracion.errores import ErrorDominio
from repositorios import insumos as repositorio
from servicios import pedidos
from servicios.validaciones import decimal_numero, entero, opcion, texto_requerido

# Estados de lo que un pedido necesita. Ya no dicen nada sobre la compra:
# eso vive en la lista, que es un documento aparte.
ESTADOS_DETALLE = {"REQUERIDO", "CONSUMIDO"}

# Unidades en que el taller mide sus materiales. "UNIDADES" cubre lo que se
# cuenta de a uno —botones, cierres, conos de hilo— y no se mide en largo.
UNIDADES_MEDIDA = {"MM", "CM", "METROS", "UNIDADES"}

MOTIVOS_AJUSTE = {"AJUSTE", "INVENTARIO_INICIAL"}


def opciones() -> dict:
    return {
        "unidades_medida": sorted(UNIDADES_MEDIDA),
        "estados_detalle": sorted(ESTADOS_DETALLE),
    }


def listar() -> list[dict]:
    return repositorio.listar()


def obtener(id_insumo: int) -> dict:
    insumo = repositorio.obtener(id_insumo)
    if not insumo:
        raise ErrorDominio("Insumo no encontrado.", 404)
    return insumo


def crear(datos: dict) -> dict:
    nombre = texto_requerido(datos, "nombre", 150)
    if repositorio.buscar_por_nombre(nombre):
        raise ErrorDominio("Ya existe un material con ese nombre.", 409)
    unidad = opcion(datos, "unidad_medida", UNIDADES_MEDIDA) or ""
    stock = decimal_numero(datos, "stock_actual", obligatorio=False) or Decimal(0)
    return repositorio.crear(nombre, stock, unidad)


def modificar(id_insumo: int, datos: dict) -> dict:
    obtener(id_insumo)
    nombre = texto_requerido(datos, "nombre", 150)
    if repositorio.buscar_por_nombre(nombre, id_insumo):
        raise ErrorDominio("Ya existe otro material con ese nombre.", 409)
    unidad = opcion(datos, "unidad_medida", UNIDADES_MEDIDA) or ""
    actualizado = repositorio.modificar(id_insumo, nombre, unidad)
    if not actualizado:
        raise ErrorDominio("Insumo no encontrado.", 404)
    return actualizado


def ajustar(id_insumo: int, datos: dict) -> dict:
    """Corrige el stock tras un recuento, dejando constancia del ajuste.

    Se indica la existencia real y el sistema calcula la diferencia: es como
    se cuenta en un taller —"hay 12"— y no "sumá 3".
    """
    insumo = obtener(id_insumo)
    real = decimal_numero(datos, "stock_real")
    if real is None:
        raise ErrorDominio("Indique el stock contado.")
    diferencia = real - Decimal(str(insumo["stock_actual"]))
    if diferencia == 0:
        return insumo
    observacion = texto_requerido(datos, "observacion", 200) if datos.get("observacion") else "Ajuste por recuento"
    return repositorio.registrar_movimiento(
        id_insumo, diferencia, "AJUSTE", observacion=observacion
    )


def movimientos(id_insumo: int) -> list[dict]:
    obtener(id_insumo)
    return repositorio.movimientos(id_insumo)


def eliminar(id_insumo: int) -> dict:
    obtener(id_insumo)
    if repositorio.esta_en_uso(id_insumo):
        raise ErrorDominio(
            "No se puede eliminar un material asociado a pedidos o compras.", 409
        )
    repositorio.eliminar(id_insumo)
    return {"eliminado": True, "id_insumo": id_insumo}


# --- Materiales que requiere un pedido ------------------------------------


def listar_por_pedido(id_pedido: int) -> list[dict]:
    pedidos.obtener(id_pedido)
    return repositorio.listar_por_pedido(id_pedido)


def _detalle(id_pedido: int, id_insumo: int) -> dict:
    detalle = repositorio.obtener_detalle(id_pedido, id_insumo)
    if not detalle:
        raise ErrorDominio("El insumo no está asociado a este pedido.", 404)
    return detalle


def agregar_a_pedido(id_pedido: int, datos: dict) -> dict:
    pedidos.obtener(id_pedido)
    id_insumo = entero(datos, "id_insumo", 1) or 0
    obtener(id_insumo)
    cantidad = decimal_numero(datos, "cantidad", Decimal("0.01")) or Decimal(0)
    if repositorio.obtener_detalle(id_pedido, id_insumo):
        raise ErrorDominio("El insumo ya está asociado a este pedido.", 409)
    return repositorio.agregar_a_pedido(id_pedido, id_insumo, cantidad)


def modificar_detalle(id_pedido: int, id_insumo: int, datos: dict) -> dict:
    """Cambia la cantidad requerida o marca el consumo.

    El consumo no es un estado que se escriba a mano: descuenta de bodega, y
    por eso se comprueba que haya existencias antes de dejarlo pasar.
    """
    pedidos.obtener(id_pedido)
    detalle = _detalle(id_pedido, id_insumo)

    estado = str(datos.get("estado_insumo", detalle["estado_insumo"])).strip().upper()
    if estado not in ESTADOS_DETALLE:
        raise ErrorDominio("El estado del material debe ser REQUERIDO o CONSUMIDO.")

    cantidad = decimal_numero(
        {"cantidad": datos.get("cantidad", detalle["cantidad"])},
        "cantidad",
        Decimal("0.01"),
    ) or Decimal(0)

    if estado == detalle["estado_insumo"]:
        if estado == "CONSUMIDO" and cantidad != Decimal(str(detalle["cantidad"])):
            raise ErrorDominio(
                "No se puede cambiar la cantidad de un material ya consumido. "
                "Devuélvalo a requerido primero."
            )
        actualizado = repositorio.modificar_cantidad(id_pedido, id_insumo, cantidad)
        return actualizado or detalle

    if estado == "CONSUMIDO":
        disponible = Decimal(str(obtener(id_insumo)["stock_actual"]))
        if disponible < cantidad:
            raise ErrorDominio(
                "No hay stock suficiente para consumir ese material.",
                detalles={"disponible": float(disponible), "requerido": float(cantidad)},
            )
        return repositorio.consumir(id_pedido, id_insumo, cantidad)

    return repositorio.devolver(id_pedido, id_insumo, Decimal(str(detalle["cantidad"])))


def eliminar_detalle(id_pedido: int, id_insumo: int) -> dict:
    pedidos.obtener(id_pedido)
    detalle = _detalle(id_pedido, id_insumo)
    if detalle["estado_insumo"] == "CONSUMIDO":
        raise ErrorDominio(
            "No se puede quitar un material ya consumido; devuélvalo primero.", 409
        )
    repositorio.eliminar_detalle(id_pedido, id_insumo)
    return {"eliminado": True, "id_pedido": id_pedido, "id_insumo": id_insumo}
