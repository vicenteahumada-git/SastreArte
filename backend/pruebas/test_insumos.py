def test_acepta_las_unidades_del_dominio(crear_insumo):
    for unidad in ("MM", "CM", "METROS", "UNIDADES"):
        insumo = crear_insumo(nombre=f"Material {unidad}", unidad=unidad)
        assert insumo["unidad_medida"] == unidad


def test_normaliza_la_unidad_a_mayusculas(crear_insumo):
    assert crear_insumo(nombre="Cinta", unidad="cm")["unidad_medida"] == "CM"


def test_rechaza_una_unidad_fuera_del_dominio(cliente_api):
    respuesta = cliente_api.post(
        "/api/insumos",
        json={"nombre": "Tela rara", "stock_actual": 1, "unidad_medida": "pulgadas"},
    )
    assert respuesta.status_code == 400
    assert "admite solo" in respuesta.get_json()["error"]


def test_modificar_tambien_valida_la_unidad(cliente_api, crear_insumo):
    insumo = crear_insumo()
    respuesta = cliente_api.put(
        f"/api/insumos/{insumo['id_insumo']}",
        json={"nombre": insumo["nombre"], "stock_actual": 5, "unidad_medida": "yardas"},
    )
    assert respuesta.status_code == 400


def test_expone_las_unidades_disponibles(cliente_api):
    opciones = cliente_api.get("/api/insumos/opciones").get_json()["datos"]
    assert opciones["unidades_medida"] == ["CM", "METROS", "MM", "UNIDADES"]


def test_asocia_insumo_a_pedido(cliente_api, crear_pedido, crear_insumo):
    pedido = crear_pedido()
    insumo = crear_insumo()
    respuesta = cliente_api.post(
        f"/api/pedidos/{pedido['id_pedido']}/insumos",
        json={"id_insumo": insumo["id_insumo"], "cantidad": 2.5},
    )
    assert respuesta.status_code == 201
    assert respuesta.get_json()["datos"]["cantidad"] == 2.5


def test_modifica_cantidad_y_marca_comprado(cliente_api, crear_pedido, crear_insumo):
    pedido = crear_pedido()
    insumo = crear_insumo()
    cliente_api.post(
        f"/api/pedidos/{pedido['id_pedido']}/insumos",
        json={"id_insumo": insumo["id_insumo"], "cantidad": 1},
    )
    respuesta = cliente_api.put(
        f"/api/pedidos/{pedido['id_pedido']}/insumos/{insumo['id_insumo']}",
        json={"cantidad": 3, "estado_insumo": "COMPRADO"},
    )
    detalle = respuesta.get_json()["datos"]
    assert detalle["cantidad"] == 3
    assert detalle["estado_insumo"] == "COMPRADO"


def test_elimina_insumo_del_pedido(cliente_api, crear_pedido, crear_insumo):
    pedido = crear_pedido()
    insumo = crear_insumo()
    cliente_api.post(
        f"/api/pedidos/{pedido['id_pedido']}/insumos",
        json={"id_insumo": insumo["id_insumo"], "cantidad": 1},
    )
    respuesta = cliente_api.delete(
        f"/api/pedidos/{pedido['id_pedido']}/insumos/{insumo['id_insumo']}"
    )
    assert respuesta.status_code == 200
    assert cliente_api.get(
        f"/api/pedidos/{pedido['id_pedido']}/insumos"
    ).get_json()["datos"] == []

