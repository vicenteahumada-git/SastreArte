"""Circuito de materiales: bodega, requerimiento del pedido y compras.

Cada bloque reproduce una de las inconsistencias detectadas al revisar el
modelo anterior, para que no vuelvan a colarse.
"""

LISTAS = "/api/listas-compra"


def _material(cliente_api, nombre, stock=0):
    return cliente_api.post(
        "/api/insumos",
        json={"nombre": nombre, "stock_actual": stock, "unidad_medida": "UNIDADES"},
    ).get_json()["datos"]


def _requerir(cliente_api, pedido, insumo, cantidad):
    return cliente_api.post(
        f"/api/pedidos/{pedido['id_pedido']}/insumos",
        json={"id_insumo": insumo["id_insumo"], "cantidad": cantidad},
    ).get_json()["datos"]


def _stock(cliente_api, insumo):
    return float(
        cliente_api.get(f"/api/insumos/{insumo['id_insumo']}").get_json()["datos"][
            "stock_actual"
        ]
    )


def _faltante(cliente_api, insumo):
    for fila in cliente_api.get(f"{LISTAS}/pendientes").get_json()["datos"]:
        if fila["id_insumo"] == insumo["id_insumo"]:
            return float(fila["cantidad_a_comprar"])
    return 0.0


# --- El stock se mueve y queda explicado ---------------------------------
def test_anotar_el_requerimiento_no_descuenta(cliente_api, crear_pedido):
    """Anotar lo que hará falta no es sacarlo del estante."""
    insumo = _material(cliente_api, "Hilo negro", 100)
    _requerir(cliente_api, crear_pedido(), insumo, 2)
    assert _stock(cliente_api, insumo) == 100


def test_consumir_descuenta_y_devolver_repone(cliente_api, crear_pedido):
    pedido = crear_pedido()
    insumo = _material(cliente_api, "Hilo negro", 100)
    _requerir(cliente_api, pedido, insumo, 2)
    ruta = f"/api/pedidos/{pedido['id_pedido']}/insumos/{insumo['id_insumo']}"

    cliente_api.put(ruta, json={"estado_insumo": "CONSUMIDO"})
    assert _stock(cliente_api, insumo) == 98

    cliente_api.put(ruta, json={"estado_insumo": "REQUERIDO"})
    assert _stock(cliente_api, insumo) == 100


def test_cada_cambio_deja_su_asiento(cliente_api, crear_pedido):
    """El saldo siempre se puede explicar hacia atrás."""
    pedido = crear_pedido()
    insumo = _material(cliente_api, "Hilo negro", 100)
    _requerir(cliente_api, pedido, insumo, 2)
    ruta = f"/api/pedidos/{pedido['id_pedido']}/insumos/{insumo['id_insumo']}"
    cliente_api.put(ruta, json={"estado_insumo": "CONSUMIDO"})

    movimientos = cliente_api.get(
        f"/api/insumos/{insumo['id_insumo']}/movimientos"
    ).get_json()["datos"]
    motivos = [movimiento["motivo"] for movimiento in movimientos]
    assert motivos == ["CONSUMO", "INVENTARIO_INICIAL"]
    assert sum(float(m["cantidad"]) for m in movimientos) == 98


def test_no_se_consume_sin_stock(cliente_api, crear_pedido):
    pedido = crear_pedido()
    insumo = _material(cliente_api, "Cierre invisible", 1)
    _requerir(cliente_api, pedido, insumo, 5)
    respuesta = cliente_api.put(
        f"/api/pedidos/{pedido['id_pedido']}/insumos/{insumo['id_insumo']}",
        json={"estado_insumo": "CONSUMIDO"},
    )
    assert respuesta.status_code == 400
    assert respuesta.get_json()["detalles"] == {"disponible": 1.0, "requerido": 5.0}


def test_el_recuento_ajusta_y_deja_constancia(cliente_api):
    insumo = _material(cliente_api, "Botón nácar", 20)
    cliente_api.patch(
        f"/api/insumos/{insumo['id_insumo']}/ajuste",
        json={"stock_real": 17, "observacion": "Faltaban tres"},
    )
    assert _stock(cliente_api, insumo) == 17
    movimiento = cliente_api.get(
        f"/api/insumos/{insumo['id_insumo']}/movimientos"
    ).get_json()["datos"][0]
    assert movimiento["motivo"] == "AJUSTE"
    assert float(movimiento["cantidad"]) == -3
    assert movimiento["observacion"] == "Faltaban tres"


