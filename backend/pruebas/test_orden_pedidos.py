from datetime import timedelta

from pruebas.conftest import ENTREGA_FUTURA, hoy


def _numeros(respuesta) -> list[int]:
    return [pedido["id_pedido"] for pedido in respuesta.get_json()["datos"]]


def test_ordena_por_numero_de_guia(cliente_api, crear_cliente, crear_pedido):
    cliente = crear_cliente()
    # Entregas en orden inverso al de registro, para que el orden importe.
    for dias in (40, 20, 60):
        crear_pedido(
            cliente=cliente,
            fecha_entrega=(hoy() + timedelta(days=dias)).isoformat(),
        )

    ascendente = _numeros(cliente_api.get("/api/pedidos?orden=id_pedido"))
    assert ascendente == sorted(ascendente)

    descendente = _numeros(
        cliente_api.get("/api/pedidos?orden=id_pedido&direccion=desc")
    )
    assert descendente == sorted(descendente, reverse=True)


def test_ordena_por_fecha_de_entrega(cliente_api, crear_cliente, crear_pedido):
    cliente = crear_cliente()
    for dias in (50, 10, 30):
        crear_pedido(
            cliente=cliente,
            fecha_entrega=(hoy() + timedelta(days=dias)).isoformat(),
        )

    datos = cliente_api.get("/api/pedidos?orden=fecha_entrega").get_json()["datos"]
    fechas = [pedido["fecha_entrega"] for pedido in datos]
    assert fechas == sorted(fechas)

    datos = cliente_api.get(
        "/api/pedidos?orden=fecha_entrega&direccion=desc"
    ).get_json()["datos"]
    fechas = [pedido["fecha_entrega"] for pedido in datos]
    assert fechas == sorted(fechas, reverse=True)


def test_ordena_por_cliente(cliente_api, crear_cliente, crear_pedido):
    for nombre, telefono in (
        ("Zulema Vidal", "+56 9 3333 0001"),
        ("Ana Bravo", "+56 9 3333 0002"),
    ):
        crear_pedido(cliente=crear_cliente(nombre, telefono), fecha_entrega=ENTREGA_FUTURA)

    datos = cliente_api.get("/api/pedidos?orden=cliente").get_json()["datos"]
    assert [pedido["cliente_nombre"] for pedido in datos] == ["Ana Bravo", "Zulema Vidal"]


def test_rechaza_una_columna_de_orden_desconocida(cliente_api):
    respuesta = cliente_api.get("/api/pedidos?orden=DROP TABLE pedido")
    assert respuesta.status_code == 400
    assert "admite solo" in respuesta.get_json()["error"]


def test_las_opciones_incluyen_los_ordenes(cliente_api):
    opciones = cliente_api.get("/api/pedidos/opciones").get_json()["datos"]
    assert "fecha_entrega" in opciones["ordenes"]
    assert "id_pedido" in opciones["ordenes"]
