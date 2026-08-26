import os
from datetime import date, datetime, timedelta
from decimal import Decimal

import psycopg
from flask import Flask, jsonify
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS

from configuracion.errores import ErrorDominio


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

    return aplicacion


app = crear_aplicacion()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
