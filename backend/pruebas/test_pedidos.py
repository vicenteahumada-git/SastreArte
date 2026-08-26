from pruebas.conftest import ENTREGA_MAS_LEJANA, ENTREGA_PASADA


def test_registra_pedido_asociado_a_cliente(crear_cliente, crear_pedido):
    cliente = crear_cliente("Inés López", "+56 9 3000 4000")
    pedido = crear_pedido(cliente=cliente, descripcion="Ajuste de vestido")
    assert pedido["id_cliente"] == cliente["id_cliente"]
    assert pedido["cliente_nombre"] == "Inés López"


def test_modifica_descripcion_y_fecha(cliente_api, crear_pedido):
    pedido = crear_pedido()
    respuesta = cliente_api.put(
        f"/api/pedidos/{pedido['id_pedido']}",
        json={"descripcion": "Nueva basta y pinzas", "fecha_entrega": ENTREGA_MAS_LEJANA},
    )
    actualizado = respuesta.get_json()["datos"]
    assert actualizado["descripcion"] == "Nueva basta y pinzas"
    assert actualizado["fecha_entrega"] == ENTREGA_MAS_LEJANA


def test_actualiza_estado_y_prioridad(cliente_api, crear_pedido):
    pedido = crear_pedido()
    estado = cliente_api.patch(
        f"/api/pedidos/{pedido['id_pedido']}/estado", json={"estado": "EN_PROCESO"}
    ).get_json()["datos"]
    prioridad = cliente_api.patch(
        f"/api/pedidos/{pedido['id_pedido']}/prioridad", json={"prioridad": "URGENTE"}
    ).get_json()["datos"]
    assert estado["estado"] == "EN_PROCESO"
    assert prioridad["prioridad"] == "URGENTE"


def test_aplica_descuento_recargo_y_calcula_totales(cliente_api, crear_pedido):
    pedido = crear_pedido(valor_base=30000)
    respuesta = cliente_api.patch(
        f"/api/pedidos/{pedido['id_pedido']}/precio",
        json={"descuento": 5000, "recargo": 2000},
    )
    actualizado = respuesta.get_json()["datos"]
    assert actualizado["valor_neto"] == 27000
    assert actualizado["iva"] == 5130
    assert actualizado["total"] == 32130


def test_rechaza_descuento_que_deja_valor_neto_negativo(cliente_api, crear_pedido):
    pedido = crear_pedido(valor_base=10000)
    respuesta = cliente_api.patch(
        f"/api/pedidos/{pedido['id_pedido']}/precio", json={"descuento": 10001}
    )
    assert respuesta.status_code == 400


# --- Dominios cerrados ----------------------------------------------------
def test_rechaza_estado_fuera_del_dominio(cliente_api, crear_cliente):
    cliente = crear_cliente()
    respuesta = cliente_api.post(
        "/api/pedidos",
        json={
            "id_cliente": cliente["id_cliente"],
            "fecha_entrega": ENTREGA_MAS_LEJANA,
            "descripcion": "Trabajo cualquiera",
            "estado": "banana",
            "valor_base": 1000,
        },
    )
    assert respuesta.status_code == 400
    assert "admite solo" in respuesta.get_json()["error"]


def test_rechaza_prioridad_y_complejidad_invalidas(cliente_api, crear_pedido):
    pedido = crear_pedido()
    respuesta = cliente_api.patch(
        f"/api/pedidos/{pedido['id_pedido']}/prioridad", json={"prioridad": "ULTRA"}
    )
    assert respuesta.status_code == 400


def test_normaliza_estado_a_mayusculas(cliente_api, crear_pedido):
    pedido = crear_pedido()
    actualizado = cliente_api.patch(
        f"/api/pedidos/{pedido['id_pedido']}/estado", json={"estado": "en proceso"}
    ).get_json()["datos"]
    assert actualizado["estado"] == "EN_PROCESO"


