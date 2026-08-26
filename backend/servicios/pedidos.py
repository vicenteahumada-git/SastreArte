"""Reglas de negocio de los pedidos (capa modelo)."""

from configuracion.errores import ErrorDominio
from configuracion.tiempo import hoy
from repositorios import asignaciones
from repositorios import pedidos as repositorio
from servicios import clientes, impuestos, trabajadores
from servicios.validaciones import (
    decimal_numero,
    entero,
    fecha_iso,
    opcion,
    texto_requerido,
)

# Dominios cerrados: la base los replica con CHECK y el frontend los consume
# desde GET /api/pedidos/opciones.
ESTADOS = {"PENDIENTE", "EN_PROCESO", "LISTO_PARA_ENTREGA", "ENTREGADO", "CANCELADO"}
PRIORIDADES = {"BAJA", "MEDIA", "ALTA", "URGENTE"}
COMPLEJIDADES = {"BAJA", "MEDIA", "ALTA"}
ESTADO_INICIAL = "PENDIENTE"

MAX_ELIMINAR = 100


def opciones() -> dict:
    return {
        "estados": sorted(ESTADOS),
        "prioridades": sorted(PRIORIDADES),
        "complejidades": sorted(COMPLEJIDADES),
        "ordenes": sorted(repositorio.COLUMNAS_ORDEN),
    }


def listar(
    buscar: str = "",
    estado: str = "",
    id_trabajador: str = "",
    orden: str = "",
    direccion: str = "",
    desde: str = "",
    hasta: str = "",
) -> list[dict]:
    trabajador = entero({"id": id_trabajador}, "id", 1) if id_trabajador else None
    filtro_estado = (
        opcion({"estado": estado}, "estado", ESTADOS) if estado.strip() else ""
    )

    orden = orden.strip().lower()
    if orden and orden not in repositorio.COLUMNAS_ORDEN:
        permitidos = ", ".join(sorted(repositorio.COLUMNAS_ORDEN))
        raise ErrorDominio(f"El campo 'orden' admite solo: {permitidos}.")

    # Rango de fechas de entrega; cualquiera de los dos extremos es opcional.
    fecha_desde = fecha_iso({"desde": desde}, "desde") if desde.strip() else None
    fecha_hasta = fecha_iso({"hasta": hasta}, "hasta") if hasta.strip() else None
    if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
        raise ErrorDominio("La fecha 'desde' no puede ser posterior a 'hasta'.")

    filas = repositorio.listar(
        buscar.strip(),
        filtro_estado or "",
        trabajador,
        orden or "fecha_entrega",
        direccion.strip().lower() in {"desc", "descendente"},
        fecha_desde,
        fecha_hasta,
    )
    return [impuestos.aplicar(fila) for fila in filas]


def obtener(id_pedido: int) -> dict:
    pedido = repositorio.obtener(id_pedido)
    if not pedido:
        raise ErrorDominio("Pedido no encontrado.", 404)
    return impuestos.aplicar(pedido)


def _validar_importes(valor_base: int, descuento: int, recargo: int) -> int:
    valor_neto = valor_base + recargo - descuento
    if valor_neto < 0:
        raise ErrorDominio(
            "El descuento no puede superar el valor base más el recargo.",
            detalles={
                "valor_base": valor_base,
                "recargo": recargo,
                "descuento": descuento,
            },
        )
    return valor_neto


def crear(datos: dict) -> dict:
    id_cliente = entero(datos, "id_cliente", 1) or 0
    clientes.obtener(id_cliente)

    valor_base = entero(datos, "valor_base", 0) or 0
    descuento = entero(datos, "descuento", 0, obligatorio=False) or 0
    recargo = entero(datos, "recargo", 0, obligatorio=False) or 0
    _validar_importes(valor_base, descuento, recargo)

    # El número de pedido lo genera el repositorio bajo bloqueo: nunca se
    # toma del cliente, para que dos altas simultáneas no colisionen.
    # La tasa vigente se copia acá y queda congelada en la fila: la manda el
    # modelo, no el cliente, para que nadie pueda inventarse su propio IVA.
    pedido = repositorio.crear(
        id_cliente,
        fecha_iso(datos, "fecha_entrega", no_anterior_a=hoy()),
        texto_requerido(datos, "descripcion", 5000),
        opcion(datos, "estado", ESTADOS, obligatorio=False) or ESTADO_INICIAL,
        opcion(datos, "prioridad", PRIORIDADES, obligatorio=False),
        opcion(datos, "complejidad", COMPLEJIDADES, obligatorio=False),
        decimal_numero(datos, "tiempo_estimado_horas", obligatorio=False),
        impuestos.tasa_vigente(),
        valor_base,
        descuento,
        recargo,
    )
    return impuestos.aplicar(pedido)


