"""Diseño de elementos de concreto armado con la E.060: losas aligeradas, vigas y escalera.

Criterios:
- Cargas de gravedad del metrado del piso típico (el más cargado); U = 1,4 CM + 1,7 CV (9.2.1).
- Losas aligeradas y vigas continuas: análisis elástico por pendiente-deflexión con alternancia
  de carga viva; momentos en el eje de los apoyos (conservador). En apoyos extremos
  monolíticos se considera un momento negativo mínimo de wu·ln²/24 (8.3.4).
- Vigas de edificios de albañilería (E.070 art. 25.1): falla por flexión antes que por corte;
  el cortante de diseño es el asociado a los momentos nominales en los extremos más el
  isostático (diseño por capacidad), con estribos de confinamiento según 21.4.4.4.
- Corte de bastones: punto de inflexión de la envolvente + max(d, 12 db, ln/16) (12.12.3),
  y no menos que la longitud de desarrollo (12.2).
Unidades: tonf, m en cargas y longitudes; cm y cm² en secciones; kgf/cm² en resistencias.
"""

import math
from dataclasses import dataclass, field

from .geometria import Losa, Viga
from .metrado import Metrado, OpcionesMetrado, _cargas_losa_por_m2
from .normas import e060
from .normas.e060 import AREAS, DIAMETROS
from .proyecto import Ficha
from .vigas_continuas import Tramo, envolvente

TOL = 1e-6
FD, FL = 1.4, 1.7


def _arriba(x: float, paso: float) -> float:
    return round(math.ceil(x / paso - 1e-9) * paso, 3)


def _abajo(x: float, paso: float) -> float:
    return round(math.floor(x / paso + 1e-9) * paso, 3)


# ------------------------------------------------------------------ armados

ARMADOS_VIGUETA = [
    ('1 %%c 3/8"', 0.71), ('1 %%c 1/2"', 1.29), ('2 %%c 3/8"', 1.42), ('1 %%c 3/8" + 1 %%c 1/2"', 2.00),
    ('2 %%c 1/2"', 2.58), ('1 %%c 1/2" + 1 %%c 5/8"', 3.28), ('2 %%c 5/8"', 3.98),
]


def armado_vigueta(As: float) -> tuple[str, float, str]:
    """Armado de una vigueta (1 o 2 barras); devuelve (texto, área, barra mayor)."""
    for texto, area in ARMADOS_VIGUETA:
        if area >= As - 1e-9:
            mayor = texto.split("%%c ")[-1]
            return texto, area, mayor
    raise ValueError(f"As = {As:.2f} cm² excede 2 Ø 5/8\" en una vigueta: aumentar el peralte del aligerado.")


def armado_viga(As: float, minimo_barras: int = 2) -> tuple[str, float, str]:
    """Combinación usual de 2 a 4 barras de 1/2" a 1" que cubre As."""
    diam = ['1/2"', '5/8"', '3/4"', '1"']
    opciones = []
    for i, d in enumerate(diam):
        for n in (2, 3, 4):
            if n >= minimo_barras:
                opciones.append((f"{n} %%c {d}", n * AREAS[d], d))
        for d2 in diam[:i]:
            opciones.append((f"2 %%c {d} + 1 %%c {d2}", 2 * AREAS[d] + AREAS[d2], d))
            opciones.append((f"2 %%c {d} + 2 %%c {d2}", 2 * AREAS[d] + 2 * AREAS[d2], d))
    for texto, area, d in sorted(opciones, key=lambda o: o[1]):
        if area >= As - 1e-9:
            return texto, area, d
    raise ValueError(f"As = {As:.2f} cm² excede 4 Ø 1\": aumentar la sección de la viga.")


def barras_en_ancho(As: float, ancho: float) -> str:
    """'n Ø d' repartidas en un ancho (cm) con separación entre ejes de 10 a 30 cm."""
    for d in ('5/8"', '3/4"', '1"'):
        n = max(math.ceil(As / AREAS[d]), math.ceil((ancho - 15) / 30) + 1)
        if (ancho - 15) / (n - 1) >= 10.0:
            return f"{n} %%c {d}"
    raise ValueError(f"As = {As:.1f} cm² no cabe en {ancho:.0f} cm.")


def esp(s_cm: float) -> str:
    """Espaciamiento en notación de plano: 10 cm → '.10'; 12,5 cm → '.125'."""
    txt = f"{s_cm / 100:.3f}".rstrip("0")
    entero, dec = txt.split(".")
    return "." + dec.ljust(2, "0")


