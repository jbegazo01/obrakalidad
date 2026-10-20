"""Análisis de vigas continuas por pendiente-deflexión, con alternancia de carga viva.

Tramos prismáticos de igual rigidez, apoyos simples (sin desplazamiento vertical). Los momentos
de extremo se toman positivos en sentido horario; los momentos de diseño se reportan con la
convención usual: positivo = tracción abajo. Unidades: tonf, m.
"""

from dataclasses import dataclass, field

import numpy as np


@dataclass
class Tramo:
    L: float
    wD: float = 0.0  # carga uniforme muerta (tonf/m)
    wL: float = 0.0  # carga uniforme viva (tonf/m)
    puntuales: list[tuple[float, float, float]] = field(default_factory=list)  # (a, PD, PL)


@dataclass
class Envolvente:
    """Momentos y cortantes últimos (1,4 D + 1,7 L) con alternancia de carga viva."""
    apoyos_neg: list[float]  # momento negativo (≤ 0) en cada apoyo
    tramos_pos: list[float]  # momento positivo máximo en cada tramo
    cortantes: list[tuple[float, float]]  # cortante máximo en cada extremo de cada tramo
    x: list[np.ndarray]  # abscisas de cada tramo
    m_max: list[np.ndarray]  # envolvente superior en cada tramo
    m_min: list[np.ndarray]  # envolvente inferior en cada tramo


def _empotramiento(t: Tramo, fD: float, fL: float) -> tuple[float, float]:
    """Momentos de empotramiento (horario +) para factores de carga dados."""
    w = fD * t.wD + fL * t.wL
    M_ij = -w * t.L**2 / 12
    M_ji = w * t.L**2 / 12
    for a, PD, PL in t.puntuales:
        P = fD * PD + fL * PL
        b = t.L - a
        M_ij -= P * a * b**2 / t.L**2
        M_ji += P * a**2 * b / t.L**2
    return M_ij, M_ji


def resolver(tramos: list[Tramo], factores: list[tuple[float, float]],
             extremos_empotrados: tuple[bool, bool] = (False, False)) -> list[tuple[float, float]]:
    """Momentos de extremo (M_ij, M_ji) de cada tramo; factores[k] = (fD, fL) del tramo k."""
    n = len(tramos)
    K = np.zeros((n + 1, n + 1))
    F = np.zeros(n + 1)
    fem = []
    for k, (t, (fD, fL)) in enumerate(zip(tramos, factores)):
        r = 2.0 / t.L  # 2EI/L con EI = 1
        K[k, k] += 2 * r
        K[k, k + 1] += r
        K[k + 1, k] += r
        K[k + 1, k + 1] += 2 * r
        m = _empotramiento(t, fD, fL)
        fem.append(m)
        F[k] -= m[0]
        F[k + 1] -= m[1]
    libres = [i for i in range(n + 1)
              if not ((i == 0 and extremos_empotrados[0]) or (i == n and extremos_empotrados[1]))]
    theta = np.zeros(n + 1)
    theta[libres] = np.linalg.solve(K[np.ix_(libres, libres)], F[libres])
    resultado = []
    for k, t in enumerate(tramos):
        r = 2.0 / t.L
        M_ij = fem[k][0] + r * (2 * theta[k] + theta[k + 1])
        M_ji = fem[k][1] + r * (theta[k] + 2 * theta[k + 1])
        resultado.append((M_ij, M_ji))
    return resultado


def diagrama(t: Tramo, M_ij: float, M_ji: float, fD: float, fL: float, n: int = 41):
    """Momento (positivo = tracción abajo) y cortante a lo largo del tramo."""
    w = fD * t.wD + fL * t.wL
    P = [(a, fD * PD + fL * PL) for a, PD, PL in t.puntuales]
    R0 = w * t.L / 2 + sum(p * (t.L - a) / t.L for a, p in P)
    V_izq = R0 - (M_ij + M_ji) / t.L
    x = np.linspace(0, t.L, n)
    M = M_ij + V_izq * x - w * x**2 / 2
    for a, p in P:
        M = M - p * np.clip(x - a, 0, None)
    V_der = V_izq - w * t.L - sum(p for _, p in P)
    return x, M, V_izq, V_der


def envolvente(tramos: list[Tramo], fD: float = 1.4, fL: float = 1.7,
               extremos_empotrados: tuple[bool, bool] = (False, False)) -> Envolvente:
    """Alternancia: carga viva en todos los tramos, en tramos pares, en impares y en cada par
    de tramos adyacentes (máximo negativo en el apoyo común)."""
    n = len(tramos)
    patrones = [[True] * n, [k % 2 == 0 for k in range(n)], [k % 2 == 1 for k in range(n)]]
    for k in range(n - 1):
        patrones.append([j in (k, k + 1) for j in range(n)])
    xs = [None] * n
    m_max = [None] * n
    m_min = [None] * n
    v = [[0.0, 0.0] for _ in range(n)]
    for patron in patrones:
        factores = [(fD, fL if cargado else 0.0) for cargado in patron]
        extremos = resolver(tramos, factores, extremos_empotrados)
        for k, (t, (M_ij, M_ji)) in enumerate(zip(tramos, extremos)):
            x, M, Vi, Vd = diagrama(t, M_ij, M_ji, *factores[k])
            xs[k] = x
            m_max[k] = M if m_max[k] is None else np.maximum(m_max[k], M)
            m_min[k] = M if m_min[k] is None else np.minimum(m_min[k], M)
            v[k][0] = max(v[k][0], abs(Vi))
            v[k][1] = max(v[k][1], abs(Vd))
    apoyos = [0.0] * (n + 1)
    for k in range(n):
        apoyos[k] = min(apoyos[k], m_min[k][0])
        apoyos[k + 1] = min(apoyos[k + 1], m_min[k][-1])
    return Envolvente(apoyos, [max(float(m.max()), 0.0) for m in m_max], [tuple(c) for c in v],
                      xs, m_max, m_min)
