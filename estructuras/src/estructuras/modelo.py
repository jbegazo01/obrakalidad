"""Modelo lateral pseudo-tridimensional para edificios de muros.

- Cada muro es un voladizo empotrado en la base (E.070 art. 24.5), modelado con elementos
  de viga de Timoshenko (flexión + corte) entre niveles, con su sección transformada
  (columnas por Ec/Em y alas de muros transversales, art. 24.6).
- Los entrepisos son diafragmas rígidos con 3 grados de libertad (ux, uy, θz) referidos al
  origen de coordenadas (E.030 art. 30.3).
- Cargas: fuerzas estáticas de la E.030 aplicadas en el centro de masas de cada nivel,
  más el momento torsor accidental (art. 37). Combinación direccional 100 % + 30 %
  (art. 28.1 y 33.3), con la excentricidad accidental solo en la dirección del 100 % (28.3).
Unidades: tonf, m, s.
"""

from dataclasses import dataclass

import numpy as np

from .muros import MuroAnalisis, seccion
from .unidades import G

CASOS = ("Sx", "Sy", "Tx", "Ty")  # Sx/Sy: fuerzas en el CM; Tx/Ty: torsión accidental (+)


@dataclass
class RespuestaMuro:
    """Fuerzas del sismo (con el R del análisis) en un muro, por entrepiso (índice 0 = piso 1)."""
    V: dict[str, np.ndarray]  # cortante por caso
    M: dict[str, np.ndarray]  # momento en la base del entrepiso por caso


@dataclass
class Combinado:
    V: np.ndarray  # valor absoluto de diseño por entrepiso
    M: np.ndarray
    combinacion: list[str]  # nombre de la combinación que gobierna en cada entrepiso


@dataclass
class ResultadoModelo:
    muros: list[MuroAnalisis]
    rigideces: dict[str, float]  # rigidez lateral del primer entrepiso (referencial), tonf/m
    respuestas: dict[str, RespuestaMuro]
    desplazamientos: dict[str, np.ndarray]  # caso -> (n, 3) [ux, uy, θ] por nivel
    alturas: np.ndarray  # cota de cada nivel
    centros_masa: list[tuple[float, float]]
    extremos: tuple[float, float, float, float]  # xmin, xmax, ymin, ymax de la planta
    periodos: list[float]
    participacion: list[tuple[float, float, float]]  # fracción de masa X, Y, θ por modo

    def combinar(self, id_muro: str) -> Combinado:
        """Envolvente de las combinaciones 100 % + 30 % con torsión accidental ±."""
        r = self.respuestas[id_muro]
        candidatos = []
        for nombre, principal, torsion, otra in (
            ("Sx+Tx+0,3Sy", "Sx", +1, "Sy"),
            ("Sx-Tx+0,3Sy", "Sx", -1, "Sy"),
            ("Sy+Ty+0,3Sx", "Sy", +1, "Sx"),
            ("Sy-Ty+0,3Sx", "Sy", -1, "Sx"),
        ):
            t = "Tx" if principal == "Sx" else "Ty"
            V = np.abs(r.V[principal] + torsion * r.V[t]) + 0.3 * np.abs(r.V[otra])
            M = np.abs(r.M[principal] + torsion * r.M[t]) + 0.3 * np.abs(r.M[otra])
            candidatos.append((nombre, V, M))
        n = len(candidatos[0][1])
        V, M, nombres = np.zeros(n), np.zeros(n), []
        for i in range(n):
            nombre, Vc, Mc = max(candidatos, key=lambda c: c[1][i])
            V[i], M[i] = Vc[i], Mc[i]
            nombres.append(nombre)
        return Combinado(V, M, nombres)

    def derivas(self, alturas_entrepiso: list[float]) -> dict[str, np.ndarray]:
        """Deriva elástica máxima por entrepiso en las esquinas de la planta, por dirección,
        para la combinación 100 % + 30 % con torsión accidental."""
        xmin, xmax, ymin, ymax = self.extremos
        esquinas = [(xmin, ymin), (xmin, ymax), (xmax, ymin), (xmax, ymax)]
        h = np.array(alturas_entrepiso)
        res = {}
        for direccion, principal, t, otra in (("X", "Sx", "Tx", "Sy"), ("Y", "Sy", "Ty", "Sx")):
            maximo = np.zeros(len(h))
            for signo in (+1, -1):
                for x, y in esquinas:
                    d_p = _desplazamiento(self.desplazamientos[principal] + signo * self.desplazamientos[t], x, y, direccion)
                    d_o = _desplazamiento(self.desplazamientos[otra], x, y, direccion)
                    drift = np.abs(np.diff(np.concatenate([[0.0], d_p]))) + 0.3 * np.abs(
                        np.diff(np.concatenate([[0.0], d_o]))
                    )
                    maximo = np.maximum(maximo, drift / h)
            res[direccion] = maximo
        return res

    def relacion_torsion(self) -> dict[str, np.ndarray]:
        """Δmax / Δprom por entrepiso entre los dos bordes de la planta (E.030 Tabla 12),
        para el sismo en cada dirección con su excentricidad accidental."""
        xmin, xmax, ymin, ymax = self.extremos
        res = {}
        for direccion, principal, t, bordes in (
            ("X", "Sx", "Tx", [(0.0, ymin), (0.0, ymax)]),
            ("Y", "Sy", "Ty", [(xmin, 0.0), (xmax, 0.0)]),
        ):
            peor = None
            for signo in (+1, -1):
                u = self.desplazamientos[principal] + signo * self.desplazamientos[t]
                d = [np.abs(np.diff(np.concatenate([[0.0], _desplazamiento(u, x, y, direccion)]))) for x, y in bordes]
                rel = np.maximum(d[0], d[1]) / ((d[0] + d[1]) / 2)
                peor = rel if peor is None else np.maximum(peor, rel)
            res[direccion] = peor
        return res


