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


def _credenciales(datos: dict, excluir: int | None = None) -> tuple[str, str] | None:
    """Valida el acceso, si se pidió uno, y comprueba que esté libre."""
    acceso = credenciales.desde_datos(datos)
    if acceso and repositorio.buscar_por_nombre_usuario(acceso[0], excluir):
        raise ErrorDominio("Ese nombre de usuario ya está tomado.", 409)
    return acceso


def crear(datos: dict) -> dict:
    nombre, apellido, telefono_valor = _campos(datos)
    if repositorio.buscar_duplicado(nombre, telefono_valor or ""):
        raise ErrorDominio("El trabajador ya existe.", 409)
    return repositorio.crear(
        nombre, apellido, telefono_valor, _credenciales(datos)
    )


def modificar(id_trabajador: int, datos: dict) -> dict:
    obtener(id_trabajador)
    nombre, apellido, telefono_valor = _campos(datos)
    if repositorio.buscar_duplicado(nombre, telefono_valor or "", id_trabajador):
        raise ErrorDominio("Ya existe otro trabajador con esos datos.", 409)
    actualizado = repositorio.modificar(
        id_trabajador,
        nombre,
        apellido,
        telefono_valor,
        _credenciales(datos, id_trabajador),
    )
    if not actualizado:
        raise ErrorDominio("Trabajador no encontrado.", 404)
    return actualizado


def dar_baja(id_trabajador: int) -> dict:
    obtener(id_trabajador)
    actualizado = repositorio.dar_baja(id_trabajador)
    if not actualizado:
        raise ErrorDominio("Trabajador no encontrado.", 404)
    return actualizado