def malla(As_por_m: float, h: float, barras=('3/8"', '1/2"', '5/8"')) -> tuple[str, float]:
    """Barras en losa o placa para As (cm²/m): 'Ø 3/8" @ .20'. Espaciamiento ≤ 3h y ≤ 40 cm."""
    s_max = min(3 * h, 40.0)
    for b in barras:
        s = _abajo(min(AREAS[b] / As_por_m * 100, s_max), 2.5) if As_por_m > 0 else _abajo(s_max, 2.5)
        if s >= 10.0:
            return f"%%c {b} @ {esp(s)}", AREAS[b] / s * 100
    raise ValueError(f"As = {As_por_m:.2f} cm²/m excede la malla disponible.")


# ------------------------------------------------------------------ aligerados

@dataclass
class ApoyoAligerado:
    posicion: float  # m, coordenada a lo largo de la tira
    Mu: float  # tonf·m por vigueta (valor absoluto del negativo)
    As_req: float
    armado: str
    largo_izq: float  # m, longitud del bastón desde el eje del apoyo hacia la izquierda
    largo_der: float


@dataclass
class TramoAligerado:
    inicio: float
    fin: float
    Mu: float  # tonf·m por vigueta (positivo)
    As_req: float
    armado: str
    Vu: float  # tonf por vigueta, a "d" de la cara
    phi_Vc: float
    ensanche: float  # m de ensanche alternado necesario en cada extremo (0 si no se requiere)


@dataclass
class Tira:
    id: str
    direccion: str  # dirección de las viguetas
    b0: float  # extensión perpendicular de la tira
    b1: float
    h: float  # m
    wD: float  # tonf/m por vigueta
    wL: float
    apoyos: list[ApoyoAligerado]
    tramos: list[TramoAligerado]
    temperatura: str = '%%c 1/4" @ .25'


def tiras_de_losas(losas: list[Losa]) -> list[list[Losa]]:
    """Agrupa paños de aligerado contiguos en la dirección de las viguetas (tramos continuos)."""
    grupos: dict[tuple, list[Losa]] = {}
    for l in losas:
        if l.tipo != "aligerado":
            continue
        (x1, y1), (x2, y2) = l.inicio, l.fin
        if l.direccion == "x":
            clave = ("x", round(min(y1, y2), 6), round(max(y1, y2), 6), l.h)
        else:
            clave = ("y", round(min(x1, x2), 6), round(max(x1, x2), 6), l.h)
        grupos.setdefault(clave, []).append(l)
    tiras = []
    for (d, _, _, _), lista in grupos.items():
        k = 0 if d == "x" else 1
        lista.sort(key=lambda l: min(l.inicio[k], l.fin[k]))
        actual = [lista[0]]
        for l in lista[1:]:
            fin_prev = max(actual[-1].inicio[k], actual[-1].fin[k])
            if abs(min(l.inicio[k], l.fin[k]) - fin_prev) < TOL:
                actual.append(l)
            else:
                tiras.append(actual)
                actual = [l]
        tiras.append(actual)
    return tiras


def _largo_baston(env, k_apoyo: int, lado: str, d: float, db: float, ln: float, ld: float) -> float:
    """Longitud del bastón negativo (m) desde el eje del apoyo hacia el tramo indicado."""
    if lado == "der":
        x, m = env.x[k_apoyo], env.m_min[k_apoyo]
        idx = next((i for i, v in enumerate(m) if v >= -1e-9), len(m) - 1)
        x_inf = x[idx]
    else:
        x, m = env.x[k_apoyo - 1], env.m_min[k_apoyo - 1]
        idx = next((i for i in range(len(m) - 1, -1, -1) if m[i] >= -1e-9), 0)
        x_inf = x[-1] - x[idx]
    extension = max(d, 12 * db, ln * 100 / 16) / 100
    return _arriba(max(x_inf + extension, ld / 100), 0.05)


