from configuracion.errores import ErrorDominio
from repositorios import clientes as repositorio
from servicios.validaciones import telefono, texto_requerido


def listar(nombre: str = "", telefono_busqueda: str = "", general: str = "") -> list[dict]:
    return repositorio.listar(nombre.strip(), telefono_busqueda.strip(), general.strip())


def obtener(id_cliente: int) -> dict:
    cliente = repositorio.obtener(id_cliente)
    if not cliente:
        raise ErrorDominio("Cliente no encontrado.", 404)
    return cliente


def _campos(datos: dict) -> tuple[str, str]:
    return texto_requerido(datos, "nombre", 150), telefono(datos) or ""


def crear(datos: dict) -> dict:
    return repositorio.crear(*_campos(datos))


def modificar(id_cliente: int, datos: dict) -> dict:
    obtener(id_cliente)
    actualizado = repositorio.modificar(id_cliente, *_campos(datos))
    if not actualizado:
        raise ErrorDominio("Cliente no encontrado.", 404)
    return actualizado


def eliminar(id_cliente: int) -> dict:
    """Elimina el cliente sólo si no tiene pedidos.

    No se borra en cascada a propósito: arrastrar los pedidos se llevaría
    también sus pagos y su historial. Si el cliente ya no opera, conviene
    conservar la ficha o eliminar antes sus pedidos de forma explícita.
    """
    cliente = obtener(id_cliente)

    pedidos = repositorio.contar_pedidos(id_cliente)
    if pedidos:
        raise ErrorDominio(
            f"No se puede eliminar a «{cliente['nombre']}» porque tiene "
            f"{pedidos} {'pedido asociado' if pedidos == 1 else 'pedidos asociados'}.",
            409,
            detalles={"pedidos": pedidos},
        )

    repositorio.eliminar(id_cliente)
    return {"eliminado": True, "id_cliente": id_cliente}
