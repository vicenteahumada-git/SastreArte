"""Trabajadores y sus cuentas de acceso.

Dar de alta a alguien es crearle la cuenta con la que entra al sistema: las
dos cosas van juntas, y por eso las credenciales son obligatorias.
"""

from pruebas.conftest import CLAVE_PRUEBA

RUTA = "/api/trabajadores"


def _alta(cliente_api, **cambios):
    datos = {
        "nombre": "Rosa",
        "apellido": "Díaz",
        "telefono": "+56 9 1111 0001",
        "nombre_usuario": "rosa.diaz",
        "contrasena": CLAVE_PRUEBA,
    }
    datos.update(cambios)
    return cliente_api.post(RUTA, json=datos)


def _entrar(cliente_api, usuario, clave):
    return cliente_api.post(
        "/api/sesion", json={"nombre_usuario": usuario, "contrasena": clave}
    )


# --- Alta ------------------------------------------------------------------
def test_agrega_trabajador_con_su_cuenta(crear_trabajador):
    trabajador = crear_trabajador()
    assert trabajador["tipo_usuario"] == "TRABAJADOR"
    assert trabajador["estado_usuario"] == "ACTIVO"
    assert trabajador["nombre_usuario"] == "mario.soto"


def test_la_cuenta_recien_creada_puede_entrar(cliente_api):
    """El punto de todo esto: que la persona pueda iniciar sesión."""
    _alta(cliente_api)
    sesion = _entrar(cliente_api, "rosa.diaz", CLAVE_PRUEBA)
    assert sesion.status_code == 200
    assert sesion.get_json()["datos"]["nombre"] == "Rosa"
    assert sesion.get_json()["datos"]["tipo_usuario"] == "TRABAJADOR"


def test_no_entra_con_la_clave_equivocada(cliente_api):
    _alta(cliente_api)
    assert _entrar(cliente_api, "rosa.diaz", "otra-clave").status_code == 401


def test_el_usuario_se_normaliza_a_minusculas(cliente_api):
    creado = _alta(cliente_api, nombre_usuario="Rosa.Diaz").get_json()["datos"]
    assert creado["nombre_usuario"] == "rosa.diaz"


def test_las_credenciales_son_obligatorias(cliente_api):
    sin_usuario = cliente_api.post(
        RUTA, json={"nombre": "Rosa", "telefono": "+56 9 1111 0002"}
    )
    assert sin_usuario.status_code == 400
    assert _alta(cliente_api, nombre_usuario="").status_code == 400
    assert _alta(cliente_api, contrasena="").status_code == 400


def test_se_rechaza_una_contrasena_corta(cliente_api):
    assert _alta(cliente_api, contrasena="corta").status_code == 400


def test_se_rechaza_un_usuario_con_espacios(cliente_api):
    assert _alta(cliente_api, nombre_usuario="rosa diaz").status_code == 400


def test_dos_personas_no_comparten_usuario(cliente_api):
    _alta(cliente_api)
    choque = _alta(cliente_api, nombre="Otra", telefono="+56 9 1111 0003")
    assert choque.status_code == 409
    assert "usuario" in choque.get_json()["error"].lower()


# --- La contraseña nunca sale ---------------------------------------------
def test_la_api_no_devuelve_la_contrasena(cliente_api):
    _alta(cliente_api)
    cuerpo = cliente_api.get(RUTA).get_data(as_text=True)
    assert "contrasena" not in cuerpo
    assert CLAVE_PRUEBA not in cuerpo


def test_la_contrasena_se_guarda_resumida(cliente_api):
    from configuracion.base_datos import conexion
    from servicios import credenciales

    _alta(cliente_api)
    with conexion() as conn:
        guardado = conn.execute(
            "SELECT contrasena_hash FROM usuario WHERE nombre_usuario = 'rosa.diaz'"
        ).fetchone()["contrasena_hash"]

    assert guardado != CLAVE_PRUEBA
    assert CLAVE_PRUEBA not in guardado
    assert credenciales.coincide(CLAVE_PRUEBA, guardado)


# --- Modificación ----------------------------------------------------------
def test_modifica_los_datos_sin_tocar_la_clave(cliente_api, crear_trabajador):
    """La contraseña en blanco conserva la que tenía."""
    trabajador = crear_trabajador()
    respuesta = cliente_api.put(
        f"{RUTA}/{trabajador['id_usuario']}",
        json={
            "nombre": "Mario",
            "apellido": "Pérez",
            "telefono": "+56 9 8080 9090",
            "nombre_usuario": "mario.soto",
        },
    )
    assert respuesta.get_json()["datos"]["apellido"] == "Pérez"
    assert _entrar(cliente_api, "mario.soto", CLAVE_PRUEBA).status_code == 200