def disenar_tira(id_: str, losas: list[Losa], ficha: Ficha, op: OpcionesMetrado) -> Tira:
    fc, fy = ficha.fc, ficha.fy
    l0 = losas[0]
    h = l0.h * 100
    d = h - 3.0  # recubrimiento 2 cm (7.7.1c) + media barra
    sec = e060.SeccionT(40.0, 5.0, 10.0, h)
    w = _cargas_losa_por_m2(l0, False, op)  # piso típico
    wD, wL = 0.40 * w.D, 0.40 * w.L
    k = 0 if l0.direccion == "x" else 1
    tramos_geo = [(min(l.inicio[k], l.fin[k]), max(l.inicio[k], l.fin[k])) for l in losas]
    tramos = [Tramo(b - a, wD, wL) for a, b in tramos_geo]
    env = envolvente(tramos, FD, FL)
    wu = FD * wD + FL * wL

    apoyos = []
    nodos = [tramos_geo[0][0]] + [b for _, b in tramos_geo]
    for j, pos in enumerate(nodos):
        Mu = -env.apoyos_neg[j]
        extremo = j in (0, len(nodos) - 1)
        if extremo:
            ln = tramos[0].L if j == 0 else tramos[-1].L
            Mu = max(Mu, wu * ln**2 / 24)
        As = max(e060.as_flexion(Mu * 1e5, 10.0, d, fc, fy), e060.as_minima_t(sec, d, fc, fy, positivo=False))
        if As > e060.as_maxima(10.0, d, fc, fy):
            raise ValueError(f"Aligerado {id_}: acero negativo excede 0,75 Asb; aumentar el peralte.")
        armado, _, barra = armado_vigueta(As)
        ld = e060.longitud_desarrollo(barra, fc, fy, superior=True)
        db = DIAMETROS[barra]
        izq = _largo_baston(env, j, "izq", d, db, tramos[j - 1].L, ld) if j > 0 else 0.0
        der = _largo_baston(env, j, "der", d, db, tramos[j].L, ld) if j < len(tramos) else 0.0
        if extremo:
            # En apoyos extremos se toma ln/4 (no hay inflexión con apoyo simple).
            ln = tramos[0].L if j == 0 else tramos[-1].L
            largo = _arriba(max(ln / 4, ld / 100), 0.05)
            izq, der = (0.0, largo) if j == 0 else (largo, 0.0)
        apoyos.append(ApoyoAligerado(pos, Mu, As, armado, izq, der))

    resultado = []
    phi_vc = e060.PHI_CORTE * 1.1 * e060.vc_viga(10.0, d, fc) / 1000  # 8.11.8: +10 %
    for t, (a, b), Mpos, (Vi, Vd) in zip(tramos, tramos_geo, env.tramos_pos, env.cortantes):
        As = max(e060.as_flexion(Mpos * 1e5, 40.0, d, fc, fy), e060.as_minima_t(sec, d, fc, fy, positivo=True))
        armado, _, _ = armado_vigueta(As)
        Vu = max(Vi, Vd) - wu * (d / 100 + 0.065)  # a "d" de la cara de un apoyo de 0,13 m
        ensanche = 0.0
        if Vu > phi_vc:
            # Longitud desde el apoyo donde el cortante supera φVc.
            ensanche = _arriba((Vu - phi_vc) / wu + d / 100, 0.05)
        resultado.append(TramoAligerado(a, b, Mpos, As, armado, Vu, phi_vc, ensanche))
    return Tira(id_, l0.direccion, *( (min(l0.inicio[1], l0.fin[1]), max(l0.inicio[1], l0.fin[1]))
                                       if l0.direccion == "x" else
                                       (min(l0.inicio[0], l0.fin[0]), max(l0.inicio[0], l0.fin[0])) ),
                l0.h, wD, wL, apoyos, resultado)


def disenar_aligerados(ficha: Ficha) -> list[Tira]:
    op = OpcionesMetrado.desde_ficha(ficha)
    tiras = tiras_de_losas(ficha.geometria.losas)
    tiras.sort(key=lambda g: (g[0].direccion, min(g[0].inicio[1], g[0].fin[1]), min(g[0].inicio[0], g[0].fin[0])))
    return [disenar_tira(f"A-{k}", t, ficha, op) for k, t in enumerate(tiras, start=1)]


# ------------------------------------------------------------------ vigas

@dataclass
class SeccionDiseno:
    posicion: float  # m a lo largo de la viga continua
    Mu: float  # tonf·m (valor absoluto)
    As_req: float
    armado: str


@dataclass
class VigaDiseno:
    id: str  # ids de las vigas que forman la viga continua
    vigas: list[str]
    b: float  # cm
    h: float  # cm
    apoyos: list[SeccionDiseno]  # negativos
    tramos: list[SeccionDiseno]  # positivos
    corrido_sup: str
    corrido_inf: str
    Vu: float  # tonf, de diseño (capacidad o gravedad, el mayor)
    estribos: str
    peralte_minimo: float  # cm, Tabla 9.1
    observaciones: list[str] = field(default_factory=list)


def vigas_continuas(vigas: list[Viga]) -> list[list[Viga]]:
    """Agrupa vigas colineales que comparten un extremo (continuidad sobre el apoyo común)."""
    def clave(v):
        horizontal = abs(v.inicio[1] - v.fin[1]) < TOL
        return ("x", round(v.inicio[1], 6), v.b, v.h) if horizontal else ("y", round(v.inicio[0], 6), v.b, v.h)

    grupos: dict[tuple, list[Viga]] = {}
    for v in vigas:
        grupos.setdefault(clave(v), []).append(v)
    resultado = []
    for (d, _, _, _), lista in grupos.items():
        k = 0 if d == "x" else 1
        lista.sort(key=lambda v: min(v.inicio[k], v.fin[k]))
        actual = [lista[0]]
        for v in lista[1:]:
            if abs(min(v.inicio[k], v.fin[k]) - max(actual[-1].inicio[k], actual[-1].fin[k])) < TOL:
                actual.append(v)
            else:
                resultado.append(actual)
                actual = [v]
        resultado.append(actual)
    return resultado


