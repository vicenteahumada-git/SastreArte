"""Credenciales de acceso (capa modelo).

Acá vive todo lo que tenga que ver con el nombre de usuario y la contraseña.
Está aparte de servicios/trabajadores.py a propósito: el día que se agregue
el inicio de sesión, la comprobación de la clave ya tiene dónde ir y no hay
que repartir la regla por varios archivos.

La contraseña **nunca** se guarda en claro. Lo que va a la base es el
resumen que produce Werkzeug —que ya viene con Flask, así que no suma
dependencias— con su sal incluida en el mismo texto.
"""

import re

from werkzeug.security import check_password_hash, generate_password_hash

from configuracion.errores import ErrorDominio
from servicios.validaciones import texto_requerido

# Mismo patrón que el CHECK de la tabla usuario: minúsculas, dígitos y
# punto, guion o guion bajo. Sin espacios ni mayúsculas, para que nadie
# quede afuera por escribir su usuario distinto de como lo creó.
PATRON_NOMBRE_USUARIO = re.compile(r"^[a-z0-9._-]{3,50}$")

LARGO_MINIMO_CONTRASENA = 8
LARGO_MAXIMO_CONTRASENA = 128


def nombre_usuario(datos: dict, campo: str = "nombre_usuario") -> str:
    """Valida y normaliza el nombre de usuario."""
    valor = texto_requerido(datos, campo, 50).lower()
    if not PATRON_NOMBRE_USUARIO.fullmatch(valor):
        raise ErrorDominio(
            "El nombre de usuario admite entre 3 y 50 caracteres, "
            "sólo letras minúsculas, números, punto, guion y guion bajo."
        )
    return valor


def contrasena(datos: dict, campo: str = "contrasena") -> str:
    """Valida la contraseña en claro antes de resumirla."""
    valor = datos.get(campo)
    if not isinstance(valor, str) or not valor:
        raise ErrorDominio("La contraseña es obligatoria.")
    # Sin .strip(): un espacio al principio o al final es parte de la clave.
    if len(valor) < LARGO_MINIMO_CONTRASENA:
        raise ErrorDominio(
            f"La contraseña debe tener al menos {LARGO_MINIMO_CONTRASENA} caracteres."
        )
    if len(valor) > LARGO_MAXIMO_CONTRASENA:
        raise ErrorDominio(
            f"La contraseña admite hasta {LARGO_MAXIMO_CONTRASENA} caracteres."
        )
    return valor


def resumir(clave: str) -> str:
    """Devuelve el hash con sal que se guarda en la base."""
    return generate_password_hash(clave)


def coincide(clave: str, resumen: str | None) -> bool:
    """Compara una contraseña en claro contra el hash almacenado."""
    if not resumen:
        return False
    return check_password_hash(resumen, clave)


def desde_datos(datos: dict, obligatorias: bool = False) -> tuple[str, str] | None:
    """Extrae usuario y hash de un cuerpo JSON.

    Con `obligatorias` las dos tienen que venir: es el caso del alta, donde
    crear el trabajador es crear su cuenta.

    Sin ella devuelve None cuando no viene ninguna, que es lo que permite
    editar el teléfono de alguien sin obligar a reescribir su contraseña.
    Si viene sólo una, es un error: la base no acepta credenciales a medias.
    """
    usuario_crudo = datos.get("nombre_usuario")
    clave_cruda = datos.get("contrasena")
    hay_usuario = isinstance(usuario_crudo, str) and usuario_crudo.strip()
    hay_clave = isinstance(clave_cruda, str) and clave_cruda

    if not hay_usuario and not hay_clave:
        if obligatorias:
            raise ErrorDominio(
                "El nombre de usuario y la contraseña son obligatorios."
            )
        return None
    if not hay_usuario or not hay_clave:
        raise ErrorDominio(
            "Para dar acceso hay que indicar el nombre de usuario y la contraseña."
        )
    return nombre_usuario(datos), resumir(contrasena(datos))


def solo_usuario(datos: dict) -> str | None:
    """Nombre de usuario nuevo cuando se edita sin cambiar la contraseña."""
    valor = datos.get("nombre_usuario")
    if not isinstance(valor, str) or not valor.strip():
        return None
    return nombre_usuario(datos)
