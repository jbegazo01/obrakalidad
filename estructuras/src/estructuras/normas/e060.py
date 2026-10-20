"""Norma Técnica E.060 Concreto Armado (D.S. N° 010-2009-VIVIENDA). Propiedades básicas."""

import math

FC_MIN_SISMICO = 210.0  # kgf/cm², cap. 21 (elementos con responsabilidad sísmica)
FY_GRADO_60 = 4200.0  # kgf/cm²
ES = 2.0e6  # kgf/cm², art. 8.5


def modulo_elasticidad(fc: float) -> float:
    """Art. 8.5, concreto de peso normal: Ec = 15 000 √f'c (kgf/cm²)."""
    return 15000.0 * math.sqrt(fc)
