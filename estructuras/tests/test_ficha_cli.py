from pathlib import Path

import pytest
import yaml

from estructuras import analisis
from estructuras.cli import main
from estructuras.proyecto import ficha_desde_dict, leer_ficha, validar

EJEMPLO = Path(__file__).parent.parent / "ejemplos" / "vivienda_albanileria.yaml"


def _datos():
    return yaml.safe_load(EJEMPLO.read_text(encoding="utf-8"))


def test_ejemplo_valido():
    ficha = leer_ficha(EJEMPLO)
    errores, _ = validar(ficha)
    assert errores == []
    assert ficha.n_pisos == 3
    assert ficha.altura_total == pytest.approx(7.8)


def test_analisis_estatico_ejemplo():
    r = analisis.analisis_estatico(leer_ficha(EJEMPLO))
    assert r.peso_total == pytest.approx(261.0)
    for d in r.direcciones:
        assert d.cortante.V == pytest.approx(107.6625)
        assert sum(d.fuerzas) == pytest.approx(d.cortante.V)
    assert r.estatico_aplicable


def test_densidad_ejemplo():
    r = analisis.verificar_densidad(leer_ficha(EJEMPLO))
    assert all(d.cumple for d in r.direcciones)
    assert r.muros_cortos == ["X6"]
    assert r.muros_delgados == []


def test_validacion_detecta_errores():
    datos = _datos()
    datos["proyecto"]["categoria"] = "B"
    datos["estructura"]["sistema"] = "ca_emdl"
    datos["estructura"]["irregularidades"] = ["torsional_extrema"]
    errores, _ = validar(ficha_desde_dict(datos))
    assert any("Tabla 9" in e for e in errores)
    assert any("Tabla 13" in e for e in errores)


def test_validacion_ts_en_zona_4():
    datos = _datos()
    datos["proyecto"]["categoria"] = "B"
    _, advertencias = validar(ficha_desde_dict(datos))
    assert any("H/V" in a for a in advertencias)


def test_cli(tmp_path, capsys):
    assert main(["sismo", str(EJEMPLO)]) == 0
    assert "107,66 tonf" in capsys.readouterr().out
    assert main(["densidad", str(EJEMPLO)]) == 0
    nueva = tmp_path / "ficha.yaml"
    assert main(["nuevo", str(nueva)]) == 0
    assert main(["validar", str(nueva)]) == 0
    assert main(["nuevo", str(nueva)]) == 1
