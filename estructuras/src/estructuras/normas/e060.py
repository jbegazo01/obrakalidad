"""Norma Técnica E.060 Concreto Armado (D.S. N° 010-2009-VIVIENDA).

La norma da sus fórmulas en MPa y mm; aquí se trabaja en kgf, cm (resistencias en kgf/cm²)
convirtiendo √f'c a MPa de forma exacta. Momentos en kgf·cm salvo que se indique.
"""

import math
from dataclasses import dataclass

from ..unidades import G

FC_MIN_SISMICO = 210.0  # kgf/cm², cap. 21 (elementos con responsabilidad sísmica)
FY_GRADO_60 = 4200.0  # kgf/cm²
ES = 2.0e6  # kgf/cm², art. 8.5
MPA = 100.0 / G  # kgf/cm² por MPa (10,197)

# Diámetros (cm) y áreas (cm²) de barras corrugadas usuales en el Perú.
DIAMETROS = {"6 mm": 0.60, "8 mm": 0.80, '3/8"': 0.953, '1/2"': 1.27, '5/8"': 1.588, '3/4"': 1.905, '1"': 2.54}
AREAS = {"6 mm": 0.28, "8 mm": 0.50, '3/8"': 0.71, '1/2"': 1.29, '5/8"': 1.99, '3/4"': 2.84, '1"': 5.10}

# Factores de reducción de resistencia (art. 9.3.2).
PHI_FLEXION = 0.90
PHI_COMPRESION = 0.70
PHI_CORTE = 0.85


def modulo_elasticidad(fc: float) -> float:
    """Art. 8.5, concreto de peso normal: Ec = 15 000 √f'c (kgf/cm²)."""
    return 15000.0 * math.sqrt(fc)


def raiz_fc_mpa(fc: float) -> float:
    """√f'c en MPa a partir de f'c en kgf/cm²."""
    return math.sqrt(fc / MPA)


def beta1(fc: float) -> float:
    """Art. 10.2.7.3: 0,85 hasta 28 MPa; 0,65 desde 56 MPa; interpolación lineal entre ambos."""
    f = fc / MPA
    if f <= 28:
        return 0.85
    if f >= 56:
        return 0.65
    return 0.85 - 0.20 * (f - 28) / 28


# ------------------------------------------------------------------ flexión

def as_flexion(Mu: float, b: float, d: float, fc: float, fy: float, phi: float = PHI_FLEXION) -> float:
    """Acero de tracción (cm²) para Mu (kgf·cm) en sección rectangular b × d (cm), bloque de
    Whitney (art. 10.2.7). Lanza ValueError si la sección no alcanza."""
    if Mu <= 0:
        return 0.0
    k = 2 * Mu / (phi * 0.85 * fc * b)
    if k > d**2:
        raise ValueError("Sección insuficiente para el momento (aumentar peralte o ancho).")
    a = d - math.sqrt(d**2 - k)
    return 0.85 * fc * b * a / fy


def momento_resistente(As: float, b: float, d: float, fc: float, fy: float, phi: float = PHI_FLEXION) -> float:
    """φMn (kgf·cm) de una sección rectangular con acero en tracción As."""
    a = As * fy / (0.85 * fc * b)
    return phi * As * fy * (d - a / 2)


def as_balanceada(b: float, d: float, fc: float, fy: float) -> float:
    """Art. 10.3.2: acero de falla balanceada (εcu = 0,003)."""
    return 0.85 * beta1(fc) * fc / fy * 6000.0 / (6000.0 + fy) * b * d


def as_maxima(b: float, d: float, fc: float, fy: float) -> float:
    """Art. 10.3.4: As ≤ 0,75 Asb."""
    return 0.75 * as_balanceada(b, d, fc, fy)


def as_minima_rectangular(b: float, d: float, fc: float, fy: float) -> float:
    """Art. 10.5.2: As mín = 0,22 √f'c / fy · bw · d (MPa)."""
    return 0.22 * raiz_fc_mpa(fc) / (fy / MPA) * b * d


@dataclass
class SeccionT:
    """Sección T (vigueta de aligerado): ala b × hf, alma bw, peralte total h (cm)."""
    b: float
    hf: float
    bw: float
    h: float

    @property
    def area(self) -> float:
        return self.b * self.hf + self.bw * (self.h - self.hf)

    @property
    def y_inferior(self) -> float:
        """Centroide medido desde la fibra inferior."""
        a1, y1 = self.b * self.hf, self.h - self.hf / 2
        a2, y2 = self.bw * (self.h - self.hf), (self.h - self.hf) / 2
        return (a1 * y1 + a2 * y2) / (a1 + a2)

    @property
    def inercia(self) -> float:
        yc = self.y_inferior
        hw = self.h - self.hf
        return (self.b * self.hf**3 / 12 + self.b * self.hf * (self.h - self.hf / 2 - yc) ** 2
                + self.bw * hw**3 / 12 + self.bw * hw * (hw / 2 - yc) ** 2)


