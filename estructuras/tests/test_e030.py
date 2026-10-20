import pytest

from estructuras.normas import e030


def test_factor_zona():
    assert e030.FACTOR_ZONA == {4: 0.45, 3: 0.35, 2: 0.25, 1: 0.10}


@pytest.mark.parametrize(
    "zona, perfil, S, TP, TL",
    [
        (4, "S0", 0.80, 0.3, 3.0),
        (4, "S1", 1.00, 0.4, 2.5),
        (4, "S2", 1.10, 0.6, 2.0),  # sin Vs30: borde flexible del intervalo
        (4, "S3", 1.20, 0.9, 1.6),
        (3, "S4", 1.30, 1.2, 1.6),
        (2, "S4", 1.70, 1.2, 1.6),
        (1, "S4", 2.40, 1.2, 1.6),
        (1, "S3", 1.60, 0.9, 1.6),
    ],
)
def test_parametros_sitio_sin_vs30(zona, perfil, S, TP, TL):
    p = e030.parametros_sitio(zona, perfil)
    assert p.S == pytest.approx(S)
    assert p.TP == pytest.approx(TP)
    assert p.TL == pytest.approx(TL)


def test_interpolacion_vs30():
    # S2 en zona 4 con Vs30 = 450 m/s: punto medio de 350–550.
    p = e030.parametros_sitio(4, "S2", vs30=450)
    assert p.S == pytest.approx(1.05)
    assert p.TP == pytest.approx(0.5)
    assert p.TL == pytest.approx(2.25)
    assert not p.advertencias
    # En el borde rígido se recuperan los valores de S1.
    p = e030.parametros_sitio(4, "S2", vs30=549.999)
    assert p.S == pytest.approx(1.00, abs=1e-4)
    assert p.TP == pytest.approx(0.4, abs=1e-4)


def test_continuidad_entre_s2_y_s3():
    s2 = e030.parametros_sitio(3, "S2", vs30=350)
    s3 = e030.parametros_sitio(3, "S3", vs30=349.999)
    assert s2.S == pytest.approx(s3.S, abs=1e-4)
    assert s2.TP == pytest.approx(s3.TP, abs=1e-4)


def test_vs30_incoherente_con_perfil():
    with pytest.raises(ValueError, match="Tabla 3"):
        e030.parametros_sitio(4, "S2", vs30=600)


def test_suelos_que_requieren_estudio():
    with pytest.raises(ValueError, match="S5"):
        e030.parametros_sitio(4, "S5")
    with pytest.raises(ValueError, match="respuesta de sitio"):
        e030.parametros_sitio(4, "S4")


def test_perfil_por_vs30():
    assert e030.perfil_por_vs30(900) == "S0"
    assert e030.perfil_por_vs30(550) == "S1"
    assert e030.perfil_por_vs30(400) == "S2"
    assert e030.perfil_por_vs30(199) == "S4"


def test_verificar_ts():
    assert e030.verificar_ts("C", 4, "S2", 0.6, None) == []
    assert "H/V" in e030.verificar_ts("B", 4, "S2", 0.6, None)[0]
    assert e030.verificar_ts("A2", 4, "S2", 0.6, 0.35) == []
    assert "14.8" in e030.verificar_ts("A2", 4, "S2", 0.6, 0.40)[0]


def test_factor_C_ramas():
    TP, TL = 0.6, 2.0
    assert e030.factor_C(0.0, TP, TL) == pytest.approx(1.0)
    assert e030.factor_C(0.06, TP, TL) == pytest.approx(1.75)
    assert e030.factor_C(0.12, TP, TL) == pytest.approx(2.5)  # continuidad en 0,2 TP
    assert e030.factor_C(0.5, TP, TL) == 2.5
    assert e030.factor_C(1.0, TP, TL) == pytest.approx(1.5)
    assert e030.factor_C(3.0, TP, TL) == pytest.approx(2.5 * 0.6 * 2.0 / 9)


