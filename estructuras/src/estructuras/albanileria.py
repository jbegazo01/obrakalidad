"""Análisis y diseño de edificios de albañilería confinada (E.070 cap. 8, arts. 24 a 27).

Flujo: metrado → peso sísmico y centro de masas → fuerzas estáticas E.030 (sismo severo) →
modelo pseudo-3D → fuerzas por muro → verificaciones E.070 → diseño de confinamientos.
Unidades: tonf, m (resistencias en kgf/cm²; áreas de acero y concreto en cm²).
"""

import math
from dataclasses import dataclass, field

import numpy as np

from . import modelo as mod
from .metrado import Metrado, metrar
from .muros import MuroAnalisis, alas, unir_muros
from .normas import e030, e060, e070
from .predimensionamiento import BARRAS
from .proyecto import Ficha

RECUBRIMIENTO = 2.0  # cm, medido al estribo, muros tarrajeados (E.070 art. 11.10)
ESTRIBO_1_4 = 0.32  # cm², Ø 1/4"
BARRA_8MM = 0.50  # cm²
AS_MINIMO_4_8MM = 4 * BARRA_8MM  # E.070 27.3 a.2


@dataclass
class OpcionesDiseno:
    mu: float = 0.8  # coeficiente de fricción: juntas sin tratamiento (27.3 a.2)
    peralte_minimo_columna: float = 25.0  # cm (norma: 15 cm, art. 20.5)


@dataclass
class VerificacionMuro:
    muro: str
    piso: int  # 1 = primer piso
    L: float
    t: float
    Pg: float  # tonf, D + 0,25 L a media altura
    Pm: float  # tonf, D + L en la base del entrepiso
    sigma_m: float  # tonf/m²
    sigma_adm: float  # tonf/m², art. 19.1b
    Ve: float  # tonf, sismo moderado
    Me: float  # tonf·m, sismo moderado
    alfa: float
    Vm: float  # tonf
    factor: float  # Vm1/Ve1 acotado entre 2 y 3
    Vu: float
    Mu: float
    agrietado: bool
    refuerzo_horizontal: str  # "" si no se requiere; si no, el motivo

    @property
    def ok_axial(self) -> bool:
        return self.sigma_m <= self.sigma_adm + 1e-9

    @property
    def ok_fisuracion(self) -> bool:
        return e070.control_fisuracion(self.Ve, self.Vm)


@dataclass
class ResistenciaGlobal:
    direccion: str
    piso: int
    suma_Vm: float
    VE: float

    @property
    def cumple(self) -> bool:
        return self.suma_Vm >= self.VE

    @property
    def elastico(self) -> bool:
        return self.suma_Vm >= 3 * self.VE


@dataclass
class DisenoColumna:
    muro: str
    piso: int
    posicion: tuple[float, float]
    extrema: bool
    agrietado: bool
    Pc: float  # tonf
    Vc: float  # tonf
    T: float  # tonf
    C: float  # tonf
    t: float  # cm
    d: float  # cm, peralte (a lo largo del muro)
    As_req: float  # cm²
    barras: str
    As_colocado: float
    estribos: str


@dataclass
class DisenoSolera:
    muro: str
    piso: int
    Ts: float  # tonf
    As_req: float
    barras: str


@dataclass
class VerificacionPlaca:
    muro: str
    piso: int
    Vu: float
    Mu: float
    phi_Vc: float
    rho_h: float  # cuantía horizontal requerida
    As_extremo: float  # cm², por flexión (aprox. brazo 0,8 L)


