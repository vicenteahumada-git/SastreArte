def test_registra_cliente(cliente_api):
    respuesta = cliente_api.post(
        "/api/clientes", json={"nombre": "Elisa Prado", "telefono": "+56 9 5555 1010"}
    )
    assert respuesta.status_code == 201
    assert respuesta.get_json()["datos"]["nombre"] == "Elisa Prado"


def test_busca_cliente_por_nombre(cliente_api, crear_cliente):
    crear_cliente("Camila Fuentes", "+56 9 1111 2222")
    crear_cliente("Óscar Vidal", "+56 9 3333 4444")
    datos = cliente_api.get("/api/clientes?nombre=Camila").get_json()["datos"]
    assert [cliente["nombre"] for cliente in datos] == ["Camila Fuentes"]


def test_busca_cliente_por_telefono(cliente_api, crear_cliente):
    creado = crear_cliente("Rosa Mena", "+56 9 9876 5432")
    datos = cliente_api.get("/api/clientes?telefono=9876").get_json()["datos"]
    assert datos[0]["id_cliente"] == creado["id_cliente"]


def test_rechaza_datos_invalidos(cliente_api):
    respuesta = cliente_api.post("/api/clientes", json={"nombre": "", "telefono": "abc"})
    assert respuesta.status_code == 400
    assert "error" in respuesta.get_json()


# --- Modificar ------------------------------------------------------------
def test_modifica_nombre_y_telefono(cliente_api, crear_cliente):
    cliente = crear_cliente("Rosa Mena", "+56 9 1111 0000")
    respuesta = cliente_api.put(
        f"/api/clientes/{cliente['id_cliente']}",
        json={"nombre": "Rosa Mena Díaz", "telefono": "+56 9 2222 0000"},
    )
    assert respuesta.status_code == 200
    actualizado = respuesta.get_json()["datos"]
    assert actualizado["nombre"] == "Rosa Mena Díaz"
    assert actualizado["telefono"] == "+56 9 2222 0000"
    assert actualizado["id_cliente"] == cliente["id_cliente"]


def test_el_cambio_se_refleja_en_sus_pedidos(cliente_api, crear_cliente, crear_pedido):
    cliente = crear_cliente("Nombre Viejo", "+56 9 3333 0000")
    pedido = crear_pedido(cliente=cliente)
    cliente_api.put(
        f"/api/clientes/{cliente['id_cliente']}",
        json={"nombre": "Nombre Nuevo", "telefono": "+56 9 3333 0000"},
    )
    actual = cliente_api.get(f"/api/pedidos/{pedido['id_pedido']}").get_json()["datos"]
    assert actual["cliente_nombre"] == "Nombre Nuevo"


def test_modificar_rechaza_datos_invalidos(cliente_api, crear_cliente):
    cliente = crear_cliente()
    respuesta = cliente_api.put(
        f"/api/clientes/{cliente['id_cliente']}",
        json={"nombre": "Ana", "telefono": "abc"},
    )
    assert respuesta.status_code == 400


def test_modificar_un_cliente_inexistente(cliente_api):
    respuesta = cliente_api.put(
        "/api/clientes/999999", json={"nombre": "Fantasma", "telefono": "+56 9 0000 0000"}
    )
    assert respuesta.status_code == 404


# --- Eliminar -------------------------------------------------------------
def test_elimina_un_cliente_sin_pedidos(cliente_api, crear_cliente):
    cliente = crear_cliente("Sin Pedidos", "+56 9 4444 0000")
    respuesta = cliente_api.delete(f"/api/clientes/{cliente['id_cliente']}")
    assert respuesta.status_code == 200
    assert cliente_api.get(f"/api/clientes/{cliente['id_cliente']}").status_code == 404


def test_no_elimina_un_cliente_con_pedidos(cliente_api, crear_cliente, crear_pedido):
    """Borrarlo arrastraría sus pedidos y los pagos de esos pedidos."""
    cliente = crear_cliente("Con Pedidos", "+56 9 5555 0000")
    crear_pedido(cliente=cliente)

    respuesta = cliente_api.delete(f"/api/clientes/{cliente['id_cliente']}")
    assert respuesta.status_code == 409
    assert "pedido asociado" in respuesta.get_json()["error"]
    assert respuesta.get_json()["detalles"]["pedidos"] == 1
    assert cliente_api.get(f"/api/clientes/{cliente['id_cliente']}").status_code == 200


def test_eliminar_un_cliente_inexistente(cliente_api):
    assert cliente_api.delete("/api/clientes/999999").status_code == 404


def test_solo_la_duena_puede_eliminar_clientes(cliente_api, crear_cliente):
    cliente = crear_cliente("Protegida", "+56 9 6666 0000")
    respuesta = cliente_api.delete(
        f"/api/clientes/{cliente['id_cliente']}",
        headers={"X-Rol-Operativo": "TRABAJADOR"},
    )
    assert respuesta.status_code == 403
    assert cliente_api.get(f"/api/clientes/{cliente['id_cliente']}").status_code == 200


def test_el_taller_si_puede_modificar(cliente_api, crear_cliente):
    """Corregir un teléfono mal anotado no requiere ser la dueña."""
    cliente = crear_cliente("Teléfono Malo", "+56 9 7777 0000")
    respuesta = cliente_api.put(
        f"/api/clientes/{cliente['id_cliente']}",
        json={"nombre": "Teléfono Bueno", "telefono": "+56 9 7777 1111"},
        headers={"X-Rol-Operativo": "TRABAJADOR"},
    )
    assert respuesta.status_code == 200