def test_C_estatico_usa_meseta_en_periodos_cortos():
    assert e030.factor_C_estatico(0.05, 0.6, 2.0) == 2.5


def test_factor_uso():
    assert e030.factor_uso("C", 4) == 1.0
    assert e030.factor_uso("B", 4) == 1.3
    assert e030.factor_uso("A2", 4) == 1.5
    assert e030.factor_uso("A1", 4, aislamiento=True) == 1.0
    assert e030.factor_uso("A1", 2) == 1.5
    with pytest.raises(ValueError):
        e030.factor_uso("A1", 4)
    with pytest.raises(ValueError):
        e030.factor_uso("D", 4)


def test_r0_y_derivas_modificadas_2026():
    emdl = e030.sistema("ca_emdl")
    assert emdl.R0 == 3.5
    assert emdl.deriva_max == 0.004
    assert e030.sistema("albanileria").R0 == 3
    assert e030.sistema("albanileria").deriva_max == 0.005


def test_sistemas_permitidos():
    assert e030.sistema_permitido("C", 4, "ca_emdl")
    assert not e030.sistema_permitido("B", 4, "ca_emdl")
    assert not e030.sistema_permitido("B", 4, "acero_omf")
    assert e030.sistema_permitido("B", 1, "acero_omf")
    assert not e030.sistema_permitido("A2", 3, "ca_porticos")
    assert not e030.sistema_permitido("A1", 4, "ca_dual")
    assert e030.sistema_permitido("A1", 4, "ca_porticos", aislamiento=True)


def test_irregularidades_y_R():
    Ia, Ip = e030.factores_irregularidad(["piso_blando", "masa", "esquinas_entrantes"])
    assert (Ia, Ip) == (0.75, 0.90)
    assert e030.coeficiente_R(8, Ia, Ip) == pytest.approx(5.4)


def test_restricciones():
    assert e030.verificar_restricciones("C", 4, ["torsional_extrema"], 3, 7.8)
    assert not e030.verificar_restricciones("C", 4, ["torsional"], 3, 7.8)
    assert not e030.verificar_restricciones("C", 2, ["torsional_extrema"], 2, 5.2)
    assert e030.verificar_restricciones("C", 2, ["torsional_extrema"], 4, 10.4)
    assert e030.verificar_restricciones("A2", 3, ["masa"], 2, 6.0)


def test_cortante_basal_y_minimo():
    v = e030.cortante_basal(0.45, 1.0, 2.5, 1.1, 3.0, 261.0)
    assert v.coeficiente == pytest.approx(0.4125)
    assert v.V == pytest.approx(107.6625)
    v = e030.cortante_basal(0.45, 1.0, 0.5, 1.0, 8.0, 100.0)
    assert v.minimo_aplicado
    assert v.C_sobre_R == 0.11


def test_distribucion_en_altura():
    f = e030.distribucion_en_altura([100, 100], [3, 6], 30.0, 0.3)
    assert f == pytest.approx([10.0, 20.0])
    assert sum(e030.distribucion_en_altura([50, 40, 30], [3, 6, 9], 60.0, 1.2)) == pytest.approx(60.0)
    assert e030.exponente_k(1.2) == pytest.approx(1.35)
    assert e030.exponente_k(3.0) == 2.0


def test_estatico_aplicable():
    alb = [e030.sistema("albanileria")]
    porticos = [e030.sistema("ca_porticos")]
    assert e030.estatico_aplicable(4, True, 25, porticos)
    assert not e030.estatico_aplicable(4, False, 25, porticos)
    assert e030.estatico_aplicable(4, False, 12, alb)
    assert e030.estatico_aplicable(1, False, 50, porticos)


def test_separacion_y_desplazamientos():
    assert e030.separacion_minima(0.45, 1.1, 7.8) == pytest.approx(0.07722)
    assert e030.separacion_minima(0.10, 1.0, 3.0) == 0.03
    assert e030.factor_desplazamiento(3, True) == pytest.approx(2.25)
    assert e030.factor_desplazamiento(3, False) == pytest.approx(2.55)