def _desplazamiento(u: np.ndarray, x: float, y: float, direccion: str) -> np.ndarray:
    """Desplazamiento de un punto (x, y) de cada diafragma en la dirección indicada."""
    if direccion == "X":
        return u[:, 0] - y * u[:, 2]
    return u[:, 1] + x * u[:, 2]


def rigidez_voladizo(E: float, Gm: float, I: float, As: float, alturas_entrepiso: list[float]) -> np.ndarray:
    """Matriz de rigidez lateral (n × n) de un muro en voladizo, condensando los giros."""
    n = len(alturas_entrepiso)
    K = np.zeros((2 * (n + 1), 2 * (n + 1)))  # gdl: (v, θ) por nivel, nivel 0 = base
    for i, L in enumerate(alturas_entrepiso):
        phi = 12 * E * I / (Gm * As * L**2)
        c = E * I / (L**3 * (1 + phi))
        k = c * np.array(
            [
                [12, 6 * L, -12, 6 * L],
                [6 * L, (4 + phi) * L**2, -6 * L, (2 - phi) * L**2],
                [-12, -6 * L, 12, -6 * L],
                [6 * L, (2 - phi) * L**2, -6 * L, (4 + phi) * L**2],
            ]
        )
        idx = [2 * i, 2 * i + 1, 2 * i + 2, 2 * i + 3]
        K[np.ix_(idx, idx)] += k
    libres = list(range(2, 2 * (n + 1)))  # base empotrada
    K = K[np.ix_(libres, libres)]
    v = list(range(0, 2 * n, 2))
    t = list(range(1, 2 * n, 2))
    Kvv, Kvt, Ktt = K[np.ix_(v, v)], K[np.ix_(v, t)], K[np.ix_(t, t)]
    return Kvv - Kvt @ np.linalg.solve(Ktt, Kvt.T)


def _transformacion(muro: MuroAnalisis, n: int) -> np.ndarray:
    """Desplazamiento lateral del muro en cada nivel a partir de (ux, uy, θ) de los diafragmas."""
    T = np.zeros((n, 3 * n))
    for k in range(n):
        if muro.direccion == "x":
            T[k, 3 * k] = 1.0
            T[k, 3 * k + 2] = -muro.linea
        else:
            T[k, 3 * k + 1] = 1.0
            T[k, 3 * k + 2] = muro.linea
    return T