def modificar(id_pedido: int, datos: dict) -> dict:
    actual = obtener(id_pedido)

    descripcion = texto_requerido(
        {"descripcion": datos.get("descripcion", actual["descripcion"])},
        "descripcion",
        5000,
    )
    # La fecha sólo se revalida contra hoy si efectivamente cambió, para no
    # bloquear la edición de pedidos cuya entrega ya venció.
    nueva_fecha = fecha_iso(
        {"fecha_entrega": datos.get("fecha_entrega", actual["fecha_entrega"])},
        "fecha_entrega",
    )
    if nueva_fecha != actual["fecha_entrega"] and nueva_fecha < hoy():
        raise ErrorDominio("El campo 'fecha_entrega' no puede ser anterior a hoy.")

    complejidad = opcion(
        {"complejidad": datos.get("complejidad", actual["complejidad"])},
        "complejidad",
        COMPLEJIDADES,
        obligatorio=False,
    )
    horas = decimal_numero(
        {
            "tiempo_estimado_horas": datos.get(
                "tiempo_estimado_horas", actual["tiempo_estimado_horas"]
            )
        },
        "tiempo_estimado_horas",
        obligatorio=False,
    )

    actualizado = repositorio.modificar(
        id_pedido, descripcion, nueva_fecha, complejidad, horas
    )
    if not actualizado:
        raise ErrorDominio("Pedido no encontrado.", 404)
    return impuestos.aplicar(actualizado)


def actualizar_estado(id_pedido: int, datos: dict) -> dict:
    obtener(id_pedido)
    estado = opcion(datos, "estado", ESTADOS)
    return impuestos.aplicar(repositorio.actualizar_estado(id_pedido, estado))


def actualizar_prioridad(id_pedido: int, datos: dict) -> dict:
    obtener(id_pedido)
    prioridad = opcion(datos, "prioridad", PRIORIDADES, obligatorio=False)
    return impuestos.aplicar(repositorio.actualizar_prioridad(id_pedido, prioridad))


def actualizar_precio(id_pedido: int, datos: dict) -> dict:
    actual = obtener(id_pedido)
    valor_base = (
        entero({"valor_base": datos.get("valor_base", actual["valor_base"])}, "valor_base", 0)
        or 0
    )
    descuento = (
        entero({"descuento": datos.get("descuento", actual["descuento"])}, "descuento", 0)
        or 0
    )
    recargo = (
        entero({"recargo": datos.get("recargo", actual["recargo"])}, "recargo", 0) or 0
    )

    valor_neto = _validar_importes(valor_base, descuento, recargo)
    # Con la tasa del pedido, no con la vigente: cambiarle el precio a un
    # encargo viejo no debe recalcularle el IVA con la alícuota de hoy.
    total = impuestos.totales(valor_neto, tasa=actual["tasa_iva"])["total"]
    if total < actual["total_pagado"]:
        raise ErrorDominio("El nuevo total no puede ser menor que lo ya pagado.")

    return impuestos.aplicar(
        repositorio.actualizar_precio(id_pedido, valor_base, descuento, recargo)
    )


def asignar(id_pedido: int, datos: dict) -> dict:
    """Asigna o reasigna el responsable del pedido.

    Un pedido mantiene un único responsable, pero puede cambiarse: si ya
    estaba asignado, la operación reemplaza al trabajador anterior.
    """
    obtener(id_pedido)
    id_trabajador = entero(datos, "id_trabajador", 1) or 0
    trabajador = trabajadores.obtener(id_trabajador)
    if trabajador["estado_usuario"] != "ACTIVO":
        raise ErrorDominio("Solo se puede asignar un trabajador activo.")
    return asignaciones.asignar(id_pedido, id_trabajador)


def desasignar(id_pedido: int) -> dict:
    obtener(id_pedido)
    if not asignaciones.desasignar(id_pedido):
        raise ErrorDominio("El pedido no tiene un responsable asignado.", 404)
    return {"id_pedido": id_pedido, "id_trabajador": None}


def eliminar(datos: dict) -> dict:
    """Elimina uno o varios pedidos en una sola transacción."""
    crudos = datos.get("ids")
    if not isinstance(crudos, list) or not crudos:
        raise ErrorDominio("Debe indicar al menos un pedido para eliminar.")
    if len(crudos) > MAX_ELIMINAR:
        raise ErrorDominio(
            f"No se pueden eliminar más de {MAX_ELIMINAR} pedidos a la vez."
        )

    ids = []
    for indice, crudo in enumerate(crudos):
        campo = f"ids[{indice}]"
        ids.append(entero({campo: crudo}, campo, 1) or 0)

    faltantes = [
        identificador
        for identificador in ids
        if repositorio.obtener(identificador) is None
    ]
    if faltantes:
        raise ErrorDominio(
            "Algunos pedidos ya no existen.", 404, detalles={"ids": faltantes}
        )

    pagos_perdidos = repositorio.contar_pagos(ids)
    eliminados = repositorio.eliminar(ids)
    return {
        "eliminados": eliminados,
        "cantidad": len(eliminados),
        "pagos_eliminados": pagos_perdidos,
    }
