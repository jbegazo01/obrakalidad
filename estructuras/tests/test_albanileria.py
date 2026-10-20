import copy
from pathlib import Path

import numpy as np
import pytest
import yaml

from estructuras import albanileria, cimentacion
from estructuras.cli import main
from estructuras.metrado import OpcionesMetrado, _cargas_losa_por_m2, metrar
from estructuras.modelo import rigidez_voladizo
from estructuras.muros import MuroAnalisis, unir_muros
from estructuras.normas.e070 import Muro
from estructuras.proyecto import ficha_desde_dict, leer_ficha

PROPUESTA = Path(__file__).parent.parent / "ejemplos" / "propuesta_vivienda_8x20.yaml"


@pytest.fixture(scope="module")
def ficha():
    return leer_ficha(PROPUESTA)


@pytest.fixture(scope="module")
def resultado(ficha):
    return albanileria.analizar(ficha)


def test_metrado_conserva_las_cargas(ficha):
    """Toda la carga de losas, vigas, columnas y escalera llega a algún muro o columna."""
    m = metrar(ficha)
    op = OpcionesMetrado.desde_ficha(ficha)
    geo = ficha.geometria
    assert m.advertencias == []
    for i, nivel in enumerate(ficha.niveles):
        asignado = sum(m.total_pano(p, i).D for p in m.panos) + sum(c[i].D for c in m.columnas.values())
        esperado = sum(
            _cargas_losa_por_m2(l, nivel.azotea, op).D * abs(l.fin[0] - l.inicio[0]) * abs(l.fin[1] - l.inicio[1])
            for l in geo.losas
        )
        esperado += sum(v.b * (v.h - 0.17) * 2.4 * v.luz for v in geo.vigas)
        esperado += sum(c.dx * c.dy * (nivel.altura_entrepiso - 0.17) * 2.4 for c in geo.columnas)
        esperado += sum(h.carga_muerta * h.area for h in geo.huecos)
        assert asignado == pytest.approx(esperado, rel=1e-6)


def test_union_de_panos(ficha):
    muros = {w.id: w for w in unir_muros(ficha.muros, ficha.geometria)}
    assert muros["MY-A"].L == 16.0
    assert muros["MY-A"].Nc == 5
    assert muros["MY-A"].Lm == 8.0  # paño mayor 4 m < 0,5 L
    assert muros["MX-5"].Nc == 3
    assert muros["PL-1"].material == "concreto"


def test_voladizo_timoshenko():
    E, t, L = 325000.0, 0.13, 4.0
    G = 0.4 * E
    K = rigidez_voladizo(E, G, t * L**3 / 12, t * L / 1.2, [2.6, 2.6, 2.6])
    H = 7.8
    teorico = H**3 / (3 * E * t * L**3 / 12) + 1.2 * H / (G * t * L)
    assert np.linalg.inv(K)[2, 2] == pytest.approx(teorico, rel=1e-9)


def test_equilibrio_del_modelo(resultado):
    m = resultado.modelo
    for caso, direccion in (("Sx", "x"), ("Sy", "y")):
        suma = sum(m.respuestas[w.id].V[caso][0] for w in resultado.muros if w.direccion == direccion)
        assert suma == pytest.approx(resultado.sismo.V, rel=1e-9)


def test_tabla_11_calculo_manual():
    """Muro de un paño L = 4 m, t = 0,13 m; Vm1 = 20 t, Mu1 = 60 t·m, h = 2,6 m, Pc = 10 t."""
    w = MuroAnalisis("M", "x", "albanileria", 0.13, 0.0, 0.0, 4.0,
                     [Muro("M", "x", 4.0, 0.13, inicio=(0, 0), fin=(4, 0))], [0.0, 4.0])
    op = albanileria.OpcionesDiseno()
    ext = albanileria.disenar_columna(w, 0.0, True, True, 1, 20.0, 60.0, 2.6, 10.0, 0.8, 210, 4200, op)
    # M = 60 − 0,5·20·2,6 = 34; F = 8,5; Vc = 1,5·20·4/(4·3) = 10; T = −1,5; C = 18,5
    assert ext.Vc == pytest.approx(10.0)
    assert ext.T == pytest.approx(-1.5)
    assert ext.C == pytest.approx(18.5)
    assert ext.As_req == pytest.approx(10000 / (4200 * 0.8 * 0.85))  # solo corte-fricción
    assert ext.d == 25
    assert ext.barras == '4 %%c 3/8" + 2 %%c 8 mm'
    inte = albanileria.disenar_columna(w, 2.0, False, True, 1, 20.0, 60.0, 2.6, 10.0, 0.8, 210, 4200, op)
    assert inte.Vc == pytest.approx(20 * 4 / (4 * 3))
    assert inte.T == pytest.approx(20 * 2.6 / 4 - 10)
    assert inte.C == pytest.approx(10 - 0.5 * 20 * 2.6 / 4)


def test_solera():
    w = MuroAnalisis("M", "x", "albanileria", 0.13, 0.0, 0.0, 8.0,
                     [Muro("a", "x", 4.0, 0.13, inicio=(0, 0), fin=(4, 0)),
                      Muro("b", "x", 4.0, 0.13, inicio=(4, 0), fin=(8, 0))], [0.0, 4.0, 8.0])
    s = albanileria.disenar_solera(w, 1, 40.0, 0.17, 210, 4200)
    assert s.Ts == pytest.approx(40 * 4 / (2 * 8))  # Lm = max(4, 0,5·8) = 4


def test_propuesta_cumple(resultado):
    assert resultado.cumple, resultado.observaciones
    assert all(g.cumple for g in resultado.globales)
    assert all(v.ok_axial and v.ok_fisuracion for v in resultado.verificaciones)
    assert max(resultado.derivas["X"].max(), resultado.derivas["Y"].max()) <= 0.005
    # Primer piso siempre se diseña como agrietado; factor de amplificación entre 2 y 3.
    assert all(v.agrietado for v in resultado.verificaciones if v.piso == 1)
    assert all(2.0 <= v.factor <= 3.0 for v in resultado.verificaciones)


def test_detecta_fisuracion():
    datos = yaml.safe_load(PROPUESTA.read_text(encoding="utf-8"))
    datos = copy.deepcopy(datos)
    for m in datos["muros"]:
        if m["id"] == "PL-2":  # placa de fachada reemplazada por un muro corto de albañilería
            m["material"] = "albanileria"
            m["espesor_m"] = 0.13
    r = albanileria.analizar(ficha_desde_dict(datos))
    assert not r.cumple
    assert any("fisuración" in o for o in r.observaciones)


def test_cimentacion(resultado):
    c = cimentacion.disenar(resultado)
    assert c.cumple
    my_a = next(x for x in c.cimientos if x.elemento == "MY-A")
    assert my_a.excentrico
    assert my_a.centro[0] - my_a.ancho / 2 == pytest.approx(-0.065)  # cara exterior a ras del muro
    assert all(v.q_min >= 0 for v in c.sismo)


def test_cli_analizar(tmp_path):
    assert main(["analizar", str(PROPUESTA), "-o", str(tmp_path)]) == 0
    for nombre in ("memoria_de_calculo.docx", "E-01.dxf", "E-02.dxf"):
        assert (tmp_path / nombre).exists()