@dataclass
class ResultadoAlbanileria:
    ficha: Ficha
    metrado: Metrado
    muros: list[MuroAnalisis]
    sismo: e030.CortanteBasal  # dirección X (igual en Y para este sistema)
    R: float
    fuerzas: list[float]  # tonf por nivel (sismo severo)
    cortantes_entrepiso: list[float]
    modelo: mod.ResultadoModelo
    derivas: dict[str, np.ndarray]  # inelásticas
    relacion_torsion: dict[str, np.ndarray]
    verificaciones: list[VerificacionMuro]
    globales: list[ResistenciaGlobal]
    columnas: list[DisenoColumna]
    soleras: list[DisenoSolera]
    placas: list[VerificacionPlaca]
    tipos_columna: dict[str, dict]  # tipo -> {"t", "d", "barras", "estribos", "nodos"}
    observaciones: list[str] = field(default_factory=list)

    def muro(self, id_: str) -> MuroAnalisis:
        return next(w for w in self.muros if w.id == id_)

    @property
    def cumple(self) -> bool:
        return not any(o.startswith("NO CUMPLE") for o in self.observaciones)


# ---------------------------------------------------------------- cargas por muro

def _pg(c) -> float:
    return c.D + 0.25 * c.L


def gravedad_muro(w: MuroAnalisis, m: Metrado, piso: int) -> tuple[float, float, float, float]:
    """(D a media altura, L, D en la base, L) acumulados desde el techo hasta el entrepiso."""
    D_mid = L = D_base = 0.0
    for p in w.panos:
        for j in range(piso - 1, m.n):
            c = m.total_pano(p.id, j)
            D_mid += c.D
            D_base += c.D
            L += c.L
            pp = m.peso_propio[p.id][j]
            D_base += pp
            D_mid += pp if j > piso - 1 else pp / 2
    return D_mid, L, D_base, L


def carga_columna(w: MuroAnalisis, s: float, piso: int, m: Metrado, todos: list[MuroAnalisis],
                  Ec_sobre_Em: float) -> float:
    """Pc (Tabla 11): carga directa sobre la columna, mitad de la carga de los paños a cada
    lado y carga de los muros transversales según su longitud tributaria (art. 24.6)."""
    punto = w.punto(s)
    pc = 0.0
    for p in w.panos:
        a, b = sorted((p.inicio[0], p.fin[0]) if w.direccion == "x" else (p.inicio[1], p.fin[1]))
        adyacente = abs(a - s) < 1e-6 or abs(b - s) < 1e-6
        for j in range(piso - 1, m.n):
            if adyacente:
                pc += 0.5 * (_pg(m.panos[p.id][j]) + m.peso_propio[p.id][j] * (1.0 if j > piso - 1 else 0.5))
            for cp in m.puntuales[p.id][j]:
                if abs(cp.punto[0] - punto[0]) < 1e-6 and abs(cp.punto[1] - punto[1]) < 1e-6:
                    pc += _pg(cp.carga)
                elif adyacente and a - 1e-6 <= w.coordenada(cp.punto) <= b + 1e-6:
                    pc += 0.5 * _pg(cp.carga)
    for ala in alas(w, todos, Ec_sobre_Em):
        if abs(ala.posicion - s) > 1e-6:
            continue
        t = next(x for x in todos if x.id == ala.muro)
        D_mid, L, _, _ = gravedad_muro(t, m, piso)
        pc += (D_mid + 0.25 * L) / t.L * ala.ancho
    return pc


# ---------------------------------------------------------------- diseño de elementos

def _combinaciones_barras() -> list[tuple[str, float]]:
    """Armados usuales en columnas de confinamiento: 4 barras iguales, 4 + 2, o 6 iguales."""
    areas = {"8 mm": BARRA_8MM, **BARRAS}
    diametros = list(areas)
    opciones = []
    for i, d in enumerate(diametros):
        if d == "8 mm":
            continue  # barras principales de 3/8" o más; 8 mm solo como complemento
        a = areas[d]
        opciones.append((f"4 %%c {d}", 4 * a))
        opciones.append((f"6 %%c {d}", 6 * a))
        for d2 in diametros[:i]:
            opciones.append((f"4 %%c {d} + 2 %%c {d2}", 4 * a + 2 * areas[d2]))
    return sorted(opciones, key=lambda o: o[1])


