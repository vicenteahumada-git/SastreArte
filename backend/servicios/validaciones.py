import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from configuracion.errores import ErrorDominio

PATRON_TELEFONO = re.compile(r"^[0-9+()\-\s]{6,30}$")


def texto_requerido(datos: dict, campo: str, maximo: int) -> str:
    valor = datos.get(campo)
    if not isinstance(valor, str) or not valor.strip():
        raise ErrorDominio(f"El campo '{campo}' es obligatorio.")
    valor = valor.strip()
    if len(valor) > maximo:
        raise ErrorDominio(f"El campo '{campo}' admite hasta {maximo} caracteres.")
    return valor


def texto_opcional(datos: dict, campo: str, maximo: int) -> str | None:
    valor = datos.get(campo)
    if valor is None or valor == "":
        return None
    if not isinstance(valor, str):
        raise ErrorDominio(f"El campo '{campo}' debe ser texto.")
    valor = valor.strip()
    if len(valor) > maximo:
        raise ErrorDominio(f"El campo '{campo}' admite hasta {maximo} caracteres.")
    return valor or None


def telefono(datos: dict, campo: str = "telefono", obligatorio: bool = True) -> str | None:
    valor = datos.get(campo)
    if not obligatorio and (valor is None or valor == ""):
        return None
    if not isinstance(valor, str) or not PATRON_TELEFONO.fullmatch(valor.strip()):
        raise ErrorDominio("El teléfono debe contener entre 6 y 30 caracteres válidos.")
    return valor.strip()


def entero(datos: dict, campo: str, minimo: int = 0, obligatorio: bool = True) -> int | None:
    """Valida un importe entero.

    Acepta enteros, cadenas numéricas y decimales sin parte fraccionaria
    (30000.0 vale, 1000.5 no), para no romper con clientes que serializan
    los montos como número de punto flotante.
    """
    valor = datos.get(campo)
    if not obligatorio and (valor is None or valor == ""):
        return None
    if valor is None or isinstance(valor, bool):
        raise ErrorDominio(f"El campo '{campo}' debe ser un número entero.")
    try:
        numero = Decimal(str(valor).strip())
    except (InvalidOperation, TypeError, ValueError):
        raise ErrorDominio(f"El campo '{campo}' debe ser un número entero.") from None
    if not numero.is_finite() or numero != numero.to_integral_value():
        raise ErrorDominio(f"El campo '{campo}' debe ser un número entero.")
    resultado = int(numero)
    if resultado < minimo:
        raise ErrorDominio(f"El campo '{campo}' debe ser mayor o igual a {minimo}.")
    return resultado


def opcion(
    datos: dict, campo: str, permitidos: set[str], obligatorio: bool = True
) -> str | None:
    """Valida que el valor pertenezca a un conjunto cerrado de opciones.

    Normaliza a mayúsculas y con guion bajo, de modo que 'en proceso' y
    'EN_PROCESO' no queden como dos estados distintos.
    """
    valor = datos.get(campo)
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        if obligatorio:
            raise ErrorDominio(f"El campo '{campo}' es obligatorio.")
        return None
    if not isinstance(valor, str):
        raise ErrorDominio(f"El campo '{campo}' debe ser texto.")
    normalizado = valor.strip().upper().replace(" ", "_").replace("-", "_")
    if normalizado not in permitidos:
        opciones = ", ".join(sorted(permitidos))
        raise ErrorDominio(f"El campo '{campo}' admite solo: {opciones}.")
    return normalizado


def decimal_numero(
    datos: dict, campo: str, minimo: Decimal = Decimal(0), obligatorio: bool = True
) -> Decimal | None:
    valor = datos.get(campo)
    if not obligatorio and (valor is None or valor == ""):
        return None
    if isinstance(valor, bool):
        raise ErrorDominio(f"El campo '{campo}' debe ser numérico.")
    try:
        numero = Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError):
        raise ErrorDominio(f"El campo '{campo}' debe ser numérico.") from None
    if not numero.is_finite() or numero < minimo:
        raise ErrorDominio(f"El campo '{campo}' debe ser mayor o igual a {minimo}.")
    return numero


def fecha_iso(datos: dict, campo: str, no_anterior_a: date | None = None) -> date:
    valor = datos.get(campo)
    if isinstance(valor, datetime):
        resultado = valor.date()
    elif isinstance(valor, date):
        resultado = valor
    elif isinstance(valor, str):
        try:
            resultado = date.fromisoformat(valor)
        except ValueError:
            raise ErrorDominio(
                f"El campo '{campo}' debe tener formato AAAA-MM-DD."
            ) from None
    else:
        raise ErrorDominio(f"El campo '{campo}' debe tener formato AAAA-MM-DD.")

    if no_anterior_a is not None and resultado < no_anterior_a:
        raise ErrorDominio(
            f"El campo '{campo}' no puede ser anterior a {no_anterior_a.isoformat()}."
        )
    return resultado


def diccionario_json(valor: Any) -> dict:
    if not isinstance(valor, dict):
        raise ErrorDominio("Se esperaba un objeto JSON.")
    return valor
