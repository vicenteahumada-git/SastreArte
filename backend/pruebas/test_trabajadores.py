def test_crea_trabajador(crear_trabajador):
    trabajador = crear_trabajador()
    assert trabajador["tipo_usuario"] == "TRABAJADOR"
    assert trabajador["estado_usuario"] == "ACTIVO"


def test_modifica_trabajador(cliente_api, crear_trabajador):
    trabajador = crear_trabajador()
    respuesta = cliente_api.put(
        f"/api/trabajadores/{trabajador['id_usuario']}",
        json={"nombre": "Mario", "apellido": "Pérez", "telefono": "+56 9 8080 9090"},
    )
    assert respuesta.get_json()["datos"]["apellido"] == "Pérez"


def test_baja_trabajador_sin_eliminarlo(cliente_api, crear_trabajador):
    trabajador = crear_trabajador()
    respuesta = cliente_api.patch(f"/api/trabajadores/{trabajador['id_usuario']}/baja")
    assert respuesta.get_json()["datos"]["estado_usuario"] == "INACTIVO"
    consulta = cliente_api.get(f"/api/trabajadores/{trabajador['id_usuario']}")
    assert consulta.status_code == 200


# --- Credenciales de acceso -----------------------------------------------
CLAVE = "sastrearte2026"


def test_el_trabajador_puede_no_tener_acceso(crear_trabajador):
    """Las credenciales son opcionales: no todos entran al sistema."""
    assert crear_trabajador()["nombre_usuario"] is None


def test_crea_trabajador_con_acceso(cliente_api):
    respuesta = cliente_api.post(
        "/api/trabajadores",
        json={
            "nombre": "Rosa",
            "telefono": "+56 9 1111 0001",
            "nombre_usuario": "Rosa.Costurera",
            "contrasena": CLAVE,
        },
    )
    assert respuesta.status_code == 201
    # Se normaliza a minúsculas para que nadie quede afuera por la mayúscula.
    assert respuesta.get_json()["datos"]["nombre_usuario"] == "rosa.costurera"


def test_la_api_nunca_devuelve_la_contrasena(cliente_api):
    cliente_api.post(
        "/api/trabajadores",
        json={
            "nombre": "Rosa",
            "telefono": "+56 9 1111 0002",
            "nombre_usuario": "rosa2",
            "contrasena": CLAVE,
        },
    )
    cuerpo = cliente_api.get("/api/trabajadores").get_data(as_text=True)
    assert "contrasena" not in cuerpo
    assert CLAVE not in cuerpo


def test_la_contrasena_se_guarda_resumida(cliente_api):
    """En la base va el hash, nunca el texto que escribió la persona."""
    from configuracion.base_datos import conexion

    cliente_api.post(
        "/api/trabajadores",
        json={
            "nombre": "Rosa",
            "telefono": "+56 9 1111 0003",
            "nombre_usuario": "rosa3",
            "contrasena": CLAVE,
        },
    )
    with conexion() as conn:
        guardado = conn.execute(
            "SELECT contrasena_hash FROM usuario WHERE nombre_usuario = 'rosa3'"
        ).fetchone()["contrasena_hash"]

    assert guardado != CLAVE
    assert CLAVE not in guardado

    from servicios import credenciales

    assert credenciales.coincide(CLAVE, guardado)
    assert not credenciales.coincide("otra-clave", guardado)


def test_dos_personas_no_comparten_nombre_de_usuario(cliente_api):
    base = {"nombre_usuario": "repetido", "contrasena": CLAVE}
    cliente_api.post(
        "/api/trabajadores", json={"nombre": "Uno", "telefono": "+56 9 1111 0004", **base}
    )
    choque = cliente_api.post(
        "/api/trabajadores", json={"nombre": "Dos", "telefono": "+56 9 1111 0005", **base}
    )
    assert choque.status_code == 409
    assert "usuario" in choque.get_json()["error"].lower()


def test_no_se_aceptan_credenciales_a_medias(cliente_api):
    respuesta = cliente_api.post(
        "/api/trabajadores",
        json={"nombre": "Rosa", "telefono": "+56 9 1111 0006", "nombre_usuario": "rosa6"},
    )
    assert respuesta.status_code == 400


def test_se_rechaza_una_contrasena_corta(cliente_api):
    respuesta = cliente_api.post(
        "/api/trabajadores",
        json={
            "nombre": "Rosa",
            "telefono": "+56 9 1111 0007",
            "nombre_usuario": "rosa7",
            "contrasena": "corta",
        },
    )
    assert respuesta.status_code == 400


def test_se_rechaza_un_nombre_de_usuario_con_espacios(cliente_api):
    respuesta = cliente_api.post(
        "/api/trabajadores",
        json={
            "nombre": "Rosa",
            "telefono": "+56 9 1111 0008",
            "nombre_usuario": "rosa con espacios",
            "contrasena": CLAVE,
        },
    )
    assert respuesta.status_code == 400


def test_editar_el_telefono_no_borra_el_acceso(cliente_api):
    """Modificar sin mandar credenciales deja las que ya estaban."""
    creado = cliente_api.post(
        "/api/trabajadores",
        json={
            "nombre": "Rosa",
            "telefono": "+56 9 1111 0009",
            "nombre_usuario": "rosa9",
            "contrasena": CLAVE,
        },
    ).get_json()["datos"]

    editado = cliente_api.put(
        f"/api/trabajadores/{creado['id_usuario']}",
        json={"nombre": "Rosa", "telefono": "+56 9 2222 0009"},
    ).get_json()["datos"]

    assert editado["nombre_usuario"] == "rosa9"