def _elegir_barras(As: float) -> tuple[str, float]:
    """Armado de menor área que cubre As."""
    for texto, area in _combinaciones_barras():
        if area >= As - 1e-9:
            return texto, area
    raise ValueError(f"As = {As:.2f} cm² excede 6 barras de 1\"; aumentar la sección.")


def _estribos(t: float, d: float, fc: float, fy: float, An_req: float, minimo: bool) -> str:
    if minimo:
        return '%%c 1/4": 1@.05, 4@.10, r@.25'
    Av = 2 * ESTRIBO_1_4
    tn = t - 2 * RECUBRIMIENTO
    Ac, An = t * d, (t - 2 * RECUBRIMIENTO) * (d - 2 * RECUBRIMIENTO)
    s1 = Av * fy / (0.3 * tn * fc * (Ac / An - 1)) if Ac > An else float("inf")
    s2 = Av * fy / (0.12 * tn * fc)
    s3 = max(d / 4, 5.0)
    s4 = 10.0
    s = max(math.floor(min(s1, s2, s3, s4)), 5)
    zona = max(45.0, 1.5 * d)
    k = math.ceil((zona - 5) / s)
    return f'%%c 1/4": 1@.05, {k}@.{s:02d}, r@.25'


def disenar_columna(w: MuroAnalisis, s: float, extrema: bool, agrietado: bool, piso: int,
                    V: float, Mu: float, h: float, Pc: float, delta: float,
                    fc: float, fy: float, op: OpcionesDiseno) -> DisenoColumna:
    """Columna de confinamiento. Muros agrietados (27.3, Tabla 11) con V = Vm del entrepiso;
    muros no agrietados de pisos superiores (27.4) con V = Vu."""
    L, Lm, Nc = w.L, w.Lm, w.Nc
    t = w.espesor * 100
    if agrietado:
        M = Mu - 0.5 * V * h
        F = M / L
        if extrema:
            Vc = 1.5 * V * Lm / (L * (Nc + 1))
            T, C = F - Pc, Pc + F
        else:
            Vc = V * Lm / (L * (Nc + 1))
            T, C = V * h / L - Pc, Pc - 0.5 * V * h / L
        Acf = Vc * 1000 / (0.2 * fc * 0.85)
        As = Vc * 1000 / (fy * op.mu * 0.85) + max(T, 0.0) * 1000 / (fy * 0.85)
    else:
        F = Mu / L
        Vc = 0.0
        if extrema:
            T, C = F - Pc, Pc + F
            As = max(T, 0.0) * 1000 / (0.9 * fy)
        else:
            T, C, As = 0.0, Pc, 0.0
        Acf = 0.0
    phi = 0.7
    An_req = As + (max(C, 0.0) * 1000 / phi - As * fy) / (0.85 * delta * fc)

    d = op.peralte_minimo_columna
    while True:
        Ac = t * d
        An = (t - 2 * RECUBRIMIENTO) * (d - 2 * RECUBRIMIENTO)
        As_min = max(0.1 * fc * Ac / fy, AS_MINIMO_4_8MM)
        As_dis = max(As, As_min)
        if Ac >= max(Acf, 15 * t) and An >= An_req:
            break
        d += 5
        if d > 100:
            break
    barras, As_col = _elegir_barras(As_dis)
    return DisenoColumna(
        w.id, piso, w.punto(s), extrema, agrietado, Pc, Vc, T, C, t, d, As_dis, barras, As_col,
        _estribos(t, d, fc, fy, An_req, minimo=not agrietado),
    )


def disenar_solera(w: MuroAnalisis, piso: int, V: float, h_losa: float, fc: float, fy: float) -> DisenoSolera:
    """Ts = V·Lm/(2L), con V = Vm1 (agrietado) o Vu (no agrietado); As ≥ 0,1 f'c Acs/fy."""
    Ts = V * w.Lm / (2 * w.L)
    Acs = w.espesor * 100 * h_losa * 100
    As = max(Ts * 1000 / (0.9 * fy), 0.1 * fc * Acs / fy, AS_MINIMO_4_8MM)
    barras, _ = _elegir_barras(As)
    return DisenoSolera(w.id, piso, Ts, As, barras)


