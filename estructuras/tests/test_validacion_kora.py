"""Contraste con la memoria de cálculo del edificio Residencial Kora (2023, E.030-2018).

Valores de la memoria (pág. 10 y 11): Z = 0,45; U = 1,00; S = 1,05; TP = 0,60 s; TL = 2,00 s;
R0 = 6, Ip = 0,75 → R = 4,5; Tx = 0,758 s, Ty = 0,632 s; Cx = 1,978, Cy = 2,373;
kx = 1,129, ky = 1,066; ZUCS/R: X = 0,208, Y = 0,249.
Para T > TP las fórmulas de C y de V no cambiaron entre 2018 y 2026.
"""

from pathlib import Path

import pytest

from estructuras import analisis
from estructuras.normas import e030
from estructuras.proyecto import leer_ficha

PESOS_KORA = [181.55004] * 10 + [150.14391]


@pytest.mark.parametrize("T, C, k, coef", [(0.758, 1.978, 1.129, 0.208), (0.632, 2.373, 1.066, 0.249)])
def test_reproduce_parametros_de_la_memoria(T, C, k, coef):
    R = e030.coeficiente_R(6, 1.0, 0.75)
    assert R == 4.5
    c = e030.factor_C(T, 0.6, 2.0)
    assert c == pytest.approx(C, abs=1e-3)
    assert e030.exponente_k(T) == pytest.approx(k, abs=1e-3)
    v = e030.cortante_basal(0.45, 1.0, c, 1.05, R, sum(PESOS_KORA))
    assert v.coeficiente == pytest.approx(coef, abs=5e-4)


def test_kora_con_e030_2026():
    ficha = leer_ficha(Path(__file__).parent.parent / "ejemplos" / "kora_e030_2026.yaml")
    r = analisis.analisis_estatico(ficha)
    assert r.sitio.S == 1.10  # S2 sin Vs30, zona 4
    x, y = r.direcciones
    assert x.R == 4.5
    assert x.cortante.coeficiente == pytest.approx(0.45 * 1.979 * 1.10 / 4.5, abs=1e-3)
    assert y.cortante.coeficiente == pytest.approx(0.45 * 2.373 * 1.10 / 4.5, abs=1e-3)
    # Junta: la memoria usó s = 0,006 h; la E.030-2026 exige s = 0,02·Z·S·h.
    assert r.separacion_minima == pytest.approx(0.02 * 0.45 * 1.10 * 28.05)
