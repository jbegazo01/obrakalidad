from pathlib import Path

import ezdxf
import pytest

from estructuras import analisis
from estructuras.cli import main
from estructuras.geometria import columnas_confinamiento, resolver_punto
from estructuras.normas import e070
from estructuras.planos import plano_estructuracion
from estructuras.predimensionamiento import cuatro_barras, espesor_aligerado, seccion_viga
from estructuras.proyecto import FichaInvalida, ficha_desde_dict, leer_ficha, validar

PROPUESTA = Path(__file__).parent.parent / "ejemplos" / "propuesta_vivienda_8x20.yaml"
EJES_X = {"A": 0.0, "B": 4.0}
EJES_Y = {"1": 0.0, "2": 4.0}


def test_resolver_punto():
    assert resolver_punto(["B", 2], EJES_X, EJES_Y) == (4.0, 4.0)
    assert resolver_punto([1.5, "1"], EJES_X, EJES_Y) == (1.5, 0.0)
    assert resolver_punto([1.0, 2.0], EJES_X, EJES_Y) == (1.0, 2.0)  # floats son coordenadas
    with pytest.raises(ValueError, match="no definido"):
        resolver_punto(["Z", 1], EJES_X, EJES_Y)


def test_muro_por_coordenadas():
    datos = {
        "proyecto": {"nombre": "t", "categoria": "C"},
        "sitio": {"zona": 4, "perfil_suelo": "S1"},
        "estructura": {"sistema": "albanileria"},
        "materiales": {"unidad_albanileria": "kk_industrial"},
        "niveles": [{"altura_entrepiso_m": 2.6, "area_m2": 16, "carga_muerta_tonf_m2": 0.8, "carga_viva_tonf_m2": 0.2}],
        "geometria": {"ejes": {"x": EJES_X, "y": EJES_Y}},
        "muros": [{"id": "M1", "desde": ["A", 1], "hasta": ["A", 2], "espesor_m": 0.13}],
    }
    ficha = ficha_desde_dict(datos)
    assert ficha.muros[0].direccion == "y"
    assert ficha.muros[0].longitud == 4.0
    datos["muros"][0]["hasta"] = ["B", 2]
    with pytest.raises(FichaInvalida, match="paralelo"):
        ficha_desde_dict(datos)


def test_columnas_confinamiento_sin_duplicados():
    muros = [
        e070.Muro("M1", "y", 4.0, 0.13, inicio=(0, 0), fin=(0, 4)),
        e070.Muro("M2", "y", 4.0, 0.13, inicio=(0, 4), fin=(0, 8)),
        e070.Muro("M3", "x", 4.0, 0.13, inicio=(0, 8), fin=(4, 8)),
        e070.Muro("P1", "x", 1.5, 0.15, "concreto", inicio=(0, 0), fin=(1.5, 0)),
    ]
    cols = columnas_confinamiento(muros)
    # 3 nodos en Y (0, 4, 8) + 2 nodos en X (esquina y extremo); la placa no lleva C-1.
    assert len(cols) == 5


def test_predimensionamiento():
    assert espesor_aligerado(4.0) == 0.17
    assert espesor_aligerado(4.8) == 0.20
    assert espesor_aligerado(6.0) == 0.25
    sv = seccion_viga(4.0)
    assert (sv.b, sv.h) == (0.25, 0.40)
    assert seccion_viga(2.0).h == 0.30
    assert cuatro_barras(e070.acero_minimo_columna(210, 13 * 25, 4200)) == '4 %%c 3/8"'
    assert cuatro_barras(e070.acero_minimo_columna(210, 23 * 25, 4200)) == '4 %%c 1/2"'


def test_propuesta_cumple():
    ficha = leer_ficha(PROPUESTA)
    errores, advertencias = validar(ficha)
    assert errores == []
    assert not any("art. 20" in a for a in advertencias)
    d = analisis.verificar_densidad(ficha)
    assert all(x.cumple for x in d.direcciones)


def test_plano_dxf(tmp_path):
    ficha = leer_ficha(PROPUESTA)
    plano = plano_estructuracion(ficha, analisis.analisis_estatico(ficha))
    ruta = tmp_path / "E-01.dxf"
    plano.guardar(ruta)
    doc = ezdxf.readfile(ruta)
    capas = {layer.dxf.name for layer in doc.layers}
    assert {"EST-EJES", "EST-MUROS", "EST-COLUMNAS", "EST-VIGAS"} <= capas
    msp = doc.modelspace()
    muros_albanileria = sum(1 for m in ficha.muros if m.material == "albanileria")
    assert len(msp.query('LWPOLYLINE[layer=="EST-MUROS"]')) == muros_albanileria + 1  # + leyenda
    textos = " ".join(t.dxf.text for t in msp.query("TEXT"))
    assert "V-104 (.25x.40)" in textos
    assert "E-01" in textos


def test_cli_plano_y_predim(tmp_path):
    assert main(["predim", str(PROPUESTA)]) == 0
    assert main(["plano", str(PROPUESTA), "-o", str(tmp_path / "E-01.dxf")]) == 0
    assert (tmp_path / "E-01.dxf").exists()