# --- No se compra lo que ya está en bodega --------------------------------
def test_no_pide_comprar_lo_que_hay(cliente_api, crear_pedido):
    insumo = _material(cliente_api, "Hilo negro", 100)
    _requerir(cliente_api, crear_pedido(), insumo, 2)
    assert _faltante(cliente_api, insumo) == 0


def test_pide_solo_lo_que_falta(cliente_api, crear_pedido):
    insumo = _material(cliente_api, "Botón de asta", 3)
    _requerir(cliente_api, crear_pedido(), insumo, 10)
    assert _faltante(cliente_api, insumo) == 7


def test_no_pide_dos_veces_lo_mismo(cliente_api, crear_pedido):
    """Lo ya solicitado en una lista abierta viene en camino."""
    insumo = _material(cliente_api, "Entretela")
    _requerir(cliente_api, crear_pedido(), insumo, 4)
    cliente_api.post(LISTAS)
    assert _faltante(cliente_api, insumo) == 0


def test_un_pedido_entregado_ya_no_pide_materiales(cliente_api, crear_pedido):
    pedido = crear_pedido()
    insumo = _material(cliente_api, "Forro satinado")
    _requerir(cliente_api, pedido, insumo, 3)
    assert _faltante(cliente_api, insumo) == 3
    cliente_api.patch(
        f"/api/pedidos/{pedido['id_pedido']}/estado", json={"estado": "ENTREGADO"}
    )
    assert _faltante(cliente_api, insumo) == 0


# --- La compra es un documento con su propio ciclo ------------------------
def test_recibir_la_compra_sube_el_stock(cliente_api, crear_pedido):
    insumo = _material(cliente_api, "Botón nácar", 3)
    _requerir(cliente_api, crear_pedido(), insumo, 10)
    lista = cliente_api.post(LISTAS).get_json()["datos"]

    cliente_api.patch(f"{LISTAS}/{lista['id_lista_compra']}/recepcion", json={})

    assert _stock(cliente_api, insumo) == 10
    recibida = cliente_api.get(f"{LISTAS}/{lista['id_lista_compra']}").get_json()["datos"]
    assert recibida["estado"] == "RECIBIDA"
    assert recibida["fecha_recepcion"] is not None


def test_recepcion_parcial(cliente_api, crear_pedido):
    """Si llega menos de lo pedido, entra lo que llegó."""
    insumo = _material(cliente_api, "Cierre invisible")
    _requerir(cliente_api, crear_pedido(), insumo, 10)
    lista = cliente_api.post(LISTAS).get_json()["datos"]

    cliente_api.patch(
        f"{LISTAS}/{lista['id_lista_compra']}/recepcion",
        json={"recibidas": {str(insumo["id_insumo"]): 4}},
    )
    assert _stock(cliente_api, insumo) == 4
    assert _faltante(cliente_api, insumo) == 6


def test_no_se_recibe_dos_veces(cliente_api, crear_pedido):
    insumo = _material(cliente_api, "Hilo blanco")
    _requerir(cliente_api, crear_pedido(), insumo, 5)
    lista = cliente_api.post(LISTAS).get_json()["datos"]
    cliente_api.patch(f"{LISTAS}/{lista['id_lista_compra']}/recepcion", json={})

    repetida = cliente_api.patch(
        f"{LISTAS}/{lista['id_lista_compra']}/recepcion", json={}
    )
    assert repetida.status_code == 409
    assert _stock(cliente_api, insumo) == 5


def test_anular_devuelve_el_faltante(cliente_api, crear_pedido):
    """El material no queda trabado: se puede volver a pedir."""
    insumo = _material(cliente_api, "Entretela")
    _requerir(cliente_api, crear_pedido(), insumo, 5)
    lista = cliente_api.post(LISTAS).get_json()["datos"]
    assert _faltante(cliente_api, insumo) == 0

    cliente_api.patch(f"{LISTAS}/{lista['id_lista_compra']}/anulacion")

    assert _faltante(cliente_api, insumo) == 5
    assert cliente_api.post(LISTAS).status_code == 201


