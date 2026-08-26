def test_genera_y_consulta_lista_con_pendientes(
    cliente_api, crear_pedido, crear_insumo
):
    pedido = crear_pedido()
    insumo = crear_insumo("Forro gris", 0, "metros")
    cliente_api.post(
        f"/api/pedidos/{pedido['id_pedido']}/insumos",
        json={"id_insumo": insumo["id_insumo"], "cantidad": 2, "estado_insumo": "PENDIENTE_COMPRA"},
    )
    generada = cliente_api.post("/api/listas-compra")
    assert generada.status_code == 201
    id_lista = generada.get_json()["datos"]["id_lista_compra"]
    consulta = cliente_api.get(f"/api/listas-compra/{id_lista}").get_json()["datos"]
    assert consulta["detalles"][0]["nombre"] == "Forro gris"


# --- Inconsistencias detectadas en la revisión ----------------------------
def _material(cliente_api, nombre, stock):
    return cliente_api.post(
        "/api/insumos",
        json={"nombre": nombre, "stock_actual": stock, "unidad_medida": "UNIDADES"},
    ).get_json()["datos"]


def test_no_pide_comprar_lo_que_ya_esta_en_bodega(cliente_api, crear_pedido):
    """Con 100 en el estante y 2 requeridas, no hay que comprar nada."""
    pedido = crear_pedido()
    insumo = _material(cliente_api, "Hilo negro", 100)
    cliente_api.post(
        f"/api/pedidos/{pedido['id_pedido']}/insumos",
        json={"id_insumo": insumo["id_insumo"], "cantidad": 2},
    )
    pendiente = cliente_api.get("/api/listas-compra/pendientes").get_json()["datos"][0]
    assert pendiente["cantidad_total"] == 2
    assert pendiente["cantidad_a_comprar"] == 0


def test_pide_comprar_solo_lo_que_falta(cliente_api, crear_pedido):
    pedido = crear_pedido()
    insumo = _material(cliente_api, "Botón de asta", 3)
    cliente_api.post(
        f"/api/pedidos/{pedido['id_pedido']}/insumos",
        json={"id_insumo": insumo["id_insumo"], "cantidad": 10},
    )
    pendiente = cliente_api.get("/api/listas-compra/pendientes").get_json()["datos"][0]
    assert pendiente["cantidad_a_comprar"] == 7


def test_lo_ya_listado_no_infla_el_pendiente(cliente_api, crear_pedido):
    """El total mostrado es lo que entraría en la lista siguiente."""
    pedido = crear_pedido()
    insumo = _material(cliente_api, "Cierre invisible", 0)
    cliente_api.post(
        f"/api/pedidos/{pedido['id_pedido']}/insumos",
        json={"id_insumo": insumo["id_insumo"], "cantidad": 4},
    )
    cliente_api.post("/api/listas-compra")
    pendiente = cliente_api.get("/api/listas-compra/pendientes").get_json()["datos"][0]
    assert pendiente["cantidad_total"] is None or pendiente["cantidad_total"] == 0
    assert pendiente["disponible_para_nueva_lista"] is False


def test_volver_a_pendiente_libera_el_material(cliente_api, crear_pedido):
    """Si el material llegó fallado, tiene que poder recomprarse."""
    pedido = crear_pedido()
    insumo = _material(cliente_api, "Entretela", 0)
    cliente_api.post(
        f"/api/pedidos/{pedido['id_pedido']}/insumos",
        json={"id_insumo": insumo["id_insumo"], "cantidad": 5},
    )
    cliente_api.post("/api/listas-compra")
    cliente_api.put(
        f"/api/pedidos/{pedido['id_pedido']}/insumos/{insumo['id_insumo']}",
        json={"cantidad": 5, "estado_insumo": "COMPRADO"},
    )
    # Llegó fallado: vuelve a pendiente.
    cliente_api.put(
        f"/api/pedidos/{pedido['id_pedido']}/insumos/{insumo['id_insumo']}",
        json={"cantidad": 5, "estado_insumo": "PENDIENTE_COMPRA"},
    )
    pendiente = cliente_api.get("/api/listas-compra/pendientes").get_json()["datos"][0]
    assert pendiente["disponible_para_nueva_lista"] is True
    assert cliente_api.post("/api/listas-compra").status_code == 201
