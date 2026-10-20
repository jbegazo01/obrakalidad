import pytest

from estructuras.cli import main
from estructuras.normas import zonificacion
from estructuras.proyecto import FichaInvalida, ficha_desde_dict


def test_totales_del_anexo():
    d = zonificacion.distritos()
    assert len(d) == 1892
    assert len({x.departamento for x in d}) == 25
    assert len({(x.departamento, x.provincia) for x in d}) == 196


@pytest.mark.parametrize(
    "distrito, provincia, zona",
    [("San Juan de Lurigancho", None, 4), ("SAN MIGUEL", "Lima", 4), ("Cusco", "Cusco", 2),
     ("Iquitos", None, 1), ("Arequipa", "Arequipa", 3), ("ica", "ica", 4)],
)
def test_zona_de(distrito, provincia, zona):
    assert zonificacion.zona_de(distrito, provincia) == zona


def test_ambiguo_y_desconocido():
    with pytest.raises(ValueError, match="ambiguo"):
        zonificacion.zona_de("Miraflores")
    with pytest.raises(ValueError, match="no figura"):
        zonificacion.zona_de("Atlantis")


def _datos(**sitio):
    return {
        "proyecto": {"nombre": "t", "categoria": "C",
                     "ubicacion": {"departamento": "Lima", "provincia": "Lima", "distrito": "Comas"}},
        "sitio": {"perfil_suelo": "S1", **sitio},
        "estructura": {"sistema": "albanileria"},
        "niveles": [{"altura_entrepiso_m": 2.6, "area_m2": 10, "carga_muerta_tonf_m2": 0.8, "carga_viva_tonf_m2": 0.2}],
    }


def test_ficha_toma_la_zona_del_distrito():
    assert ficha_desde_dict(_datos()).zona == 4
    with pytest.raises(FichaInvalida, match="no coincide"):
        ficha_desde_dict(_datos(zona=2))


def test_cli_zona(capsys):
    assert main(["zona", "Miraflores", "--provincia", "Lima"]) == 0
    assert "zona 4" in capsys.readouterr().out