def verificar_placa(w: MuroAnalisis, piso: int, Vu: float, Mu: float, fc: float, fy: float) -> VerificacionPlaca:
    """Placa de concreto (E.070 art. 25.1: gravedad + sismo moderado; E.060 art. 11.10)."""
    t, L = w.espesor * 100, w.L * 100
    d = 0.8 * L
    Vc = 0.53 * math.sqrt(fc) * t * d / 1000
    phi = 0.85
    Vs_req = max(Vu / phi - Vc, 0.0)
    rho = max(0.0025, Vs_req * 1000 / (t * d * fy))
    As_ext = Mu * 1e5 / (0.9 * fy * 0.8 * L)
    return VerificacionPlaca(w.id, piso, Vu, Mu, phi * Vc, rho, As_ext)


# ---------------------------------------------------------------- análisis completo

def analizar(ficha: Ficha, opciones: OpcionesDiseno | None = None) -> ResultadoAlbanileria:
    op = opciones or OpcionesDiseno()
    if ficha.unidad_albanileria is None:
        raise ValueError("Falta 'materiales.unidad_albanileria'.")
    for clave in (ficha.sistema_x, ficha.sistema_y):
        if clave != "albanileria":
            raise ValueError("El análisis de albañilería requiere sistema 'albanileria' en ambas direcciones.")
    if ficha.n_pisos > 5 or ficha.altura_total > 15.0:
        raise ValueError("E.070 art. 27a: el diseño de albañilería confinada aplica hasta 5 pisos o 15 m.")

    observaciones: list[str] = []
    unidad = e070.unidad(ficha.unidad_albanileria)
    fm, vm, fc, fy = unidad.fm, unidad.vm, ficha.fc, ficha.fy
    Em = e070.modulo_elasticidad(fm) * 10  # tonf/m²
    Ec = e060.modulo_elasticidad(fc) * 10
    Ec_sobre_Em = Ec / Em
    vm_max = 0.319 * math.sqrt(fm * 0.0980665) / 0.0980665  # art. 13.8, en kgf/cm²
    if vm > vm_max:
        observaciones.append(f"v'm limitado a 0,319√f'm = {vm_max:.2f} kgf/cm² (art. 13.8).")
        vm = vm_max

    met = metrar(ficha)
    observaciones += met.advertencias
    muros = unir_muros(ficha.muros, ficha.geometria)
    h = [n.altura_entrepiso for n in ficha.niveles]
    h_losa = max(l.h for l in ficha.geometria.losas)
    n = ficha.n_pisos

    # Sismo severo (E.070 art. 22a: E.030 con R = 3, reducido si hay irregularidades).
    sitio = e030.parametros_sitio(ficha.zona, ficha.perfil_suelo, ficha.vs30)
    U = e030.factor_uso(ficha.categoria, ficha.zona, ficha.aislamiento)
    Ia, Ip = e030.factores_irregularidad(ficha.irregularidades)
    R = e030.coeficiente_R(e030.sistema("albanileria").R0, Ia, Ip)
    T = ficha.periodo_x or e030.periodo_fundamental(ficha.altura_total, 60)
    C = e030.factor_C_estatico(T, sitio.TP, sitio.TL)
    sismo = e030.cortante_basal(sitio.Z, U, C, sitio.S, R, sum(met.pesos_sismicos))
    cotas = list(np.cumsum(h))
    F = e030.distribucion_en_altura(met.pesos_sismicos, cotas, sismo.V, T)
    VE = [sum(F[i:]) for i in range(n)]

    res = mod.analizar(muros, h, met.pesos_sismicos, met.centros_masa, F, F, Em, Ec)
    factor_d = e030.factor_desplazamiento(R, ficha.regular)
    derivas = {k: v * factor_d for k, v in res.derivas(h).items()}
    rel = res.relacion_torsion()

    deriva_max = e030.sistema("albanileria").deriva_max
    for d, valores in derivas.items():
        if valores.max() > deriva_max:
            observaciones.append(f"NO CUMPLE: deriva en {d} = {valores.max():.4f} > {deriva_max} (E.030 Tabla 14).")
        aplica = valores.max() > 0.5 * deriva_max
        r = rel[d].max()
        if aplica and r > 1.5:
            observaciones.append(
                f"NO CUMPLE: irregularidad torsional extrema en {d} (Δmax/Δprom = {r:.2f} > 1,5), "
                "no permitida en esta categoría y zona (E.030 Tabla 13). Rebalancear la rigidez en planta."
            )
        elif aplica and r > 1.3 and "torsional" not in ficha.irregularidades:
            observaciones.append(
                f"Irregularidad torsional en {d} (Δmax/Δprom = {r:.2f} > 1,3): agregar 'torsional' a "
                "estructura.irregularidades (Ip = 0,75) y volver a calcular."
            )

    # --- Verificaciones por muro y entrepiso.
    verificaciones: list[VerificacionMuro] = []
    placas: list[VerificacionPlaca] = []
    combinados = {w.id: res.combinar(w.id) for w in muros}
    for w in muros:
        comb = combinados[w.id]
        Ve = comb.V / 2  # sismo moderado
        Me = comb.M / 2
        if w.material == "concreto":
            for i in range(n):
                placas.append(verificar_placa(w, i + 1, Ve[i], Me[i], fc, fy))
            continue
        filas = []
        for i in range(n):
            D_mid, L_v, D_base, _ = gravedad_muro(w, met, i + 1)
            Pg = D_mid + 0.25 * L_v
            Pm = D_base + L_v
            sigma = Pm / (w.L * w.espesor)
            h_libre = h[i] - h_losa
            sigma_adm = e070.esfuerzo_axial_maximo(fm, h_libre, w.espesor)
            alfa = e070.factor_esbeltez(Ve[i], Me[i], w.L)
            Vm_i = e070.resistencia_corte(vm, alfa, w.espesor, w.L, Pg)
            filas.append([Pg, Pm, sigma, sigma_adm, alfa, Vm_i])
        Vm1, Ve1 = filas[0][5], Ve[0]
        factor = min(max(Vm1 / Ve1, 2.0), 3.0) if Ve1 > 0 else 3.0
        for i in range(n):
            Pg, Pm, sigma, sigma_adm, alfa, Vm_i = filas[i]
            Vu, Mu = Ve[i] * factor, Me[i] * factor
            agrietado = i == 0 or Vu >= Vm_i
            motivo = []
            if Vu >= Vm_i:
                motivo.append("Vu ≥ Vm")
            if sigma >= 0.05 * fm * 10:
                motivo.append("σm ≥ 0,05 f'm")
            if i == 0 and n > 3:
                motivo.append("primer piso de edificio de más de 3 pisos")
            verificaciones.append(
                VerificacionMuro(w.id, i + 1, w.L, w.espesor, Pg, Pm, sigma, sigma_adm, Ve[i], Me[i],
                                 alfa, Vm_i, factor, Vu, Mu, agrietado, ", ".join(motivo))
            )

    for v in verificaciones:
        if not v.ok_axial:
            observaciones.append(f"NO CUMPLE: esfuerzo axial en {v.muro}, piso {v.piso} "
                                 f"({v.sigma_m:.1f} > {v.sigma_adm:.1f} tonf/m², art. 19.1b).")
        if not v.ok_fisuracion:
            observaciones.append(f"NO CUMPLE: fisuración en {v.muro}, piso {v.piso} "
                                 f"(Ve = {v.Ve:.2f} > 0,55 Vm = {0.55 * v.Vm:.2f} tonf, art. 26.2).")

    # --- Resistencia global (26.4).
    globales = []
    for direccion in ("x", "y"):
        for i in range(n):
            suma = sum(v.Vm for v in verificaciones
                       if v.piso == i + 1 and _direccion(muros, v.muro) == direccion and v.L >= e070.LONGITUD_MINIMA_MURO)
            suma += sum(p.phi_Vc / 0.85 for p in placas if p.piso == i + 1 and _direccion(muros, p.muro) == direccion)
            g = ResistenciaGlobal(direccion.upper(), i + 1, suma, VE[i])
            globales.append(g)
            if not g.cumple:
                observaciones.append(f"NO CUMPLE: ΣVm = {suma:.1f} < VE = {VE[i]:.1f} tonf en {direccion.upper()}, "
                                     f"piso {i + 1} (art. 26.4).")

    # --- Confinamientos.
    columnas: list[DisenoColumna] = []
    soleras: list[DisenoSolera] = []
    for w in muros:
        if w.material != "albanileria":
            continue
        transversales = {round(a.posicion, 6) for a in alas(w, muros, Ec_sobre_Em)}
        for v in [x for x in verificaciones if x.muro == w.id]:
            i = v.piso - 1
            V = v.Vm if v.agrietado else v.Vu
            for k, s in enumerate(w.nodos):
                extrema = k in (0, len(w.nodos) - 1)
                Pc = carga_columna(w, s, v.piso, met, muros, Ec_sobre_Em)
                delta = 1.0 if round(s, 6) in transversales else 0.8
                columnas.append(disenar_columna(w, s, extrema, v.agrietado, v.piso, V, v.Mu, h[i], Pc,
                                                delta, fc, fy, op))
            soleras.append(disenar_solera(w, v.piso, V, h_losa, fc, fy))

    for p in placas:
        if p.rho_h > 0.0025:
            observaciones.append(f"Placa {p.muro}, piso {p.piso}: requiere ρh = {p.rho_h:.4f} (E.060).")

    tipos = _tipos_columna(columnas, fc, fy)
    return ResultadoAlbanileria(
        ficha, met, muros, sismo, R, F, VE, res, derivas, rel, verificaciones, globales, columnas,
        soleras, placas, tipos, observaciones,
    )


