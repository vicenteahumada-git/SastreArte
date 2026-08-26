def test_asigna_pedido_a_trabajador(cliente_api, crear_pedido, crear_trabajador):
    pedido = crear_pedido()
    trabajador = crear_trabajador()
    respuesta = cliente_api.post(
        f"/api/pedidos/{pedido['id_pedido']}/asignacion",
        json={"id_trabajador": trabajador["id_usuario"]},
    )
    assert respuesta.status_code == 201
    assert respuesta.get_json()["datos"]["id_trabajador"] == trabajador["id_usuario"]


def test_un_trabajador_puede_tener_varios_pedidos(
    cliente_api, crear_cliente, crear_pedido, crear_trabajador
):
    cliente = crear_cliente()
    trabajador = crear_trabajador()
    pedidos = [crear_pedido(cliente=cliente), crear_pedido(cliente=cliente)]
    for pedido in pedidos:
        respuesta = cliente_api.post(
            f"/api/pedidos/{pedido['id_pedido']}/asignacion",
            json={"id_trabajador": trabajador["id_usuario"]},
        )
        assert respuesta.status_code == 201


def test_un_pedido_conserva_un_solo_responsable(
    cliente_api, crear_pedido, crear_trabajador
):
    """Reasignar reemplaza al anterior en vez de acumular responsables."""
    pedido = crear_pedido()
    primero = crear_trabajador("Mario", "Soto", "+56 9 1111 1111")
    segundo = crear_trabajador("Paula", "Ríos", "+56 9 2222 2222")

    cliente_api.post(
        f"/api/pedidos/{pedido['id_pedido']}/asignacion",
        json={"id_trabajador": primero["id_usuario"]},
    )
    reasignacion = cliente_api.post(
        f"/api/pedidos/{pedido['id_pedido']}/asignacion",
        json={"id_trabajador": segundo["id_usuario"]},
    )
    assert reasignacion.status_code == 201
    assert reasignacion.get_json()["datos"]["id_trabajador"] == segundo["id_usuario"]

    actual = cliente_api.get(f"/api/pedidos/{pedido['id_pedido']}").get_json()["datos"]
    assert actual["id_trabajador"] == segundo["id_usuario"]
    assert actual["trabajador_nombre"] == "Paula Ríos"


def test_permite_quitar_la_asignacion(cliente_api, crear_pedido, crear_trabajador):
    pedido = crear_pedido()
    trabajador = crear_trabajador()
    cliente_api.post(
        f"/api/pedidos/{pedido['id_pedido']}/asignacion",
        json={"id_trabajador": trabajador["id_usuario"]},
    )
    respuesta = cliente_api.delete(f"/api/pedidos/{pedido['id_pedido']}/asignacion")
    assert respuesta.status_code == 200

    actual = cliente_api.get(f"/api/pedidos/{pedido['id_pedido']}").get_json()["datos"]
    assert actual["id_trabajador"] is None


def test_no_asigna_trabajador_inactivo(cliente_api, crear_pedido, crear_trabajador):
    pedido = crear_pedido()
    trabajador = crear_trabajador()
    cliente_api.patch(f"/api/trabajadores/{trabajador['id_usuario']}/baja")
    respuesta = cliente_api.post(
        f"/api/pedidos/{pedido['id_pedido']}/asignacion",
        json={"id_trabajador": trabajador["id_usuario"]},
    )
    assert respuesta.status_code == 400