def _estribos_viga(Vu: float, b: float, d: float, h: float, fc: float, fy: float, db_min: float) -> str:
    """Estribos Ø 3/8": confinamiento en 2h (21.4.4.4) y resto según cortante y d/2."""
    Av = 2 * AREAS['3/8"']
    s_corte = e060.separacion_estribos(Vu * 1000, b, d, fc, fy, Av)
    s0 = min(max(d / 4, 15.0), 10 * db_min, 24 * DIAMETROS['3/8"'], 30.0, s_corte)
    s0 = _abajo(s0, 2.5)
    s = _abajo(min(d / 2, s_corte), 2.5)
    n = math.ceil((2 * h - 5) / s0)
    return f'%%c 3/8": 1@.05, {n}@{esp(s0)}, r@{esp(s)}'


def disenar_viga(grupo: list[Viga], met: Metrado, ficha: Ficha) -> VigaDiseno:
    fc, fy = ficha.fc, ficha.fy
    b, h = grupo[0].b * 100, grupo[0].h * 100
    d = h - 6.0  # recubrimiento 4 cm (7.7.1c) + estribo + media barra
    tramos = []
    for v in grupo:
        # Nivel más cargado (piso típico).
        nivel = max(range(met.n), key=lambda i: met.vigas[v.id][i][0].D + met.vigas[v.id][i][0].L)
        rep, punt = met.vigas[v.id][nivel]
        tramos.append(Tramo(v.luz, rep.D / v.luz, rep.L / v.luz, [(s, p.D, p.L) for s, p in punt]))
    env = envolvente(tramos, FD, FL)
    observaciones = []

    As_min = e060.as_minima_rectangular(b, d, fc, fy)
    As_max = e060.as_maxima(b, d, fc, fy)
    pos = [0.0]
    for t in tramos:
        pos.append(pos[-1] + t.L)
    apoyos = []
    for j, x in enumerate(pos):
        Mu = -env.apoyos_neg[j]
        if j in (0, len(pos) - 1):
            t = tramos[0] if j == 0 else tramos[-1]
            Mu = max(Mu, (FD * t.wD + FL * t.wL) * t.L**2 / 24)
        As = e060.as_flexion(Mu * 1e5, b, d, fc, fy)
        apoyos.append(SeccionDiseno(x, Mu, As, ""))
    positivos = []
    for t, x0, Mpos in zip(tramos, pos, env.tramos_pos):
        positivos.append(SeccionDiseno(x0 + t.L / 2, Mpos, e060.as_flexion(Mpos * 1e5, b, d, fc, fy), ""))

    As_neg_max = max(a.As_req for a in apoyos)
    As_pos_max = max(p.As_req for p in positivos)
    # 21.4.4.1 y 21.4.4.3: dos barras corridas arriba y abajo, ≥ As mín, ≥ 1/4 del máximo, y
    # resistencia positiva en la cara ≥ 1/3 de la negativa.
    sup, As_sup, d_sup = armado_viga(max(As_min, As_neg_max / 4), 2)
    inf, As_inf, d_inf = armado_viga(max(As_min, As_pos_max, As_neg_max / 3), 2)
    if not sup.startswith("2 ") or "+" in sup:
        sup, As_sup, d_sup = armado_viga(max(As_min, As_neg_max / 4), 2)
    for a in apoyos:
        if a.As_req > As_max:
            observaciones.append(f"Acero negativo excede 0,75 Asb en x = {a.posicion:.2f} m: aumentar la sección.")
        faltante = a.As_req - As_sup
        a.armado = sup if faltante <= 0 else f"{sup} + bastones {armado_viga(faltante, 1)[0]}"
    for p in positivos:
        p.armado = inf

    # Cortante por capacidad (E.070 25.1; E.060 21.4.3a) con Mn de los aceros colocados.
    Mn_sup = e060.momento_resistente(max(As_sup, max(a.As_req for a in apoyos)), b, d, fc, fy, phi=1.0) / 1e5
    Mn_inf = e060.momento_resistente(As_inf, b, d, fc, fy, phi=1.0) / 1e5
    Vu = 0.0
    for t, (Vi, Vd) in zip(tramos, env.cortantes):
        w125 = 1.25 * (t.wD + t.wL)
        P125 = sum(1.25 * (PD + PL) for _, PD, PL in t.puntuales)
        v_cap = (Mn_sup + Mn_inf) / t.L + w125 * t.L / 2 + P125
        Vu = max(Vu, v_cap, Vi, Vd)
    db_min = DIAMETROS[d_inf] if DIAMETROS[d_inf] < DIAMETROS[d_sup] else DIAMETROS[d_sup]
    estribos = _estribos_viga(Vu, b, d, h, fc, fy, db_min)

    continuo = len(grupo) > 1
    divisor = 18.5 if continuo else 16.0
    h_min = max(t.L for t in tramos) * 100 / divisor
    if h < h_min - 1e-6:
        observaciones.append(f"Peralte {h:.0f} cm < L/{divisor:g} = {h_min:.0f} cm (Tabla 9.1): verificar deflexiones.")
    return VigaDiseno("/".join(v.id for v in grupo), [v.id for v in grupo], b, h, apoyos, positivos, sup, inf,
                      Vu, estribos, h_min, observaciones)


