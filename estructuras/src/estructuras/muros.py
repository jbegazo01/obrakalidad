"""Muros de análisis: paños colineales y contiguos unidos en un solo muro, y sus propiedades
de sección para el cálculo de rigidez (E.070 art. 24.6).

Un muro confinado de varios paños (con columnas intermedias) trabaja como un solo muro: su
longitud L incluye todos los paños y Nc es su número de columnas (E.070 Tabla 11).
"""

from dataclasses import dataclass, field

from .geometria import LADO_COLUMNA_CONFINAMIENTO, Geometria
from .normas.e070 import Muro

TOL = 1e-6


@dataclass
class MuroAnalisis:
    id: str
    direccion: str  # "x" o "y"
    material: str  # "albanileria" o "concreto"
    espesor: float  # m
    linea: float  # coordenada fija: y para muros en X, x para muros en Y
    s0: float  # inicio a lo largo del muro
    s1: float  # fin a lo largo del muro
    panos: list[Muro]
    nodos: list[float] = field(default_factory=list)  # posiciones de columnas a lo largo del muro

    @property
    def L(self) -> float:
        return self.s1 - self.s0

    @property
    def Nc(self) -> int:
        return len(self.nodos)

    @property
    def Lm(self) -> float:
        """Longitud del paño mayor ó 0,5 L, lo que sea mayor (E.070 Tabla 11)."""
        if len(self.panos) == 1:
            return self.L
        return max(max(p.longitud for p in self.panos), 0.5 * self.L)

    @property
    def centro(self) -> tuple[float, float]:
        s = (self.s0 + self.s1) / 2
        return (s, self.linea) if self.direccion == "x" else (self.linea, s)

    def punto(self, s: float) -> tuple[float, float]:
        return (s, self.linea) if self.direccion == "x" else (self.linea, s)

    def contiene(self, p: tuple[float, float]) -> bool:
        """True si el punto está sobre el eje del muro (incluidos sus extremos)."""
        if self.direccion == "x":
            return abs(p[1] - self.linea) < TOL and self.s0 - TOL <= p[0] <= self.s1 + TOL
        return abs(p[0] - self.linea) < TOL and self.s0 - TOL <= p[1] <= self.s1 + TOL

    def coordenada(self, p: tuple[float, float]) -> float:
        return p[0] if self.direccion == "x" else p[1]


def _clave_linea(m: Muro) -> float:
    return m.inicio[1] if m.direccion == "x" else m.inicio[0]


def _tramo(m: Muro) -> tuple[float, float]:
    a, b = (m.inicio[0], m.fin[0]) if m.direccion == "x" else (m.inicio[1], m.fin[1])
    return min(a, b), max(a, b)


def _nombre_eje(ejes: dict[str, float], valor: float) -> str | None:
    for nombre, v in ejes.items():
        if abs(v - valor) < TOL:
            return nombre
    return None


def unir_muros(muros: list[Muro], geo: Geometria | None = None) -> list[MuroAnalisis]:
    """Une paños colineales, contiguos y de igual espesor y material en muros de análisis."""
    sin_coordenadas = [m.id for m in muros if m.inicio is None]
    if sin_coordenadas:
        raise ValueError(f"Los muros {', '.join(sin_coordenadas)} no tienen coordenadas ('desde'/'hasta').")

    grupos: dict[tuple, list[Muro]] = {}
    for m in muros:
        clave = (m.direccion, round(_clave_linea(m), 6), round(m.espesor, 6), m.material)
        grupos.setdefault(clave, []).append(m)

    resultado: list[MuroAnalisis] = []
    for (direccion, linea, espesor, material), lista in grupos.items():
        lista.sort(key=lambda m: _tramo(m)[0])
        cadena: list[Muro] = []
        for m in lista:
            if cadena and abs(_tramo(cadena[-1])[1] - _tramo(m)[0]) > TOL:
                resultado.append(_crear(direccion, linea, espesor, material, cadena))
                cadena = []
            cadena.append(m)
        if cadena:
            resultado.append(_crear(direccion, linea, espesor, material, cadena))

    _nombrar(resultado, geo)
    resultado.sort(key=lambda w: (w.direccion, w.id))
    return resultado


def _crear(direccion, linea, espesor, material, cadena: list[Muro]) -> MuroAnalisis:
    nodos = sorted({round(v, 6) for m in cadena for v in _tramo(m)})
    return MuroAnalisis(
        id="",
        direccion=direccion,
        material=material,
        espesor=espesor,
        linea=linea,
        s0=nodos[0],
        s1=nodos[-1],
        panos=list(cadena),
        nodos=nodos if material == "albanileria" else [nodos[0], nodos[-1]],
    )


