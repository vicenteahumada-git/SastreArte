"""Fecha local del taller.

Los contenedores corren en UTC. Si se usara date.today() directamente, entre
las 20:00 y la medianoche de Chile el servidor ya estaría en el día siguiente
y rechazaría una entrega agendada para hoy.
"""

import os
from datetime import date, datetime
from zoneinfo import ZoneInfo

ZONA_POR_DEFECTO = "America/Santiago"


def zona() -> ZoneInfo:
    return ZoneInfo(os.getenv("ZONA_HORARIA", ZONA_POR_DEFECTO))


def hoy() -> date:
    """Fecha de hoy en la zona horaria del taller."""
    return datetime.now(tz=zona()).date()