def test_cambia_la_contrasena(cliente_api, crear_trabajador):
    trabajador = crear_trabajador()
    cliente_api.put(
        f"{RUTA}/{trabajador['id_usuario']}",
        json={
            "nombre": "Mario",
            "apellido": "Soto",
            "telefono": "+56 9 3344 5566",
            "nombre_usuario": "mario.soto",
            "contrasena": "clave-nueva-123",
        },
    )
    assert _entrar(cliente_api, "mario.soto", CLAVE_PRUEBA).status_code == 401
    assert _entrar(cliente_api, "mario.soto", "clave-nueva-123").status_code == 200


def test_cambia_el_nombre_de_usuario_conservando_la_clave(cliente_api, crear_trabajador):
    trabajador = crear_trabajador()
    cliente_api.put(
        f"{RUTA}/{trabajador['id_usuario']}",
        json={
            "nombre": "Mario",
            "apellido": "Soto",
            "telefono": "+56 9 3344 5566",
            "nombre_usuario": "msoto",
        },
    )
    assert _entrar(cliente_api, "mario.soto", CLAVE_PRUEBA).status_code == 401
    assert _entrar(cliente_api, "msoto", CLAVE_PRUEBA).status_code == 200


def test_no_se_puede_tomar_el_usuario_de_otro(cliente_api, crear_trabajador):
    primero = crear_trabajador()
    segundo = crear_trabajador("Paula", "Ríos", "+56 9 2222 2222")
    respuesta = cliente_api.put(
        f"{RUTA}/{segundo['id_usuario']}",
        json={
            "nombre": "Paula",
            "apellido": "Ríos",
            "telefono": "+56 9 2222 2222",
            "nombre_usuario": primero["nombre_usuario"],
        },
    )
    assert respuesta.status_code == 409


# --- Eliminación -----------------------------------------------------------
def test_eliminar_saca_del_taller_sin_borrar(cliente_api, crear_trabajador):
    """Es baja lógica: los pedidos que hizo conservan su nombre."""
    trabajador = crear_trabajador()
    respuesta = cliente_api.delete(f"{RUTA}/{trabajador['id_usuario']}")
    assert respuesta.status_code == 200
    assert respuesta.get_json()["datos"]["estado_usuario"] == "INACTIVO"
    assert cliente_api.get(f"{RUTA}/{trabajador['id_usuario']}").status_code == 200


def test_no_se_elimina_con_pedidos_encima(cliente_api, crear_pedido, crear_trabajador):
    pedido = crear_pedido()
    trabajador = crear_trabajador()
    cliente_api.post(
        f"/api/pedidos/{pedido['id_pedido']}/asignacion",
        json={"id_trabajador": trabajador["id_usuario"]},
    )
    respuesta = cliente_api.delete(f"{RUTA}/{trabajador['id_usuario']}")
    assert respuesta.status_code == 409
    assert respuesta.get_json()["detalles"] == {"pedidos_asignados": 1}
    # Sigue activo: la operación no dejó nada a medias.
    assert cliente_api.get(f"{RUTA}/{trabajador['id_usuario']}").get_json()["datos"][
        "estado_usuario"
    ] == "ACTIVO"


def test_un_pedido_entregado_no_impide_eliminar(
    cliente_api, crear_pedido, crear_trabajador
):
    """Lo que bloquea es el trabajo pendiente, no el historial."""
    pedido = crear_pedido()
    trabajador = crear_trabajador()
    cliente_api.post(
        f"/api/pedidos/{pedido['id_pedido']}/asignacion",
        json={"id_trabajador": trabajador["id_usuario"]},
    )
    cliente_api.patch(
        f"/api/pedidos/{pedido['id_pedido']}/estado", json={"estado": "ENTREGADO"}
    )
    assert cliente_api.delete(f"{RUTA}/{trabajador['id_usuario']}").status_code == 200


def test_no_se_elimina_dos_veces(cliente_api, crear_trabajador):
    trabajador = crear_trabajador()
    cliente_api.delete(f"{RUTA}/{trabajador['id_usuario']}")
    assert cliente_api.delete(f"{RUTA}/{trabajador['id_usuario']}").status_code == 409


def test_una_clave_guardada_en_claro_no_autentica(cliente_api, crear_trabajador):
    """Regresión: cuentas creadas cuando el login comparaba texto plano.

    En esas filas `contrasena_hash` guarda la clave tal cual. Verificar
    contra eso tiene que fallar sin reventar: la comparación con un resumen
    mal formado devuelve False, no una excepción, así que la API responde
    401 y no 500. Se arreglan reescribiendo la fila con un hash de verdad.
    """
    from configuracion.base_datos import conexion

    trabajador = crear_trabajador()
    with conexion() as conn:
        conn.execute(
            "UPDATE usuario SET contrasena_hash = '12345' WHERE id_usuario = %s",
            (trabajador["id_usuario"],),
        )

    respuesta = _entrar(cliente_api, trabajador["nombre_usuario"], "12345")
    assert respuesta.status_code == 401