def _nombrar(muros: list[MuroAnalisis], geo: Geometria | None):
    """Muros de un paño conservan su id; los de varios paños se nombran por su eje."""
    por_eje: dict[str, list[MuroAnalisis]] = {}
    for w in muros:
        if len(w.panos) == 1:
            w.id = w.panos[0].id
            continue
        eje = None
        if geo is not None:
            eje = _nombre_eje(geo.ejes_y if w.direccion == "x" else geo.ejes_x, w.linea)
        base = f"M{w.direccion.upper()}-{eje}" if eje else f"{w.panos[0].id}…{w.panos[-1].id}"
        por_eje.setdefault(base, []).append(w)
    for base, lista in por_eje.items():
        if len(lista) == 1:
            lista[0].id = base
        else:
            for i, w in enumerate(sorted(lista, key=lambda w: w.s0)):
                w.id = f"{base}{chr(ord('a') + i)}"


@dataclass
class Ala:
    """Aporte de un muro transversal a la sección del muro en análisis (E.070 art. 24.6)."""
    muro: str  # id del muro transversal
    posicion: float  # coordenada a lo largo del muro en análisis
    ancho: float  # m, longitud del ala (en la dirección transversal)
    espesor: float  # m
    lado: int  # +1 o -1: hacia dónde se extiende respecto del eje del muro
    E_relativo: float  # E del ala / E del muro en análisis


def _longitud_transversal_desde(t: MuroAnalisis, s_nodo: float) -> list[tuple[float, int]]:
    """Longitudes del muro transversal a cada lado del nodo (largo, signo)."""
    tramos = []
    if s_nodo - t.s0 > TOL:
        tramos.append((s_nodo - t.s0, -1))
    if t.s1 - s_nodo > TOL:
        tramos.append((t.s1 - s_nodo, +1))
    return tramos


def alas(muro: MuroAnalisis, todos: list[MuroAnalisis], Ec_sobre_Em: float) -> list[Ala]:
    """Alas de muros transversales que concurren al muro (24.6): 25 % de su longitud o 6t,
    lo que sea mayor; si el transversal concurre a dos muros, no más de la mitad de su longitud."""
    resultado = []
    for t in todos:
        if t.direccion == muro.direccion:
            continue
        # Intersección: punto del eje de t sobre la línea del muro.
        p = muro.punto(t.linea)
        if not (muro.contiene(p) and t.contiene(p)):
            continue
        s_t = t.coordenada(p)
        concurrencias = sum(1 for w in todos if w.direccion == muro.direccion and _se_cruzan(t, w))
        total = max(0.25 * t.L, 6 * t.espesor)
        if concurrencias >= 2:
            total = min(total, t.L / 2)
        lados = _longitud_transversal_desde(t, s_t)
        for largo, lado in lados:
            # El ancho total se reparte entre los lados del nudo (muro transversal pasante).
            ancho = min(total / len(lados), largo)
            if t.material == muro.material:
                e_rel = 1.0
            elif t.material == "concreto":
                e_rel = Ec_sobre_Em
            else:
                e_rel = 1.0 / Ec_sobre_Em
            resultado.append(Ala(t.id, muro.coordenada(p), ancho, t.espesor, lado, e_rel))
    return resultado


def _se_cruzan(t: MuroAnalisis, w: MuroAnalisis) -> bool:
    """True si los ejes de dos muros perpendiculares se tocan."""
    p = t.punto(w.linea)
    return t.contiene(p) and w.contiene(p)


@dataclass
class Seccion:
    area_corte: float  # m², alma (t·L) para la deformación por corte
    inercia: float  # m⁴, respecto del centroide, en unidades del material del muro
    centroide: float  # coordenada a lo largo del muro


def seccion(muro: MuroAnalisis, todos: list[MuroAnalisis], Ec_sobre_Em: float) -> Seccion:
    """Sección transformada al material del muro: alma, columnas de confinamiento (concreto
    transformado por Ec/Em, art. 24.6) y alas de los muros transversales."""
    # Rectángulos a lo largo del muro: (posición del centro, largo en la dirección del muro, ancho).
    partes: list[tuple[float, float, float]] = [((muro.s0 + muro.s1) / 2, muro.L, muro.espesor)]
    if muro.material == "albanileria":
        extra = muro.espesor * (Ec_sobre_Em - 1.0)
        for s in muro.nodos:
            a = max(s - LADO_COLUMNA_CONFINAMIENTO / 2, muro.s0)
            b = min(s + LADO_COLUMNA_CONFINAMIENTO / 2, muro.s1)
            partes.append(((a + b) / 2, b - a, extra))
    for ala in alas(muro, todos, Ec_sobre_Em):
        # El ala aporta su espesor a lo largo del muro y su ancho en la otra dirección.
        partes.append((ala.posicion, ala.espesor, ala.ancho * ala.E_relativo))

    area = sum(l * b for _, l, b in partes)
    centroide = sum(s * l * b for s, l, b in partes) / area
    inercia = sum(b * l**3 / 12 + l * b * (s - centroide) ** 2 for s, l, b in partes)
    return Seccion(area_corte=muro.espesor * muro.L, inercia=inercia, centroide=centroide)