def analizar(
    muros: list[MuroAnalisis],
    alturas_entrepiso: list[float],
    pesos: list[float],
    centros_masa: list[tuple[float, float]],
    fuerzas_x: list[float],
    fuerzas_y: list[float],
    Em: float,
    Ec: float,
) -> ResultadoModelo:
    """Em y Ec en tonf/m². Fuerzas por nivel en tonf (dirección X e Y)."""
    n = len(alturas_entrepiso)
    Ec_sobre_Em = Ec / Em
    K = np.zeros((3 * n, 3 * n))
    datos = {}
    rigideces = {}
    for w in muros:
        sec = seccion(w, muros, Ec_sobre_Em)
        if w.material == "concreto":
            E, Gw = Ec, Ec / (2 * (1 + 0.2))
        else:
            E, Gw = Em, 0.4 * Em
        Kw = rigidez_voladizo(E, Gw, sec.inercia, sec.area_corte / 1.2, alturas_entrepiso)
        T = _transformacion(w, n)
        K += T.T @ Kw @ T
        datos[w.id] = (Kw, T)
        rigideces[w.id] = 1.0 / np.linalg.inv(Kw)[0, 0]

    xs = [w.punto(w.s0)[0] for w in muros] + [w.punto(w.s1)[0] for w in muros]
    ys = [w.punto(w.s0)[1] for w in muros] + [w.punto(w.s1)[1] for w in muros]
    xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
    Dx, Dy = xmax - xmin, ymax - ymin

    cargas = {c: np.zeros(3 * n) for c in CASOS}
    for k in range(n):
        xc, yc = centros_masa[k]
        cargas["Sx"][3 * k] = fuerzas_x[k]
        cargas["Sx"][3 * k + 2] = -fuerzas_x[k] * yc
        cargas["Sy"][3 * k + 1] = fuerzas_y[k]
        cargas["Sy"][3 * k + 2] = fuerzas_y[k] * xc
        cargas["Tx"][3 * k + 2] = fuerzas_x[k] * 0.05 * Dy
        cargas["Ty"][3 * k + 2] = fuerzas_y[k] * 0.05 * Dx

    cotas = np.cumsum(alturas_entrepiso)
    desplazamientos = {}
    respuestas = {w.id: RespuestaMuro({}, {}) for w in muros}
    for caso, F in cargas.items():
        u = np.linalg.solve(K, F)
        desplazamientos[caso] = u.reshape(n, 3)
        for w in muros:
            Kw, T = datos[w.id]
            f = Kw @ (T @ u)  # fuerza lateral en cada nivel
            V = np.array([f[i:].sum() for i in range(n)])
            base = np.concatenate([[0.0], cotas[:-1]])
            M = np.array([sum(f[j] * (cotas[j] - base[i]) for j in range(i, n)) for i in range(n)])
            respuestas[w.id].V[caso] = V
            respuestas[w.id].M[caso] = M

    periodos, participacion = _modos(K, pesos, centros_masa, Dx, Dy)
    return ResultadoModelo(
        muros, rigideces, respuestas, desplazamientos, cotas, centros_masa,
        (xmin, xmax, ymin, ymax), periodos, participacion,
    )


def _modos(K, pesos, centros, Dx, Dy):
    """Periodos y fracción de masa participante (X, Y, rotación) de los modos de vibración."""
    n = len(pesos)
    M = np.zeros((3 * n, 3 * n))
    for k, (P, (xc, yc)) in enumerate(zip(pesos, centros)):
        m = P / G
        r2 = (Dx**2 + Dy**2) / 12  # radio de giro² de una planta rectangular uniforme
        bloque = m * np.array([[1, 0, -yc], [0, 1, xc], [-yc, xc, xc**2 + yc**2 + r2]])
        M[3 * k:3 * k + 3, 3 * k:3 * k + 3] = bloque
    Lc = np.linalg.cholesky(M)
    Linv = np.linalg.inv(Lc)
    w2, z = np.linalg.eigh(Linv @ K @ Linv.T)
    phi = Linv.T @ z
    periodos = [2 * np.pi / np.sqrt(v) for v in w2]
    masa_total = sum(pesos) / G
    part = []
    for j in range(3 * n):
        f = phi[:, j]
        mj = f @ M @ f
        fracciones = []
        for gdl in range(3):
            r = np.zeros(3 * n)
            if gdl < 2:
                r[gdl::3] = 1.0
                ref = masa_total
            else:
                r[2::3] = 1.0
                ref = sum(M[3 * k + 2, 3 * k + 2] for k in range(n))
            gamma = (f @ M @ r) / mj
            fracciones.append(gamma**2 * mj / ref)
        part.append(tuple(fracciones))
    return periodos, part