def disenar_vigas(ficha: Ficha, met: Metrado) -> list[VigaDiseno]:
    return [disenar_viga(g, met, ficha) for g in vigas_continuas(ficha.geometria.vigas)]


# ------------------------------------------------------------------ escalera

@dataclass
class EscaleraDiseno:
    nombre: str
    contrapasos: int
    contrapaso: float  # m
    paso: float  # m
    garganta: float  # m
    ancho_tramo: float  # m
    luz_tramo: float  # m (proyección horizontal)
    luz_descanso: float  # m
    wu_tramo: float  # tonf/m²
    acero_pos: str
    acero_neg: str
    acero_descanso: str
    temperatura: str
    observaciones: list[str]


def disenar_escalera(ficha: Ficha) -> EscaleraDiseno | None:
    hueco = next((h for h in ficha.geometria.huecos if h.escalera), None)
    if hueco is None:
        return None
    fc, fy = ficha.fc, ficha.fy
    p = hueco.escalera
    (x1, y1), (x2, y2) = hueco.inicio, hueco.fin
    largo, ancho = max(abs(x2 - x1), abs(y2 - y1)), min(abs(x2 - x1), abs(y2 - y1))
    descanso = float(p.get("descanso_m", 1.20))
    paso = float(p.get("paso_m", 0.25))
    t = float(p.get("garganta_m", 0.15))
    h_piso = ficha.niveles[0].altura_entrepiso
    n = math.ceil(h_piso / 0.18)
    n += n % 2  # número par: dos tramos iguales
    cp = h_piso / n
    observaciones = []
    if not 0.60 <= 2 * cp + paso <= 0.64:
        observaciones.append(f"2·cp + p = {2 * cp + paso:.3f} m fuera de 0,60–0,64 (A.010): revisar el paso.")
    recorrido = (n / 2 - 1) * paso
    luz = largo - descanso
    if recorrido > luz + 1e-6:
        observaciones.append(f"El tramo ({recorrido:.2f} m) no entra en el hueco ({luz:.2f} m).")
    cos = paso / math.hypot(paso, cp)
    wD = 2.4 * (t / cos + cp / 2) + 0.10
    wL = 0.20
    wu = FD * wD + FL * wL
    d = t * 100 - 3.0
    Mu = wu * luz**2 / 8
    As_min = 0.0018 * 100 * t * 100
    As_pos = max(e060.as_flexion(Mu * 1e5, 100.0, d, fc, fy), As_min)
    As_neg = max(e060.as_flexion(wu * luz**2 / 24 * 1e5, 100.0, d, fc, fy), As_min)
    Vu = wu * luz / 2
    if Vu * 1000 > e060.PHI_CORTE * e060.vc_viga(100.0, d, fc):
        observaciones.append("El cortante del tramo excede φVc: aumentar la garganta.")
    if t < luz / 20 - 1e-6:
        observaciones.append(f"Garganta {t:.2f} m < L/20 = {luz / 20:.2f} m (Tabla 9.1): verificar deflexiones.")

    # Descanso: losa en una dirección entre sus apoyos (ancho del hueco) con la reacción de los tramos.
    ancho_tramo = ancho / 2
    reaccion = 2 * (wu * luz / 2) * ancho_tramo  # tonf, dos tramos sobre el descanso
    wu_desc = FD * (2.4 * t + 0.10) + FL * wL + reaccion / (ancho * descanso)
    As_desc = max(e060.as_flexion(wu_desc * ancho**2 / 8 * 1e5, 100.0, d, fc, fy), As_min)
    return EscaleraDiseno(
        hueco.nombre, n, cp, paso, t, ancho_tramo, luz, ancho, wu,
        malla(As_pos, t * 100)[0], malla(As_neg, t * 100)[0], malla(As_desc, t * 100)[0],
        malla(As_min, t * 100)[0], observaciones,
    )


