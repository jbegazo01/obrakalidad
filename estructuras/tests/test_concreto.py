import math
from pathlib import Path

import pytest

from estructuras import albanileria, cimentacion, concreto
from estructuras.metrado import metrar
from estructuras.normas import e060
from estructuras.proyecto import leer_ficha
from estructuras.vigas_continuas import Tramo, envolvente, resolver

PROPUESTA = Path(__file__).parent.parent / "ejemplos" / "propuesta_vivienda_8x20.yaml"


@pytest.fixture(scope="module")
def ficha():
    return leer_ficha(PROPUESTA)


@pytest.fixture(scope="module")
def res(ficha):
    return albanileria.analizar(ficha)


# ---------------------------------------------------------------- E.060

def test_constantes_e060():
    assert e060.vc_viga(1, 1, 210) / math.sqrt(210) == pytest.approx(0.543, abs=1e-3)  # ≈ 0,53 √f'c
    assert e060.as_minima_rectangular(100, 100, 210, 4200) / 1e4 == pytest.approx(0.00242, abs=1e-5)
    assert e060.as_balanceada(100, 100, 210, 4200) / 1e4 == pytest.approx(0.02125)
    assert e060.beta1(210) == 0.85
    assert e060.beta1(350) == pytest.approx(0.85 - 0.2 * (350 / e060.MPA - 28) / 28)


def test_flexion_ida_y_vuelta():
    As = e060.as_flexion(12e5, 25, 34, 210, 4200)
    assert e060.momento_resistente(As, 25, 34, 210, 4200) == pytest.approx(12e5)
    with pytest.raises(ValueError):
        e060.as_flexion(60e5, 25, 34, 210, 4200)


def test_vigueta_17():
    s = e060.SeccionT(40, 5, 10, 17)
    assert s.inercia == pytest.approx(7275, abs=5)
    assert e060.as_minima_t(s, 14, 210, 4200, positivo=False) == pytest.approx(0.90, abs=0.02)
    assert e060.as_minima_t(s, 14, 210, 4200, positivo=True) == pytest.approx(0.42, abs=0.02)


def test_anclajes():
    # ld = fy/(2,6 √f'c) db en MPa para barras ≤ 3/4"
    ld = (4200 / e060.MPA) / (2.6 * math.sqrt(210 / e060.MPA)) * 1.27
    assert e060.longitud_desarrollo('1/2"', 210, 4200) == pytest.approx(ld)
    assert e060.longitud_gancho('5/8"', 210, 4200) == pytest.approx(0.24 * (4200 / e060.MPA) / math.sqrt(210 / e060.MPA) * 1.588)


# ---------------------------------------------------------------- vigas continuas

def test_viga_continua_casos_de_libro():
    m = resolver([Tramo(4, 1), Tramo(4, 1)], [(1, 0), (1, 0)])
    assert m[0][1] == pytest.approx(2.0)  # wL²/8 en el apoyo central
    assert resolver([Tramo(6, 1)], [(1, 0)], (True, True))[0][0] == pytest.approx(-3.0)
    env = envolvente([Tramo(5, 0, 1)] * 3, 0, 1)
    assert env.tramos_pos[0] / 25 == pytest.approx(0.1013, abs=1e-4)
    assert min(env.apoyos_neg) / 25 == pytest.approx(-0.1167, abs=1e-4)


# ---------------------------------------------------------------- elementos de la propuesta

def test_aligerados(ficha):
    tiras = concreto.disenar_aligerados(ficha)
    assert len(tiras) == 4
    tipica = tiras[0]
    central = tipica.apoyos[1]
    assert central.Mu == pytest.approx(0.81, abs=0.01)  # ≈ 0,1 wu L² con alternancia
    assert central.armado == '1 %%c 3/8" + 1 %%c 1/2"'
    assert central.largo_izq >= 4.0 / 3 - 0.2  # del orden de ln/3
    assert all(t.Vu <= t.phi_Vc for t in tipica.tramos)


def test_vigas(ficha):
    vigas = {v.id: v for v in concreto.disenar_vigas(ficha, metrar(ficha))}
    assert "V-101/V-102" in vigas  # continuas sobre la columna C-2
    v105 = vigas["V-105"]
    As_pos = v105.tramos[0].As_req
    assert e060.momento_resistente(As_pos, 25, 34, 210, 4200) / 1e5 == pytest.approx(v105.tramos[0].Mu)
    assert v105.Vu >= max(v105.tramos[0].Mu, 0)  # incluye el cortante por capacidad
    assert all(not v.observaciones for v in vigas.values())


def test_escalera(ficha):
    e = concreto.disenar_escalera(ficha)
    assert e.contrapasos == 16
    assert 0.60 <= 2 * e.contrapaso + e.paso <= 0.64
    assert e.observaciones == []


def test_placas_cumplen(res, ficha):
    for p in concreto.disenar_placas(res, ficha):
        assert not p.observaciones
        assert all(M <= cap for _, _, M, cap in p.combinaciones)
        assert p.Vu <= p.phi_Vn


def test_diagrama_mano():
    """Placa 200 × 15 cm, núcleos 4 Ø 1/2" a 12,5 cm de cada borde, sin acero de alma:
    a Pu = 0, φMn ≈ 0,9·As·fy·(d − a/2)."""
    As = 4 * 1.29
    diag = concreto.diagrama_interaccion(200, 15, [(12.5, As), (187.5, As)], 210, 4200)
    a = As * 4200 / (0.85 * 210 * 15)
    esperado = 0.9 * As * 4200 * (187.5 - a / 2) / 1e5
    assert concreto.momento_capacidad(diag, 0.0) == pytest.approx(esperado, rel=0.03)


def test_cimiento_combinado(res, ficha):
    cim = cimentacion.disenar(res)
    assert cim.cumple, cim.observaciones
    zc = next(c for c in cim.cimientos if c.tipo == "combinado")
    assert set(zc.componentes) == {"PL-1", "PL-2", "C-2"}
    zapatas = concreto.disenar_zapatas(res, cim, ficha)
    assert zapatas[0].h >= 0.60
    assert zapatas[0].Vu_corte <= zapatas[0].phi_Vc_corte
