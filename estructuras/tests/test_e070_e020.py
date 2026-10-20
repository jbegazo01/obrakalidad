import pytest

from estructuras.normas import e020, e060, e070
from estructuras.normas.e070 import Muro


def test_densidad_requerida():
    assert e070.densidad_requerida(0.45, 1.0, 1.1, 3) == pytest.approx(0.026518, rel=1e-4)


def test_densidad_muros_transforma_concreto_y_excluye_cortos():
    muros = [
        Muro("X1", "x", 3.0, 0.13),
        Muro("X2", "x", 1.0, 0.13),  # L ≤ 1,2 m: no cuenta
        Muro("P1", "x", 1.5, 0.15, "concreto"),
        Muro("Y1", "y", 5.0, 0.23),
    ]
    d = e070.densidad_muros(muros, "x", 100.0, Ec_sobre_Em=6.0)
    assert d == pytest.approx((3.0 * 0.13 + 1.5 * 0.15 * 6.0) / 100.0)


def test_espesor_minimo():
    assert e070.espesor_minimo(2.4, 4) == pytest.approx(0.12)
    assert e070.espesor_minimo(2.5, 1) == pytest.approx(0.10)


def test_esfuerzo_axial_maximo():
    # f'm = 65 kgf/cm² = 650 tonf/m², h = 2,4 m, t = 0,13 m
    esperado = 0.2 * 650 * (1 - (2.4 / (35 * 0.13)) ** 2)
    assert e070.esfuerzo_axial_maximo(65, 2.4, 0.13) == pytest.approx(esperado)
    # muro grueso y corto: gobierna 0,15 f'm
    assert e070.esfuerzo_axial_maximo(65, 1.0, 0.25) == pytest.approx(0.15 * 650)


def test_resistencia_corte():
    # v'm = 8,1 kgf/cm² = 81 tonf/m²; α = 1; t = 0,13; L = 4; Pg = 20 tonf
    assert e070.resistencia_corte(8.1, 1.0, 0.13, 4.0, 20.0) == pytest.approx(0.5 * 81 * 0.13 * 4 + 4.6)
    assert e070.factor_esbeltez(10, 100, 2) == pytest.approx(1 / 3)
    assert e070.factor_esbeltez(10, 10, 2) == 1.0
    assert e070.control_fisuracion(5.5, 10.0)
    assert not e070.control_fisuracion(5.6, 10.0)


def test_modulos():
    assert e070.modulo_elasticidad(65) == 32500
    assert e070.modulo_corte(32500) == 13000
    assert e060.modulo_elasticidad(210) == pytest.approx(217370.65, rel=1e-6)


def test_e020():
    assert e020.carga_viva("vivienda") == 0.20
    assert e020.peso_aligerado(0.20) == 0.30
    with pytest.raises(ValueError):
        e020.peso_aligerado(0.22)
