from configuracion.base_datos import conexion

# Lo que se devuelve al exterior. contrasena_hash queda deliberadamente
# fuera: el resumen de la clave no sale nunca de la base de datos.
DEVUELVE = """id_usuario, nombre, apellido, telefono, nombre_usuario,
              estado_usuario, tipo_usuario"""


def listar(estado: str = "") -> list[dict]:
    filtro = "AND estado_usuario = %s" if estado else ""
    parametros = (estado,) if estado else ()
    with conexion() as conn:
        return conn.execute(
            f"""SELECT {DEVUELVE}
                 FROM usuario
                 WHERE tipo_usuario = 'TRABAJADOR' {filtro}
                 ORDER BY estado_usuario, nombre, apellido""",
            parametros,
        ).fetchall()


def obtener(id_trabajador: int) -> dict | None:
    with conexion() as conn:
        return conn.execute(
            f"""SELECT {DEVUELVE}
               FROM usuario WHERE id_usuario = %s AND tipo_usuario = 'TRABAJADOR'""",
            (id_trabajador,),
        ).fetchone()


def buscar_duplicado(nombre: str, telefono: str, excluir: int | None = None) -> dict | None:
    condicion = "AND id_usuario <> %s" if excluir else ""
    parametros = [nombre, telefono]
    if excluir:
        parametros.append(excluir)
    with conexion() as conn:
        return conn.execute(
            f"""SELECT id_usuario FROM usuario
                 WHERE tipo_usuario = 'TRABAJADOR'
                   AND lower(nombre) = lower(%s) AND telefono = %s {condicion}
                 LIMIT 1""",
            parametros,
        ).fetchone()


def buscar_por_nombre_usuario(nombre_usuario: str, excluir: int | None = None) -> dict | None:
    """Busca a cualquier usuario por su nombre de acceso.

    No filtra por tipo_usuario: el nombre de usuario es único en toda la
    tabla, así que un trabajador tampoco puede quedarse con el de la dueña.
    """
    condicion = "AND id_usuario <> %s" if excluir else ""
    parametros = [nombre_usuario] + ([excluir] if excluir else [])
    with conexion() as conn:
        return conn.execute(
            f"SELECT id_usuario FROM usuario WHERE nombre_usuario = %s {condicion} LIMIT 1",
            parametros,
        ).fetchone()


def crear(
    nombre: str,
    apellido: str | None,
    telefono: str | None,
    credenciales: tuple[str, str] | None = None,
) -> dict:
    """Da de alta un trabajador, con acceso al sistema o sin él."""
    usuario, resumen = credenciales or (None, None)
    with conexion() as conn:
        return conn.execute(
            f"""INSERT INTO usuario (
                    nombre, apellido, telefono, nombre_usuario,
                    contrasena_hash, estado_usuario, tipo_usuario
                )
               VALUES (%s, %s, %s, %s, %s, 'ACTIVO', 'TRABAJADOR')
               RETURNING {DEVUELVE}""",
            (nombre, apellido, telefono, usuario, resumen),
        ).fetchone()


def modificar(
    id_trabajador: int,
    nombre: str,
    apellido: str | None,
    telefono: str | None,
    credenciales: tuple[str, str] | None = None,
    nombre_usuario: str | None = None,
) -> dict | None:
    """Actualiza los datos del trabajador.

    Con `credenciales` cambia usuario y contraseña. Con `nombre_usuario` sólo
    el usuario, dejando la contraseña como estaba: editar el teléfono de
    alguien no puede tener el efecto lateral de borrarle el acceso.
    """
    if credenciales is not None:
        asignaciones = ", nombre_usuario = %s, contrasena_hash = %s"
        extra = list(credenciales)
    elif nombre_usuario is not None:
        asignaciones = ", nombre_usuario = %s"
        extra = [nombre_usuario]
    else:
        asignaciones, extra = "", []

    with conexion() as conn:
        return conn.execute(
            f"""UPDATE usuario
                SET nombre = %s, apellido = %s, telefono = %s{asignaciones}
               WHERE id_usuario = %s AND tipo_usuario = 'TRABAJADOR'
               RETURNING {DEVUELVE}""",
            [nombre, apellido, telefono, *extra, id_trabajador],
        ).fetchone()


def contar_pedidos_asignados(id_trabajador: int) -> int:
    """Pedidos que todavía tiene encima, sin contar los ya cerrados."""
    with conexion() as conn:
        return conn.execute(
            """SELECT COUNT(*) AS total
               FROM asignacion a
               JOIN pedido p ON p.id_pedido = a.id_pedido
               WHERE a.id_trabajador = %s
                 AND p.estado NOT IN ('ENTREGADO', 'CANCELADO')""",
            (id_trabajador,),
        ).fetchone()["total"]


def dar_baja(id_trabajador: int) -> dict | None:
    with conexion() as conn:
        return conn.execute(
            f"""UPDATE usuario SET estado_usuario = 'INACTIVO'
               WHERE id_usuario = %s AND tipo_usuario = 'TRABAJADOR'
               RETURNING {DEVUELVE}""",
            (id_trabajador,),
        ).fetchone()

