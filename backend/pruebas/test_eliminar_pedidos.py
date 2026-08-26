def test_elimina_un_pedido(cliente_api, crear_pedido):
    pedido = crear_pedido()
    respuesta = cliente_api.delete(f"/api/pedidos/{pedido['id_pedido']}")
    assert respuesta.status_code == 200
    assert respuesta.get_json()["datos"]["cantidad"] == 1
    assert cliente_api.get(f"/api/pedidos/{pedido['id_pedido']}").status_code == 404


def test_elimina_varios_pedidos_de_una_vez(cliente_api, crear_cliente, crear_pedido):
    cliente = crear_cliente()
    pedidos = [crear_pedido(cliente=cliente) for _ in range(3)]
    ids = [pedido["id_pedido"] for pedido in pedidos]

    respuesta = cliente_api.post("/api/pedidos/eliminar", json={"ids": ids})
    assert respuesta.status_code == 200
    assert respuesta.get_json()["datos"]["cantidad"] == 3
    assert cliente_api.get("/api/pedidos").get_json()["datos"] == []


def test_el_borrado_arrastra_pagos_y_asignaciones(
    cliente_api, crear_pedido, crear_trabajador
):
    pedido = crear_pedido(valor_base=30000)
    trabajador = crear_trabajador()
    cliente_api.post(
        f"/api/pedidos/{pedido['id_pedido']}/asignacion",
        json={"id_trabajador": trabajador["id_usuario"]},
    )
    cliente_api.post(
        f"/api/pedidos/{pedido['id_pedido']}/pagos",
        json={"monto": 10000, "metodo_pago": "EFECTIVO"},
    )

    respuesta = cliente_api.post(
        "/api/pedidos/eliminar", json={"ids": [pedido["id_pedido"]]}
    )
    assert respuesta.get_json()["datos"]["pagos_eliminados"] == 1
    assert cliente_api.get(f"/api/pedidos/{pedido['id_pedido']}/pagos").status_code == 404


def test_no_borra_nada_si_algun_id_no_existe(cliente_api, crear_pedido):
    """La eliminación es todo o nada."""
    pedido = crear_pedido()
    respuesta = cliente_api.post(
        "/api/pedidos/eliminar", json={"ids": [pedido["id_pedido"], 999999]}
    )
    assert respuesta.status_code == 404
    assert cliente_api.get(f"/api/pedidos/{pedido['id_pedido']}").status_code == 200


def test_rechaza_lista_vacia(cliente_api):
    respuesta = cliente_api.post("/api/pedidos/eliminar", json={"ids": []})
    assert respuesta.status_code == 400


def test_solo_la_duena_puede_eliminar(cliente_api, crear_pedido):
    pedido = crear_pedido()
    respuesta = cliente_api.post(
        "/api/pedidos/eliminar",
        json={"ids": [pedido["id_pedido"]]},
        headers={"X-Rol-Operativo": "TRABAJADOR"},
    )
    assert respuesta.status_code == 403
    assert cliente_api.get(f"/api/pedidos/{pedido['id_pedido']}").status_code == 200
