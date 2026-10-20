"""Zona sísmica por distrito, E.030 Anexo II (R.M. N° 183-2026-VIVIENDA).

Los datos se extraen del PDF oficial con herramientas/extraer_zonificacion.py.
"""

import csv
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources


@dataclass(frozen=True)
class Distrito:
    departamento: str
    provincia: str
    distrito: str
    zona: int


def normalizar(texto: str) -> str:
    """Mayúsculas sin tildes ni espacios repetidos (la Ñ se conserva)."""
    texto = " ".join(texto.upper().split())
    descompuesto = unicodedata.normalize("NFD", texto.replace("Ñ", "\0"))
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn").replace("\0", "Ñ")


@lru_cache(maxsize=1)
def distritos() -> tuple[Distrito, ...]:
    archivo = resources.files("estructuras") / "datos" / "zonificacion_e030_2026.csv"
    with archivo.open(encoding="utf-8") as f:
        return tuple(
            Distrito(r["departamento"], r["provincia"], r["distrito"], int(r["zona"])) for r in csv.DictReader(f)
        )


def buscar(distrito: str, provincia: str | None = None, departamento: str | None = None) -> list[Distrito]:
    """Distritos que coinciden; provincia y departamento sirven para desambiguar."""
    d = normalizar(distrito)
    p = normalizar(provincia) if provincia else None
    dep = normalizar(departamento) if departamento else None
    return [
        x for x in distritos()
        if normalizar(x.distrito) == d
        and (p is None or normalizar(x.provincia) == p)
        and (dep is None or normalizar(x.departamento) == dep)
    ]


def zona_de(distrito: str, provincia: str | None = None, departamento: str | None = None) -> int:
    encontrados = buscar(distrito, provincia, departamento)
    if not encontrados:
        raise ValueError(f"Distrito {distrito!r} no figura en el Anexo II de la E.030.")
    zonas = {x.zona for x in encontrados}
    if len(zonas) > 1:
        opciones = "; ".join(f"{x.distrito} ({x.provincia}, {x.departamento}): zona {x.zona}" for x in encontrados)
        raise ValueError(f"Distrito {distrito!r} ambiguo, indique provincia y departamento: {opciones}.")
    return zonas.pop()
