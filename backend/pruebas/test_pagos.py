def test_registra_pago(cliente_api, crear_pedido):
    pedido = crear_pedido()
    respuesta = cliente_api.post(
        f"/api/pedidos/{pedido['id_pedido']}/pagos",
        json={"monto": 10000, "metodo_pago": "TRANSFERENCIA"},
    )
    assert respuesta.status_code == 201
    assert respuesta.get_json()["datos"]["pago"]["monto"] == 10000


def test_varios_pagos_actualizan_total_pagado_y_saldo(cliente_api, crear_pedido):
    pedido = crear_pedido(valor_base=30000)
    for monto, metodo in ((10000, "EFECTIVO"), (8000, "TARJETA")):
        cliente_api.post(
            f"/api/pedidos/{pedido['id_pedido']}/pagos",
            json={"monto": monto, "metodo_pago": metodo},
        )
    consulta = cliente_api.get(f"/api/pedidos/{pedido['id_pedido']}/pagos").get_json()["datos"]
    assert len(consulta["pagos"]) == 2
    assert consulta["pedido"]["total_pagado"] == 18000
    assert consulta["pedido"]["saldo_restante"] == 17700


def test_rechaza_pago_mayor_al_saldo(cliente_api, crear_pedido):
    # 30000 de base -> total 35700 con IVA.
    pedido = crear_pedido(valor_base=30000)
    respuesta = cliente_api.post(
        f"/api/pedidos/{pedido['id_pedido']}/pagos",
        json={"monto": 35701, "metodo_pago": "EFECTIVO"},
    )
    assert respuesta.status_code == 400
    assert "supera el saldo" in respuesta.get_json()["error"]


def test_acepta_el_pago_exacto_del_saldo(cliente_api, crear_pedido):
    pedido = crear_pedido(valor_base=30000)
    respuesta = cliente_api.post(
        f"/api/pedidos/{pedido['id_pedido']}/pagos",
        json={"monto": 35700, "metodo_pago": "EFECTIVO"},
    )
    assert respuesta.status_code == 201
    assert respuesta.get_json()["datos"]["pedido"]["saldo_restante"] == 0


def test_rechaza_pagos_sobre_un_pedido_saldado(cliente_api, crear_pedido):
    pedido = crear_pedido(valor_base=30000)
    cliente_api.post(
        f"/api/pedidos/{pedido['id_pedido']}/pagos",
        json={"monto": 35700, "metodo_pago": "EFECTIVO"},
    )
    respuesta = cliente_api.post(
        f"/api/pedidos/{pedido['id_pedido']}/pagos",
        json={"monto": 1000, "metodo_pago": "EFECTIVO"},
    )
    assert respuesta.status_code == 409
    assert "pagado por completo" in respuesta.get_json()["error"]


def test_el_total_pagado_nunca_supera_al_total(cliente_api, crear_pedido):
    pedido = crear_pedido(valor_base=30000)
    for _ in range(3):
        cliente_api.post(
            f"/api/pedidos/{pedido['id_pedido']}/pagos",
            json={"monto": 20000, "metodo_pago": "EFECTIVO"},
        )
    actual = cliente_api.get(f"/api/pedidos/{pedido['id_pedido']}").get_json()["datos"]
    assert actual["total_pagado"] <= actual["total"]

