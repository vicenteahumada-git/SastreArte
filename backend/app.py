import os
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import psycopg
from flask import Flask, jsonify, request, send_from_directory
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS
from werkzeug.exceptions import HTTPException, NotFound
from werkzeug.security import safe_join

from configuracion.errores import ErrorDominio

# Frontend ya compilado. Sólo existe en despliegue: en desarrollo lo sirve Vite.
FRONTEND = Path(__file__).resolve().parents[1] / "frontend" / "dist"


def origenes_permitidos() -> list[str]:
    """Orígenes habilitados para el frontend (CORS_ORIGINS, separados por coma)."""
    return [
        origen.strip()
        for origen in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if origen.strip()
    ]


class JSONSastreArte(DefaultJSONProvider):
    @staticmethod
    def default(valor):
        if isinstance(valor, (date, datetime)):
            return valor.isoformat()
        if isinstance(valor, timedelta):
            return round(valor.total_seconds() / 3600, 2)
        if isinstance(valor, Decimal):
            return int(valor) if valor == valor.to_integral_value() else float(valor)
        return DefaultJSONProvider.default(valor)


def crear_aplicacion() -> Flask:
    aplicacion = Flask(__name__)
    aplicacion.json = JSONSastreArte(aplicacion)
    CORS(aplicacion, resources={r"/api/*": {"origins": origenes_permitidos()}})

    from rutas.clientes import clientes_bp
    from rutas.compras import compras_bp
    from rutas.insumos import insumos_bp
    from rutas.pagos import pagos_bp
    from rutas.pedidos import pedidos_bp
    from rutas.resumen import resumen_bp
    from rutas.sesion import sesion_bp
    from rutas.trabajadores import trabajadores_bp

    for blueprint in (
        clientes_bp,
        pedidos_bp,
        pagos_bp,
        insumos_bp,
        compras_bp,
        trabajadores_bp,
        resumen_bp,
        sesion_bp,
    ):
        aplicacion.register_blueprint(blueprint)

    @aplicacion.get("/api/salud")
    def salud():
        return jsonify({"datos": {"estado": "ok", "servicio": "SastreArte API"}})

    _registrar_frontend(aplicacion)

    @aplicacion.errorhandler(ErrorDominio)
    def error_dominio(error: ErrorDominio):
        contenido = {"error": error.mensaje}
        if error.detalles is not None:
            contenido["detalles"] = error.detalles
        return jsonify(contenido), error.estado_http

    @aplicacion.errorhandler(psycopg.errors.UniqueViolation)
    def error_unico(_error):
        return jsonify({"error": "El registro ya existe."}), 409

    @aplicacion.errorhandler(psycopg.errors.ForeignKeyViolation)
    def error_relacion(_error):
        return jsonify({"error": "El registro está relacionado con otros datos."}), 409

    @aplicacion.errorhandler(psycopg.errors.CheckViolation)
    def error_restriccion(_error):
        return jsonify({"error": "Los datos no cumplen las reglas del sistema."}), 400

    @aplicacion.errorhandler(HTTPException)
    def error_http(error: HTTPException):
        """La API contesta siempre en JSON, incluso al fallar la ruta.

        Sin esto, una ruta inexistente bajo /api devolvía la página HTML por
        defecto de Flask y el cliente reventaba al interpretarla como JSON.
        """
        if request.path.startswith("/api/"):
            return jsonify({"error": error.description}), error.code
        return error

    return aplicacion


def _registrar_frontend(aplicacion: Flask) -> None:
    """Sirve el frontend compilado desde el mismo origen que la API.

    Sólo se activa si existe frontend/dist, es decir en un despliegue de un
    único servicio. En desarrollo el frontend lo sirve Vite con su proxy.
    """
    if not FRONTEND.is_dir():
        return

    @aplicacion.get("/", defaults={"ruta": ""})
    @aplicacion.get("/<path:ruta>")
    def frontend(ruta: str):
        # Las rutas de API desconocidas deben responder 404 en JSON y no la
        # portada de la aplicación.
        if ruta.startswith("api/"):
            raise NotFound

        # safe_join descarta cualquier intento de salir del directorio.
        destino = safe_join(str(FRONTEND), ruta) if ruta else None
        if destino and Path(destino).is_file():
            return send_from_directory(FRONTEND, ruta)

        # El resto son rutas del enrutador del cliente: va la portada.
        return send_from_directory(FRONTEND, "index.html")


app = crear_aplicacion()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