def test_no_genera_lista_si_no_falta_nada(cliente_api, crear_pedido):
    insumo = _material(cliente_api, "Hilo negro", 50)
    _requerir(cliente_api, crear_pedido(), insumo, 2)
    respuesta = cliente_api.post(LISTAS)
    assert respuesta.status_code == 400
    assert "No falta" in respuesta.get_json()["error"]


# --- Borrar un pedido no reescribe la historia ----------------------------
def test_borrar_un_pedido_no_vacia_la_compra(cliente_api, crear_pedido):
    pedido = crear_pedido()
    insumo = _material(cliente_api, "Botón nácar")
    _requerir(cliente_api, pedido, insumo, 6)
    lista = cliente_api.post(LISTAS).get_json()["datos"]
    cliente_api.patch(f"{LISTAS}/{lista['id_lista_compra']}/recepcion", json={})

    cliente_api.post("/api/pedidos/eliminar", json={"ids": [pedido["id_pedido"]]})

    archivada = cliente_api.get(f"{LISTAS}/{lista['id_lista_compra']}").get_json()["datos"]
    assert len(archivada["detalles"]) == 1
    assert float(archivada["detalles"][0]["cantidad_solicitada"]) == 6
    assert _stock(cliente_api, insumo) == 6


def test_los_movimientos_sobreviven_al_pedido(cliente_api, crear_pedido):
    """La mercadería se movió igual: el asiento queda, sin documento."""
    pedido = crear_pedido()
    insumo = _material(cliente_api, "Hilo negro", 10)
    _requerir(cliente_api, pedido, insumo, 2)
    cliente_api.put(
        f"/api/pedidos/{pedido['id_pedido']}/insumos/{insumo['id_insumo']}",
        json={"estado_insumo": "CONSUMIDO"},
    )
    cliente_api.post("/api/pedidos/eliminar", json={"ids": [pedido["id_pedido"]]})

    movimientos = cliente_api.get(
        f"/api/insumos/{insumo['id_insumo']}/movimientos"
    ).get_json()["datos"]
    assert len(movimientos) == 2
    assert all(movimiento["id_pedido"] is None for movimiento in movimientos)
    assert _stock(cliente_api, insumo) == 8


# --- Reglas del catálogo --------------------------------------------------
def test_no_se_repite_el_nombre_del_material(cliente_api):
    _material(cliente_api, "Hilo negro")
    repetido = cliente_api.post(
        "/api/insumos",
        json={"nombre": "hilo negro", "stock_actual": 0, "unidad_medida": "UNIDADES"},
    )
    assert repetido.status_code == 409


def test_no_se_elimina_un_material_en_uso(cliente_api, crear_pedido):
    insumo = _material(cliente_api, "Hilo negro", 10)
    _requerir(cliente_api, crear_pedido(), insumo, 1)
    assert cliente_api.delete(f"/api/insumos/{insumo['id_insumo']}").status_code == 409


def test_no_se_quita_del_pedido_un_material_consumido(cliente_api, crear_pedido):
    pedido = crear_pedido()
    insumo = _material(cliente_api, "Hilo negro", 10)
    _requerir(cliente_api, pedido, insumo, 2)
    cliente_api.put(
        f"/api/pedidos/{pedido['id_pedido']}/insumos/{insumo['id_insumo']}",
        json={"estado_insumo": "CONSUMIDO"},
    )
    respuesta = cliente_api.delete(
        f"/api/pedidos/{pedido['id_pedido']}/insumos/{insumo['id_insumo']}"
    )
    assert respuesta.status_code == 409
    assert _stock(cliente_api, insumo) == 8


def test_el_nombre_del_material_no_distingue_mayusculas(cliente_api):
    """La base y el servicio comparan igual: sin distinguir mayúsculas.

    Si el índice fuera sobre `nombre` a secas, 'Hilo' pasaría el control de
    la base y lo rechazaría la aplicación, que es peor que rechazarlo antes.
    """
    _material(cliente_api, "Hilo negro")
    for variante in ("hilo negro", "HILO NEGRO", "Hilo Negro"):
        repetido = cliente_api.post(
            "/api/insumos",
            json={"nombre": variante, "stock_actual": 0, "unidad_medida": "UNIDADES"},
        )
        assert repetido.status_code == 409, variante
