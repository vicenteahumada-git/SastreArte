"""Servicio de inicio de sesión — contraseña en texto plano (demo local)."""

from configuracion.base_datos import conexion
from configuracion.errores import ErrorDominio


def iniciar(datos: dict) -> dict:
    nombre_usr = datos.get("nombre_usuario", "").strip().lower()
    clave = datos.get("contrasena", "")

    if not nombre_usr or not clave:
        raise ErrorDominio("El usuario y la contraseña son obligatorios.", 400)

    with conexion() as conn:
        fila = conn.execute(
            """SELECT id_usuario, nombre, apellido, tipo_usuario,
                      estado_usuario, contrasena_hash
                 FROM usuario
                WHERE nombre_usuario = %s
                LIMIT 1""",
            (nombre_usr,),
        ).fetchone()

    if not fila or fila["contrasena_hash"] != clave:
        raise ErrorDominio("Usuario o contraseña incorrectos.", 401)

    if fila["estado_usuario"] != "ACTIVO":
        raise ErrorDominio("El usuario está inactivo. Contacte a la administradora.", 403)

    return {
        "id_usuario": fila["id_usuario"],
        "nombre": fila["nombre"],
        "apellido": fila["apellido"],
        "tipo_usuario": fila["tipo_usuario"],
    }