# ------------------------------------------------------------------ placas

@dataclass
class PuntoDiagrama:
    phi_Pn: float  # tonf
    phi_Mn: float  # tonf·m


@dataclass
class PlacaDiseno:
    id: str
    L: float  # cm
    t: float  # cm
    nucleo: float  # cm, longitud de cada núcleo extremo
    As_nucleo: str  # armado de cada núcleo
    rho_v: float
    rho_h: float
    malla_v: str
    malla_h: str
    estribos_nucleo: str
    combinaciones: list[tuple[str, float, float, float]]  # (nombre, Pu, Mu, φMn a ese Pu)
    Vu: float
    phi_Vn: float
    diagrama: list[PuntoDiagrama]
    observaciones: list[str] = field(default_factory=list)


def diagrama_interaccion(L: float, t: float, capas: list[tuple[float, float]], fc: float, fy: float,
                         n: int = 60) -> list[PuntoDiagrama]:
    """Diagrama φPn–φMn de una sección rectangular L × t (cm) con capas de acero (x desde el
    borde comprimido, área). Compatibilidad de deformaciones, εcu = 0,003 (10.2)."""
    b1 = e060.beta1(fc)
    Ag = L * t
    Ast = sum(a for _, a in capas)
    Po = 0.85 * fc * (Ag - Ast) + fy * Ast
    phi_Pn_max = 0.8 * e060.PHI_COMPRESION * Po  # 10.3.6.2
    puntos = []
    for c in [L * k for k in (0.02 * 1.12**i for i in range(n))]:
        a = min(b1 * c, L)
        Cc = 0.85 * fc * a * t
        Pn = Cc
        Mn = Cc * (L / 2 - a / 2)
        for x, As in capas:
            es = 0.003 * (c - x) / c
            fs = max(min(e060.ES * es, fy), -fy)
            if x < a:
                fs -= 0.85 * fc  # descuenta el concreto desplazado
            Pn += As * fs
            Mn += As * fs * (L / 2 - x)
        limite = 0.1 * fc * Ag
        if Pn >= limite:
            phi = e060.PHI_COMPRESION
        else:
            phi = 0.9 - 0.2 * max(Pn, 0.0) / limite  # 9.3.2.2
        puntos.append(PuntoDiagrama(min(phi * Pn, phi_Pn_max) / 1000, phi * Mn / 1e5))
    # Tracción pura
    puntos.append(PuntoDiagrama(-0.9 * fy * Ast / 1000, 0.0))
    return puntos


def momento_capacidad(diagrama: list[PuntoDiagrama], Pu: float) -> float:
    """φMn del diagrama para la carga axial Pu (interpolación en la rama de mayor momento)."""
    mejor = 0.0
    pts = sorted(diagrama, key=lambda p: p.phi_Pn)
    for p1, p2 in zip(pts, pts[1:]):
        if min(p1.phi_Pn, p2.phi_Pn) - 1e-9 <= Pu <= max(p1.phi_Pn, p2.phi_Pn) + 1e-9:
            if abs(p2.phi_Pn - p1.phi_Pn) < 1e-9:
                m = max(p1.phi_Mn, p2.phi_Mn)
            else:
                f = (Pu - p1.phi_Pn) / (p2.phi_Pn - p1.phi_Pn)
                m = p1.phi_Mn + f * (p2.phi_Mn - p1.phi_Mn)
            mejor = max(mejor, m)
    return mejor


ARMADOS_NUCLEO = [("4 %%c 1/2\"", '1/2"', 4), ("4 %%c 5/8\"", '5/8"', 4), ("6 %%c 5/8\"", '5/8"', 6),
                  ("4 %%c 3/4\"", '3/4"', 4), ("6 %%c 3/4\"", '3/4"', 6), ("4 %%c 1\"", '1"', 4),
                  ("6 %%c 1\"", '1"', 6)]


