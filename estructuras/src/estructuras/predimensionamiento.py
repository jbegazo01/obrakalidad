"""Predimensionamiento con criterios prácticos usuales en el Perú (no son exigencias de norma).

Las dimensiones se confirman luego con el análisis y el diseño de cada elemento.
"""

import math
from dataclasses import dataclass

from .normas.e020 import PESO_ALIGERADO

ESPESORES_ALIGERADO = tuple(sorted(PESO_ALIGERADO))
ANCHO_MINIMO_VIGA = 0.25  # m, E.060 art. 21 para vigas con responsabilidad sísmica


def _redondear_arriba(valor: float, paso: float = 0.05) -> float:
    return round(math.ceil(valor / paso - 1e-9) * paso, 2)


def espesor_aligerado(luz: float) -> float:
    """h ≥ Ln/25, redondeado al espesor de aligerado tabulado inmediato superior."""
    requerido = luz / 25.0
    for h in ESPESORES_ALIGERADO:
        if h >= requerido - 1e-9:
            return h
    raise ValueError(f"Luz de {luz:g} m excede el rango del aligerado; use losa maciza o vigas intermedias.")


def espesor_maciza_dos_direcciones(perimetro: float) -> float:
    """h ≥ perímetro/180, redondeado a 0,05 m (mínimo 0,12 m)."""
    return max(_redondear_arriba(perimetro / 180.0), 0.12)


@dataclass
class SeccionViga:
    b: float
    h: float
    h_min: float  # Ln/12
    h_max: float  # Ln/10


# Áreas de barras corrugadas usuales (cm²).
BARRAS = {'3/8"': 0.71, '1/2"': 1.29, '5/8"': 1.99, '3/4"': 2.84, '1"': 5.10}


def cuatro_barras(as_requerido: float) -> str:
    """Menor diámetro con el que 4 barras cubren el área requerida (cm²)."""
    for diametro, area in BARRAS.items():
        if 4 * area >= as_requerido - 1e-9:
            return f"4 %%c {diametro}"  # %%c: símbolo de diámetro en AutoCAD
    raise ValueError(f"As = {as_requerido:.2f} cm² excede 4 barras de 1\".")


def seccion_viga(luz: float) -> SeccionViga:
    """Peralte entre Ln/12 y Ln/10; se adopta Ln/10 redondeado (mín. 0,30 m), b = 0,25 m."""
    h = max(_redondear_arriba(luz / 10.0), 0.30)
    return SeccionViga(b=ANCHO_MINIMO_VIGA, h=h, h_min=luz / 12.0, h_max=luz / 10.0)
