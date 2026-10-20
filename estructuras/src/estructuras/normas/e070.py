"""Norma Técnica E.070 Albañilería (D.S. N° 011-2006-VIVIENDA).

Unidades: tonf, m. Resistencias en kgf/cm² (se convierten a tonf/m² multiplicando por 10).
"""

from dataclasses import dataclass

from ..unidades import kgf_cm2_a_tonf_m2


@dataclass(frozen=True)
class UnidadAlbanileria:
    clave: str
    nombre: str
    fb: float  # resistencia de la unidad, kgf/cm²
    fm: float  # resistencia de pilas, kgf/cm²
    vm: float  # resistencia de muretes, kgf/cm²


# Tabla 9: resistencias características de la albañilería (unidades de arcilla).
UNIDADES = {
    u.clave: u
    for u in (
        UnidadAlbanileria("kk_artesanal", "King Kong artesanal (arcilla)", 55, 35, 5.1),
        UnidadAlbanileria("kk_industrial", "King Kong industrial (arcilla)", 145, 65, 8.1),
        UnidadAlbanileria("rejilla_industrial", "Rejilla industrial (arcilla)", 215, 85, 9.2),
    )
}

LONGITUD_MINIMA_MURO = 1.20  # m, solo muros con L > 1,2 m aportan a la densidad (art. 19.2 b)


def unidad(clave: str) -> UnidadAlbanileria:
    try:
        return UNIDADES[clave]
    except KeyError:
        raise ValueError(f"Unidad {clave!r} no existe; use una de {', '.join(UNIDADES)}.") from None


def modulo_elasticidad(fm: float) -> float:
    """Art. 24.7: Em = 500 f'm para unidades de arcilla (kgf/cm²)."""
    return 500.0 * fm


def modulo_corte(Em: float) -> float:
    """Art. 24.7: Gm = 0,4 Em."""
    return 0.4 * Em


def espesor_minimo(h: float, zona: int) -> float:
    """Art. 19.1 a): t ≥ h/20 en zonas sísmicas 2 a 4, t ≥ h/25 en zona 1."""
    return h / 20.0 if zona >= 2 else h / 25.0


def densidad_requerida(Z: float, U: float, S: float, N: int) -> float:
    """Art. 19.2 b): Σ L·t / Ap ≥ Z·U·S·N / 56."""
    return Z * U * S * N / 56.0


@dataclass(frozen=True)
class Muro:
    id: str
    direccion: str  # "x" o "y"
    longitud: float  # m, incluye columnas de confinamiento
    espesor: float  # m, espesor efectivo
    material: str = "albanileria"  # o "concreto"


def densidad_muros(muros: list[Muro], direccion: str, area_planta: float, Ec_sobre_Em: float) -> float:
    """Σ L·t / Ap en una dirección. Los muros de concreto se transforman con Ec/Em."""
    total = 0.0
    for m in muros:
        if m.direccion != direccion or m.longitud <= LONGITUD_MINIMA_MURO:
            continue
        t = m.espesor * Ec_sobre_Em if m.material == "concreto" else m.espesor
        total += m.longitud * t
    return total / area_planta


def esfuerzo_axial_maximo(fm: float, h: float, t: float) -> float:
    """Art. 19.1 b): σm ≤ 0,2 f'm [1 − (h/35t)²] ≤ 0,15 f'm. Devuelve tonf/m²."""
    fm_t = kgf_cm2_a_tonf_m2(fm)
    return min(0.2 * fm_t * (1.0 - (h / (35.0 * t)) ** 2), 0.15 * fm_t)


def factor_esbeltez(Ve: float, Me: float, L: float) -> float:
    """Art. 26.3: α = Ve·L/Me, con 1/3 ≤ α ≤ 1."""
    if Me == 0:
        return 1.0
    return min(max(Ve * L / Me, 1.0 / 3.0), 1.0)


def resistencia_corte(vm: float, alfa: float, t: float, L: float, Pg: float) -> float:
    """Art. 26.3, unidades de arcilla: Vm = 0,5 v'm·α·t·L + 0,23 Pg (tonf)."""
    return 0.5 * kgf_cm2_a_tonf_m2(vm) * alfa * t * L + 0.23 * Pg


def control_fisuracion(Ve: float, Vm: float) -> bool:
    """Art. 26.2: Ve ≤ 0,55 Vm ante el sismo moderado."""
    return Ve <= 0.55 * Vm
