"""Conversiones de unidades. Sistema interno: tonf, m, s."""

G = 9.80665  # m/s²

KN_POR_TONF = G
KPA_POR_TONF_M2 = G


def kgf_cm2_a_tonf_m2(valor: float) -> float:
    return valor * 10.0


def tonf_m2_a_kgf_cm2(valor: float) -> float:
    return valor / 10.0


def kgf_m2_a_tonf_m2(valor: float) -> float:
    return valor / 1000.0


def mpa_a_kgf_cm2(valor: float) -> float:
    return valor * 1000.0 / G


def tonf_a_kn(valor: float) -> float:
    return valor * KN_POR_TONF
