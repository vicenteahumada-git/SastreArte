from dataclasses import dataclass
from typing import Any


@dataclass
class ErrorDominio(Exception):
    mensaje: str
    estado_http: int = 400
    detalles: Any | None = None

    def __str__(self) -> str:
        return self.mensaje