def test_expone_las_opciones_validas(cliente_api):
    opciones = cliente_api.get("/api/pedidos/opciones").get_json()["datos"]
    assert "CANCELADO" in opciones["estados"]
    assert opciones["prioridades"] == ["ALTA", "BAJA", "MEDIA", "URGENTE"]


def test_permite_cancelar_un_pedido(cliente_api, crear_pedido):
    pedido = crear_pedido()
    actualizado = cliente_api.patch(
        f"/api/pedidos/{pedido['id_pedido']}/estado", json={"estado": "CANCELADO"}
    ).get_json()["datos"]
    assert actualizado["estado"] == "CANCELADO"


# --- Numeración de guías --------------------------------------------------
def test_el_servidor_asigna_el_numero_e_ignora_el_del_cliente(cliente_api, crear_pedido):
    primero = crear_pedido()
    segundo = crear_pedido(id_pedido=9999, numero_pedido=9999)
    assert segundo["id_pedido"] == primero["id_pedido"] + 1


def test_el_numero_de_guia_no_se_reutiliza_tras_borrar(cliente_api, crear_pedido):
    """La identidad de PostgreSQL nunca reasigna un número ya usado."""
    pedidos = [crear_pedido() for _ in range(3)]
    ultimo = pedidos[-1]

    cliente_api.post("/api/pedidos/eliminar", json={"ids": [ultimo["id_pedido"]]})
    nuevo = crear_pedido()

    assert nuevo["id_pedido"] != ultimo["id_pedido"]
    assert nuevo["id_pedido"] == ultimo["id_pedido"] + 1


def test_la_tabla_pedido_no_tiene_numero_pedido(crear_pedido):
    from configuracion.base_datos import conexion

    crear_pedido()
    with conexion() as conn:
        columnas = {
            fila["column_name"]
            for fila in conn.execute(
                """SELECT column_name FROM information_schema.columns
                   WHERE table_name = 'pedido'
                     AND table_schema = current_schema()"""
            ).fetchall()
        }
    assert "numero_pedido" not in columnas


# --- Fechas y montos ------------------------------------------------------
def test_rechaza_fecha_de_entrega_pasada(cliente_api, crear_cliente):
    cliente = crear_cliente()
    respuesta = cliente_api.post(
        "/api/pedidos",
        json={
            "id_cliente": cliente["id_cliente"],
            "fecha_entrega": ENTREGA_PASADA,
            "descripcion": "Trabajo con fecha vencida",
            "estado": "PENDIENTE",
            "valor_base": 1000,
        },
    )
    assert respuesta.status_code == 400
    assert "no puede ser anterior" in respuesta.get_json()["error"]


def test_descuento_excesivo_al_crear_da_mensaje_claro(cliente_api, crear_cliente):
    cliente = crear_cliente()
    respuesta = cliente_api.post(
        "/api/pedidos",
        json={
            "id_cliente": cliente["id_cliente"],
            "fecha_entrega": ENTREGA_MAS_LEJANA,
            "descripcion": "Trabajo con descuento excesivo",
            "estado": "PENDIENTE",
            "valor_base": 1000,
            "descuento": 50000,
        },
    )
    assert respuesta.status_code == 400
    assert "descuento" in respuesta.get_json()["error"].lower()


def test_acepta_montos_como_decimal_integro(cliente_api, crear_cliente):
    cliente = crear_cliente()
    respuesta = cliente_api.post(
        "/api/pedidos",
        json={
            "id_cliente": cliente["id_cliente"],
            "fecha_entrega": ENTREGA_MAS_LEJANA,
            "descripcion": "Monto enviado como float",
            "estado": "PENDIENTE",
            "valor_base": 30000.0,
        },
    )
    assert respuesta.status_code == 201
    assert respuesta.get_json()["datos"]["valor_base"] == 30000


def test_rechaza_montos_con_decimales(cliente_api, crear_cliente):
    cliente = crear_cliente()
    respuesta = cliente_api.post(
        "/api/pedidos",
        json={
            "id_cliente": cliente["id_cliente"],
            "fecha_entrega": ENTREGA_MAS_LEJANA,
            "descripcion": "Monto con centavos",
            "estado": "PENDIENTE",
            "valor_base": 1000.5,
        },
    )
    assert respuesta.status_code == 400


