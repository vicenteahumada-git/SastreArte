from datetime import timedelta

from pruebas.conftest import hoy


def _entrega(dias: int) -> str:
    return (hoy() + timedelta(days=dias)).isoformat()


def _ids(respuesta) -> list[int]:
    return [pedido["id_pedido"] for pedido in respuesta.get_json()["datos"]]


# --- Filtro por estado ----------------------------------------------------
def test_filtra_por_estado(cliente_api, crear_cliente, crear_pedido):
    cliente = crear_cliente()
    pendiente = crear_pedido(cliente=cliente)
    en_proceso = crear_pedido(cliente=cliente)
    cliente_api.patch(
        f"/api/pedidos/{en_proceso['id_pedido']}/estado", json={"estado": "EN_PROCESO"}
    )

    assert _ids(cliente_api.get("/api/pedidos?estado=PENDIENTE")) == [pendiente["id_pedido"]]
    assert _ids(cliente_api.get("/api/pedidos?estado=EN_PROCESO")) == [en_proceso["id_pedido"]]
    assert len(_ids(cliente_api.get("/api/pedidos"))) == 2


def test_el_filtro_de_estado_normaliza(cliente_api, crear_pedido):
    pedido = crear_pedido()
    assert _ids(cliente_api.get("/api/pedidos?estado=pendiente")) == [pedido["id_pedido"]]


def test_rechaza_un_estado_invalido_en_el_filtro(cliente_api):
    respuesta = cliente_api.get("/api/pedidos?estado=banana")
    assert respuesta.status_code == 400
    assert "admite solo" in respuesta.get_json()["error"]


# --- Filtro por fecha de entrega ------------------------------------------
def test_filtra_por_rango_de_entrega(cliente_api, crear_cliente, crear_pedido):
    cliente = crear_cliente()
    cercano = crear_pedido(cliente=cliente, fecha_entrega=_entrega(5))
    medio = crear_pedido(cliente=cliente, fecha_entrega=_entrega(20))
    lejano = crear_pedido(cliente=cliente, fecha_entrega=_entrega(60))

    # Sólo el extremo inferior.
    assert _ids(cliente_api.get(f"/api/pedidos?desde={_entrega(10)}")) == [
        medio["id_pedido"],
        lejano["id_pedido"],
    ]
    # Sólo el extremo superior.
    assert _ids(cliente_api.get(f"/api/pedidos?hasta={_entrega(10)}")) == [
        cercano["id_pedido"]
    ]
    # Rango cerrado.
    assert _ids(
        cliente_api.get(f"/api/pedidos?desde={_entrega(10)}&hasta={_entrega(30)}")
    ) == [medio["id_pedido"]]


def test_el_rango_incluye_los_extremos(cliente_api, crear_pedido):
    pedido = crear_pedido(fecha_entrega=_entrega(15))
    consulta = f"/api/pedidos?desde={_entrega(15)}&hasta={_entrega(15)}"
    assert _ids(cliente_api.get(consulta)) == [pedido["id_pedido"]]


def test_rechaza_un_rango_invertido(cliente_api):
    respuesta = cliente_api.get(
        f"/api/pedidos?desde={_entrega(30)}&hasta={_entrega(10)}"
    )
    assert respuesta.status_code == 400
    assert "posterior" in respuesta.get_json()["error"]


def test_rechaza_una_fecha_mal_formada(cliente_api):
    assert cliente_api.get("/api/pedidos?desde=30-01-2027").status_code == 400


# --- Filtros combinados ---------------------------------------------------
def test_combina_estado_fecha_y_busqueda(cliente_api, crear_cliente, crear_pedido):
    ana = crear_cliente("Ana Soto", "+56 9 1111 0001")
    luis = crear_cliente("Luis Vera", "+56 9 1111 0002")
    objetivo = crear_pedido(cliente=ana, fecha_entrega=_entrega(20))
    crear_pedido(cliente=luis, fecha_entrega=_entrega(20))
    crear_pedido(cliente=ana, fecha_entrega=_entrega(90))

    consulta = f"/api/pedidos?buscar=Ana&estado=PENDIENTE&desde={_entrega(10)}&hasta={_entrega(30)}"
    assert _ids(cliente_api.get(consulta)) == [objetivo["id_pedido"]]


# --- Orden por urgencia ---------------------------------------------------
def test_ordena_por_urgencia_y_no_alfabeticamente(cliente_api, crear_cliente, crear_pedido):
    """BAJA empieza con B, pero debe quedar al final: manda la gravedad."""
    cliente = crear_cliente()
    creados = {}
    for prioridad in ("BAJA", "URGENTE", "MEDIA", "ALTA"):
        pedido = crear_pedido(cliente=cliente, prioridad=prioridad)
        creados[prioridad] = pedido["id_pedido"]

    datos = cliente_api.get("/api/pedidos?orden=prioridad").get_json()["datos"]
    assert [p["prioridad"] for p in datos] == ["URGENTE", "ALTA", "MEDIA", "BAJA"]

    datos = cliente_api.get("/api/pedidos?orden=prioridad&direccion=desc").get_json()["datos"]
    assert [p["prioridad"] for p in datos] == ["BAJA", "MEDIA", "ALTA", "URGENTE"]


def test_prioridad_figura_entre_los_ordenes_validos(cliente_api):
    opciones = cliente_api.get("/api/pedidos/opciones").get_json()["datos"]
    assert "prioridad" in opciones["ordenes"]
