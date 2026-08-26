"""Servicio de inicio de sesión.

La contraseña nunca se compara en claro: lo que hay guardado es el resumen
con sal que produce servicios/credenciales.py, y la verificación se delega
ahí. Es también lo que permite que una cuenta creada desde la pantalla de
trabajadores pueda entrar: esa pantalla guarda el hash, no el texto.
"""

from configuracion.base_datos import conexion
from configuracion.errores import ErrorDominio
from servicios import credenciales


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

    # Un solo mensaje para usuario inexistente y clave equivocada: decir cuál
    # de los dos falló le confirmaría a un desconocido qué usuarios existen.
    if not fila or not credenciales.coincide(clave, fila["contrasena_hash"]):
        raise ErrorDominio("Usuario o contraseña incorrectos.", 401)

    if fila["estado_usuario"] != "ACTIVO":
        raise ErrorDominio("El usuario está inactivo. Contacte a la administradora.", 403)

    return {
        "id_usuario": fila["id_usuario"],
        "nombre": fila["nombre"],
        "apellido": fila["apellido"],
        "tipo_usuario": fila["tipo_usuario"],
    }