def momento_agrietamiento(seccion: SeccionT, fc: float, positivo: bool) -> float:
    """Art. 10.5.1: Mcr = fr·Ig / yt, fr = 0,62 √f'c (kgf·cm)."""
    fr = 0.62 * raiz_fc_mpa(fc) * MPA
    yt = seccion.y_inferior if positivo else seccion.h - seccion.y_inferior
    return fr * seccion.inercia / yt


def as_minima_t(seccion: SeccionT, d: float, fc: float, fy: float, positivo: bool) -> float:
    """Acero mínimo de una sección T: φMn ≥ 1,2 Mcr (10.5.1). Con el ala en compresión
    (momento positivo) tampoco menor que 10.5.2 con el ancho del alma."""
    b = seccion.b if positivo else seccion.bw
    As = as_flexion(1.2 * momento_agrietamiento(seccion, fc, positivo), b, d, fc, fy)
    if positivo:
        As = max(As, as_minima_rectangular(seccion.bw, d, fc, fy))
    return As


# ------------------------------------------------------------------ corte

def vc_viga(bw: float, d: float, fc: float) -> float:
    """Art. 11.3.1.1: Vc = 0,17 √f'c bw d (kgf)."""
    return 0.17 * raiz_fc_mpa(fc) * MPA * bw * d


def vs_maximo(bw: float, d: float, fc: float) -> float:
    """Art. 11.5.7.9: Vs ≤ 0,66 √f'c bw d."""
    return 0.66 * raiz_fc_mpa(fc) * MPA * bw * d


def separacion_estribos(Vu: float, bw: float, d: float, fc: float, fy: float, Av: float) -> float:
    """Separación (cm) de estribos por resistencia y por 11.5.5 y 11.5.6."""
    Vc = vc_viga(bw, d, fc)
    Vs = max(Vu / PHI_CORTE - Vc, 0.0)
    if Vs > vs_maximo(bw, d, fc):
        raise ValueError("Vs excede 0,66 √f'c bw d: aumentar la sección (11.5.7.9).")
    s_max = min(d / 2, 60.0)
    if Vs > 0.33 * raiz_fc_mpa(fc) * MPA * bw * d:
        s_max /= 2  # 11.5.5.3
    s_res = Av * fy * d / Vs if Vs > 0 else float("inf")
    # Av mín = 0,062 √f'c bw s / fy ≥ 0,35 bw s / fy (11.5.6.2)
    coef = max(0.062 * raiz_fc_mpa(fc), 0.35) * MPA
    s_min = Av * fy / (coef * bw)
    return min(s_res, s_max, s_min)


def vc_muro(Acw: float, hm: float, lm: float, fc: float) -> float:
    """Art. 11.10.5: Vc = αc √f'c Acw, αc = 0,25 (hm/lm ≤ 1,5) a 0,17 (hm/lm ≥ 2)."""
    r = hm / lm
    if r <= 1.5:
        ac = 0.25
    elif r >= 2.0:
        ac = 0.17
    else:
        ac = 0.25 - 0.08 * (r - 1.5) / 0.5
    return ac * raiz_fc_mpa(fc) * MPA * Acw


def vn_max_muro(Acw: float, fc: float) -> float:
    """Art. 11.10.4: Vn ≤ 0,83 √f'c Acw."""
    return 0.83 * raiz_fc_mpa(fc) * MPA * Acw


def vc_punzonamiento(bo: float, d: float, fc: float, beta: float, alfa_s: float) -> float:
    """Art. 11.12.2.1: menor de (a), (b) y (c) en kgf (bo, d en cm)."""
    r = raiz_fc_mpa(fc) * MPA
    a = 0.17 * (1 + 2 / beta) * r * bo * d
    b = 0.083 * (alfa_s * d / bo + 2) * r * bo * d
    c = 0.33 * r * bo * d
    return min(a, b, c)


# ------------------------------------------------------------------ anclajes

def longitud_desarrollo(barra: str, fc: float, fy: float, superior: bool = False) -> float:
    """Art. 12.2.2, Tabla 12.1 (espaciamiento y recubrimiento normales), cm, ≥ 30 cm."""
    db = DIAMETROS[barra]
    psi_t = 1.3 if superior else 1.0
    divisor = 2.6 if db <= DIAMETROS['3/4"'] else 2.1
    ld = (fy / MPA) * psi_t / (divisor * raiz_fc_mpa(fc)) * db
    return max(ld, 30.0)


def longitud_gancho(barra: str, fc: float, fy: float) -> float:
    """Art. 12.5.2: ldg = 0,24 fy / √f'c · db (cm), ≥ max(8 db, 15 cm)."""
    db = DIAMETROS[barra]
    return max(0.24 * (fy / MPA) / raiz_fc_mpa(fc) * db, 8 * db, 15.0)


def empalme_traslape(barra: str, fc: float, fy: float, superior: bool = False) -> float:
    """Art. 12.15.1: empalme clase B = 1,3 ld (cm), ≥ 30 cm."""
    return max(1.3 * longitud_desarrollo(barra, fc, fy, superior), 30.0)