# --- IVA: la tasa se guarda, el importe se calcula ------------------------
def _columnas_pedido():
    from configuracion.base_datos import conexion

    with conexion() as conn:
        return {
            fila["column_name"]
            for fila in conn.execute(
                """SELECT column_name FROM information_schema.columns
                   WHERE table_name = 'pedido'
                     AND table_schema = current_schema()"""
            ).fetchall()
        }


def test_la_tasa_se_guarda_pero_los_importes_no(crear_pedido):
    """Se almacena la alícuota; iva y total se siguen derivando de ella."""
    crear_pedido()
    columnas = _columnas_pedido()
    assert "tasa_iva" in columnas
    assert {"iva", "total", "saldo_restante"}.isdisjoint(columnas)


def test_el_pedido_nace_con_la_tasa_vigente(crear_pedido):
    pedido = crear_pedido(valor_base=100000)
    assert pedido["tasa_iva"] == 0.19
    assert pedido["iva"] == 19000
    assert pedido["total"] == 119000


def test_un_cambio_de_iva_no_toca_los_pedidos_viejos(
    monkeypatch, cliente_api, crear_pedido
):
    """El motivo de guardar la tasa: no reescribir el pasado.

    Si el IVA sube, el encargo ya tomado tiene que seguir valiendo lo que
    decía su boleta; de lo contrario el saldo dejaría de cuadrar contra lo
    que el cliente ya pagó.
    """
    viejo = crear_pedido(valor_base=100000)

    monkeypatch.setenv("TASA_IVA", "0.10")
    releido = cliente_api.get(f"/api/pedidos/{viejo['id_pedido']}").get_json()["datos"]

    assert releido["tasa_iva"] == 0.19
    assert releido["iva"] == 19000
    assert releido["total"] == 119000


def test_los_pedidos_nuevos_toman_la_tasa_nueva(monkeypatch, crear_pedido):
    monkeypatch.setenv("TASA_IVA", "0.10")
    nuevo = crear_pedido(valor_base=100000)
    assert nuevo["tasa_iva"] == 0.10
    assert nuevo["iva"] == 10000


def test_conviven_pedidos_con_tasas_distintas(monkeypatch, cliente_api, crear_pedido):
    """Cada fila conserva la suya y el listado devuelve ambas."""
    antiguo = crear_pedido(valor_base=100000)
    monkeypatch.setenv("TASA_IVA", "0.21")
    reciente = crear_pedido(valor_base=100000)

    por_id = {
        pedido["id_pedido"]: pedido
        for pedido in cliente_api.get("/api/pedidos").get_json()["datos"]
    }
    assert por_id[antiguo["id_pedido"]]["iva"] == 19000
    assert por_id[reciente["id_pedido"]]["iva"] == 21000


def test_una_tasa_mal_configurada_no_voltea_la_aplicacion(monkeypatch, crear_pedido):
    """Un valor absurdo en la variable cae en la tasa por defecto."""
    monkeypatch.setenv("TASA_IVA", "no-es-un-numero")
    assert crear_pedido(valor_base=100000)["tasa_iva"] == 0.19
    monkeypatch.setenv("TASA_IVA", "7")
    assert crear_pedido(valor_base=100000)["tasa_iva"] == 0.19


def test_el_cliente_no_puede_imponer_su_propia_tasa(cliente_api, crear_cliente):
    """La tasa la pone el modelo; lo que mande el cuerpo se ignora."""
    respuesta = cliente_api.post(
        "/api/pedidos",
        json={
            "id_cliente": crear_cliente()["id_cliente"],
            "fecha_entrega": "2030-01-01",
            "descripcion": "Intento de fijar el IVA a mano",
            "valor_base": 100000,
            "tasa_iva": 0,
        },
    )
    assert respuesta.get_json()["datos"]["tasa_iva"] == 0.19
