"""Reglas de negocio de los trabajadores (capa modelo).

Cada trabajador es también una cuenta: se da de alta con su nombre de usuario
y su contraseña, porque un trabajador que no puede entrar al sistema no sirve
de mucho. La contraseña se guarda resumida (servicios/credenciales.py) y no
sale nunca por la API.
"""

from configuracion.errores import ErrorDominio
from repositorios import trabajadores as repositorio
from servicios import credenciales
from servicios.validaciones import telefono, texto_opcional, texto_requerido


def listar(estado: str = "") -> list[dict]:
    estado = estado.strip().upper()
    if estado and estado not in {"ACTIVO", "INACTIVO"}:
        raise ErrorDominio("El estado de trabajador no es válido.")
    return repositorio.listar(estado)


def obtener(id_trabajador: int) -> dict:
    trabajador = repositorio.obtener(id_trabajador)
    if not trabajador:
        raise ErrorDominio("Trabajador no encontrado.", 404)
    return trabajador


def _campos(datos: dict) -> tuple[str, str | None, str | None]:
    return (
        texto_requerido(datos, "nombre", 100),
        texto_opcional(datos, "apellido", 100),
        telefono(datos, obligatorio=False),
    )


def _comprobar_usuario_libre(usuario: str, excluir: int | None = None) -> None:
    if repositorio.buscar_por_nombre_usuario(usuario, excluir):
        raise ErrorDominio("Ese nombre de usuario ya está tomado.", 409)


def crear(datos: dict) -> dict:
    """Da de alta al trabajador junto con su cuenta de acceso."""
    nombre, apellido, telefono_valor = _campos(datos)
    if repositorio.buscar_duplicado(nombre, telefono_valor or ""):
        raise ErrorDominio("El trabajador ya existe.", 409)

    acceso = credenciales.desde_datos(datos, obligatorias=True)
    _comprobar_usuario_libre(acceso[0])
    return repositorio.crear(nombre, apellido, telefono_valor, acceso)


def modificar(id_trabajador: int, datos: dict) -> dict:
    """Actualiza los datos y, si se indicó una nueva, la contraseña.

    Dejar la contraseña en blanco conserva la que tenía: editar un teléfono
    no puede obligar a inventarle una clave nueva a la persona.
    """
    actual = obtener(id_trabajador)
    nombre, apellido, telefono_valor = _campos(datos)
    if repositorio.buscar_duplicado(nombre, telefono_valor or "", id_trabajador):
        raise ErrorDominio("Ya existe otro trabajador con esos datos.", 409)

    if datos.get("contrasena"):
        acceso = credenciales.desde_datos(datos, obligatorias=True)
        _comprobar_usuario_libre(acceso[0], id_trabajador)
        actualizado = repositorio.modificar(
            id_trabajador, nombre, apellido, telefono_valor, acceso
        )
    else:
        # Sin contraseña nueva, el nombre de usuario todavía puede cambiar.
        usuario = credenciales.solo_usuario(datos) or actual["nombre_usuario"]
        if usuario and usuario != actual["nombre_usuario"]:
            _comprobar_usuario_libre(usuario, id_trabajador)
        actualizado = repositorio.modificar(
            id_trabajador, nombre, apellido, telefono_valor, nombre_usuario=usuario
        )

    if not actualizado:
        raise ErrorDominio("Trabajador no encontrado.", 404)
    return actualizado


def eliminar(id_trabajador: int) -> dict:
    """Saca al trabajador del taller.

    Es una baja lógica, no un borrado: los pedidos que hizo conservan quién
    los hizo, y esa historia se perdería al borrar la fila. Por eso también
    se impide sacar a alguien que todavía tiene pedidos encima.
    """
    trabajador = obtener(id_trabajador)
    if trabajador["estado_usuario"] == "INACTIVO":
        raise ErrorDominio("El trabajador ya está fuera del taller.", 409)

    pedidos = repositorio.contar_pedidos_asignados(id_trabajador)
    if pedidos:
        raise ErrorDominio(
            f"No se puede eliminar: tiene {pedidos} "
            f"{'pedido asignado' if pedidos == 1 else 'pedidos asignados'}. "
            "Reasígnalos primero.",
            409,
            detalles={"pedidos_asignados": pedidos},
        )

    actualizado = repositorio.dar_baja(id_trabajador)
    if not actualizado:
        raise ErrorDominio("Trabajador no encontrado.", 404)
    return actualizado
