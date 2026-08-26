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