def disenar_placa(res, w, ficha: Ficha) -> PlacaDiseno:
    """Placa de concreto en un edificio de albañilería: gravedad + sismo moderado
    (E.070 25.1), combinaciones 9.2.3, flexocompresión (cap. 10) y corte (11.10)."""
    from .albanileria import gravedad_muro

    fc, fy = ficha.fc, ficha.fy
    L, t = w.L * 100, w.espesor * 100
    nucleo = 25.0
    comb = res.modelo.combinar(w.id)
    _, CV, CM, _ = gravedad_muro(w, res.metrado, 1)
    Mu = comb.M[0] / 2  # sismo moderado
    Vu = comb.V[0] / 2
    combos = [("1,4CM + 1,7CV", 1.4 * CM + 1.7 * CV, 0.0),
              ("1,25(CM + CV) ± CS", 1.25 * (CM + CV), Mu),
              ("0,9CM ± CS", 0.9 * CM, Mu)]
    Acw = L * t
    hm = ficha.altura_total * 100
    raiz = e060.raiz_fc_mpa(fc) * e060.MPA
    observaciones = []

    # Corte (11.10).
    Vc = e060.vc_muro(Acw, hm, L, fc) / 1000
    if Vu * 1000 <= 0.085 * raiz * Acw:
        rho_h, rho_v = 0.0020, 0.0015  # 11.10.7
    else:
        rho_h = max(0.0025, (Vu / e060.PHI_CORTE - Vc) * 1000 / (Acw * fy))
        rho_v = max(0.0025, 0.0025 + 0.5 * (2.5 - hm / L) * (rho_h - 0.0025))
        rho_v = min(rho_v, rho_h)
    phi_Vn = e060.PHI_CORTE * min(Vc + rho_h * Acw * fy / 1000, e060.vn_max_muro(Acw, fc) / 1000)
    if Vu > phi_Vn + 1e-9:
        observaciones.append("Vu excede φVn máximo (11.10.4): aumentar el espesor o la longitud de la placa.")
    malla_h, As_h = malla(rho_h * t * 100, t)
    malla_v, As_v = malla(rho_v * t * 100, t)

    # Flexocompresión: el menor núcleo que cumpla todas las combinaciones.
    elegido = None
    for texto, barra, nb in ARMADOS_NUCLEO:
        As_n = nb * AREAS[barra]
        capas = [(nucleo / 2, As_n), (L - nucleo / 2, As_n)]
        alma = L - 2 * nucleo
        if alma > 0:
            n_capas = max(int(alma // 20), 1)
            for i in range(n_capas):
                capas.append((nucleo + (i + 0.5) * alma / n_capas, As_v / 100 * alma / n_capas))
        diag = diagrama_interaccion(L, t, capas, fc, fy)
        filas = [(nombre, Pu, M, momento_capacidad(diag, Pu)) for nombre, Pu, M in combos]
        if all(M <= cap + 1e-9 for _, _, M, cap in filas):
            elegido = (texto, barra, diag, filas)
            break
    if elegido is None:
        observaciones.append("Ningún armado de núcleo cumple la flexocompresión: aumentar la placa.")
        texto, barra, _ = ARMADOS_NUCLEO[-1]
        elegido = (texto, barra, diag, filas)
    texto, barra, diag, filas = elegido
    s = min(16 * DIAMETROS[barra], 48 * DIAMETROS["8 mm"], t)  # 7.10.5.2
    estribos = f"%%c 8 mm: 1@.05, r@{esp(_abajo(s, 2.5))}"
    return PlacaDiseno(w.id, L, t, nucleo, texto, rho_v, rho_h, malla_v, malla_h, estribos, filas,
                       Vu, phi_Vn, diag, observaciones)


def disenar_placas(res, ficha: Ficha) -> list[PlacaDiseno]:
    return [disenar_placa(res, w, ficha) for w in res.muros if w.material == "concreto"]


# ------------------------------------------------------------------ zapatas

@dataclass
class ZapataDiseno:
    elemento: str
    tipo: str
    largo: float  # m
    ancho: float  # m
    h: float  # m
    Pu: float  # tonf
    qu: float  # tonf/m²
    Vu_punz: float
    phi_Vc_punz: float
    Vu_corte: float
    phi_Vc_corte: float
    Mu: float  # tonf·m por metro
    acero_largo: str  # barras paralelas al lado largo
    acero_corto: str
    observaciones: list[str] = field(default_factory=list)


def disenar_zapata_aislada(c, cargas, B: float, ficha: Ficha, h0: float = 0.50) -> ZapataDiseno:
    """Zapata cuadrada B × B bajo columna aislada (15.4, 15.5, 11.12)."""
    fc, fy = ficha.fc, ficha.fy
    CM = sum(x.D for x in cargas)
    CV = sum(x.L for x in cargas)
    Pu = FD * CM + FL * CV
    qu = Pu / B**2
    c1, c2 = c.dx, c.dy
    h = h0
    while True:
        d = h - 0.10
        bo = 2 * (c1 + d) + 2 * (c2 + d)
        Vp = Pu - qu * (c1 + d) * (c2 + d)
        phi_vp = e060.PHI_CORTE * e060.vc_punzonamiento(bo * 100, d * 100, fc, max(c1, c2) / min(c1, c2), 40) / 1000
        m = (B - min(c1, c2)) / 2
        Vc1 = qu * B * max(m - d, 0.0)
        phi_vc1 = e060.PHI_CORTE * e060.vc_viga(B * 100, d * 100, fc) / 1000
        if (Vp <= phi_vp and Vc1 <= phi_vc1) or h >= 1.5:
            break
        h = round(h + 0.05, 2)
    Mu = qu * m**2 / 2  # por metro de ancho
    As = max(e060.as_flexion(Mu * 1e5, 100.0, d * 100, fc, fy), 0.0018 * 100 * h * 100)
    acero = malla(As, h * 100, barras=('1/2"', '5/8"', '3/4"'))[0]
    return ZapataDiseno(c.id, "aislada", B, B, h, Pu, qu, Vp, phi_vp, Vc1, phi_vc1, Mu, acero, acero)


def disenar_cimiento_combinado(z, res, ficha: Ficha) -> ZapataDiseno:
    """Cimiento combinado de placas (concreto armado, 15.4, 11.12):
    - transversal: voladizo (B − t)/2 con la presión última máxima;
    - longitudinal: el cimiento recibe el momento en la base de cada placa (sismo moderado,
      E.070 25.1) y lo transmite al suelo; se diseña para el mayor entre ese momento y el de la
      presión del suelo entre apoyos (wu·l²/10), con refuerzo arriba y abajo;
    - peralte para anclar con gancho el refuerzo de los núcleos (12.5)."""
    from .cimentacion import presion_maxima

    fc, fy = ficha.fc, ficha.fy
    placas = [res.muro(c) for c in z.componentes if c in {w.id for w in res.muros}]
    t = max(w.espesor for w in placas)
    P_serv = z.P
    qu = max(FD * P_serv / (z.ancho * z.largo),  # gravedad (D y L no separados: 1,4·(D + L))
             presion_maxima(1.25 * P_serv, z.M_sismo, z.ancho, z.largo))
    M_placa = max(res.modelo.combinar(w.id).M[0] / 2 for w in placas)
    # Luces entre apoyos (placas y columnas) a lo largo del cimiento.
    posiciones = []
    for c in z.componentes:
        if c in {w.id for w in res.muros}:
            w = res.muro(c)
            posiciones += [w.s0, w.s1]
        else:
            col = next(x for x in ficha.geometria.columnas if x.id == c)
            posiciones.append(col.centro[0] if z.direccion == "x" else col.centro[1])
    posiciones.sort()
    luz = max((b - a for a, b in zip(posiciones, posiciones[1:])), default=0.0)
    Mu_long = max(M_placa, qu * z.ancho * luz**2 / 10)
    barra = '5/8"'
    h = max(0.60, _arriba((e060.longitud_gancho(barra, fc, fy) + 10) / 100, 0.05))
    observaciones = []
    while True:
        # Peralte con cuantía longitudinal económica (≤ 0,5 %), muy por debajo de 0,75 ρb.
        d = h - 0.10
        try:
            As_long = e060.as_flexion(Mu_long * 1e5, z.ancho * 100, d * 100, fc, fy)
            if As_long <= 0.005 * z.ancho * 100 * d * 100 or h >= 1.50:
                break
        except ValueError:
            pass
        h = round(h + 0.10, 2)
    As_long = max(As_long, 0.0018 * z.ancho * 100 * h * 100 / 2)
    m = (z.ancho - t) / 2
    Mu_t = qu * m**2 / 2
    As_t = max(e060.as_flexion(Mu_t * 1e5, 100.0, d * 100, fc, fy), 0.0018 * 100 * h * 100)
    Vu = qu * max(m - d, 0.0)
    phi_vc = e060.PHI_CORTE * e060.vc_viga(100.0, d * 100, fc) / 1000
    longitudinal = barras_en_ancho(As_long, z.ancho * 100)
    transversal = malla(As_t, h * 100, barras=('1/2"', '5/8"'))[0]
    observaciones.append(f"Refuerzo longitudinal {longitudinal} arriba y abajo (Mu = {Mu_long:.1f} tonf·m, "
                         "momento de la base de la placa).")
    return ZapataDiseno(z.elemento, "combinado", z.largo, z.ancho, h, 1.25 * P_serv, qu, 0.0, 0.0, Vu, phi_vc,
                        Mu_long, f"{longitudinal} sup. e inf.", transversal, observaciones)


def disenar_zapatas(res, cim, ficha: Ficha) -> list[ZapataDiseno]:
    resultado = []
    for z in cim.cimientos:
        if z.tipo == "aislada":
            col = next(x for x in ficha.geometria.columnas if x.id == z.elemento)
            resultado.append(disenar_zapata_aislada(col, res.metrado.columnas[col.id], z.largo, ficha))
        elif z.tipo == "combinado":
            resultado.append(disenar_cimiento_combinado(z, res, ficha))
    return resultado