def _direccion(muros: list[MuroAnalisis], id_: str) -> str:
    return next(w.direccion for w in muros if w.id == id_)


def _tipos_columna(columnas: list[DisenoColumna], fc: float, fy: float) -> dict[str, dict]:
    """Agrupa columnas por nudo (envolvente de pisos y muros que concurren) y luego en tipos."""
    por_nudo: dict[tuple[float, float], list[DisenoColumna]] = {}
    for c in columnas:
        clave = (round(c.posicion[0], 3), round(c.posicion[1], 3))
        por_nudo.setdefault(clave, []).append(c)
    firmas: dict[tuple, list[tuple[float, float]]] = {}
    for nudo, lista in por_nudo.items():
        # Art. 26.1a: en la intersección se coloca el mayor refuerzo de los diseños de cada muro.
        t = max(c.t for c in lista)
        d = max(c.d for c in lista)
        As = max(max(c.As_req for c in lista), 0.1 * fc * t * d / fy)
        barras, _ = _elegir_barras(As)
        estribo = min((c.estribos for c in lista), key=_paso_estribo)
        firma = (t, d, barras, estribo)
        firmas.setdefault(firma, []).append(nudo)
    tipos = {}
    for k, (firma, nudos) in enumerate(sorted(firmas.items(), key=lambda f: (f[0][0] * f[0][1], f[0][2])), start=1):
        t, d, barras, estribos = firma
        tipos[f"C-{k}"] = {"t": t, "d": d, "barras": barras, "estribos": estribos, "nodos": sorted(nudos)}
    return tipos


def _paso_estribo(texto: str) -> int:
    """Espaciamiento en la zona confinada (cm) de una especificación '1@.05, k@.ss, r@.25'."""
    try:
        return int(texto.split(",")[1].split("@.")[1])
    except (IndexError, ValueError):
        return 99
