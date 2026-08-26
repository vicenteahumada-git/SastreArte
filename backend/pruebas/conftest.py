import os
import uuid
from datetime import timedelta
from pathlib import Path

import psycopg
import pytest
from psycopg import ClientCursor, sql

from app import crear_aplicacion
from configuracion.base_datos import cerrar_pool, conexion, url_base_datos
from configuracion.tiempo import hoy

# Fechas relativas a hoy: la API rechaza entregas en el pasado, así que las
# pruebas no pueden depender de una fecha fija escrita a mano.
ENTREGA_FUTURA = (hoy() + timedelta(days=30)).isoformat()
ENTREGA_MAS_LEJANA = (hoy() + timedelta(days=60)).isoformat()
ENTREGA_PASADA = (hoy() - timedelta(days=1)).isoformat()


@pytest.fixture(scope="session", autouse=True)
def esquema_pruebas():
    esquema = f"prueba_{uuid.uuid4().hex[:10]}"
    archivo_sql = Path(os.getenv("PRUEBAS_SCHEMA_SQL", "/postgresql/schema.sql"))
    if not archivo_sql.exists():
        archivo_sql = Path(__file__).resolve().parents[2] / "postgresql" / "schema.sql"

    conn = psycopg.connect(url_base_datos(), autocommit=True, cursor_factory=ClientCursor)
    conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(esquema)))
    conn.execute(sql.SQL("SET search_path TO {}, public").format(sql.Identifier(esquema)))
    conn.execute(archivo_sql.read_text(encoding="utf-8"))
    os.environ["DB_SCHEMA"] = esquema
    yield esquema
    os.environ.pop("DB_SCHEMA", None)
    # El pool se cierra antes de borrar el esquema para no dejar conexiones
    # apuntando a un search_path inexistente.
    cerrar_pool()
    conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(esquema)))
    conn.close()


@pytest.fixture(autouse=True)
def limpiar_datos(esquema_pruebas):
    with conexion() as conn:
        conn.execute(
            """TRUNCATE TABLE detalle_insumo, pago, asignacion, pedido,
                              cliente, usuario, insumo, lista_compra
               RESTART IDENTITY CASCADE"""
        )


@pytest.fixture()
def cliente_api():
    aplicacion = crear_aplicacion()
    aplicacion.config.update(TESTING=True)
    return aplicacion.test_client()


@pytest.fixture()
def crear_cliente(cliente_api):
    def fabrica(nombre="Ana Torres", telefono="+56 9 1234 5678"):
        respuesta = cliente_api.post(
            "/api/clientes", json={"nombre": nombre, "telefono": telefono}
        )
        assert respuesta.status_code == 201
        return respuesta.get_json()["datos"]

    return fabrica


@pytest.fixture()
def crear_pedido(cliente_api, crear_cliente):
    def fabrica(cliente=None, **cambios):
        cliente = cliente or crear_cliente()
        datos = {
            "id_cliente": cliente["id_cliente"],
            "fecha_entrega": ENTREGA_FUTURA,
            "descripcion": "Ajuste de chaqueta de vestir",
            "estado": "PENDIENTE",
            "prioridad": "MEDIA",
            "complejidad": "MEDIA",
            "tiempo_estimado_horas": 4,
            "valor_base": 30000,
            "descuento": 0,
            "recargo": 0,
        }
        datos.update(cambios)
        respuesta = cliente_api.post("/api/pedidos", json=datos)
        assert respuesta.status_code == 201, respuesta.get_json()
        return respuesta.get_json()["datos"]

    return fabrica


# Contraseña de los trabajadores de prueba. Alta y cuenta son la misma
# operación, así que la fábrica tiene que crear las credenciales.
CLAVE_PRUEBA = "sastrearte2026"


@pytest.fixture()
def crear_trabajador(cliente_api):
    def fabrica(
        nombre="Mario",
        apellido="Soto",
        telefono="+56 9 3344 5566",
        usuario=None,
        contrasena=CLAVE_PRUEBA,
    ):
        # El usuario sale del nombre si no se indica, para que dos altas
        # seguidas no choquen contra la unicidad.
        if usuario is None:
            usuario = f"{nombre}.{apellido or 'x'}".lower().replace(" ", "")
            usuario = "".join(c for c in usuario if c.isascii() and (c.isalnum() or c in "._-"))
        respuesta = cliente_api.post(
            "/api/trabajadores",
            json={
                "nombre": nombre,
                "apellido": apellido,
                "telefono": telefono,
                "nombre_usuario": usuario,
                "contrasena": contrasena,
            },
        )
        assert respuesta.status_code == 201, respuesta.get_json()
        return respuesta.get_json()["datos"]

    return fabrica


@pytest.fixture()
def crear_insumo(cliente_api):
    def fabrica(nombre="Hilo azul", stock=10, unidad="UNIDADES"):
        respuesta = cliente_api.post(
            "/api/insumos",
            json={"nombre": nombre, "stock_actual": stock, "unidad_medida": unidad},
        )
        assert respuesta.status_code == 201
        return respuesta.get_json()["datos"]

    return fabrica

