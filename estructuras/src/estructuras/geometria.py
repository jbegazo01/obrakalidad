"""Geometría en planta: ejes, muros, columnas, vigas, losas y huecos. Coordenadas en m.

En la ficha, un punto se escribe como [eje_x, eje_y] usando los nombres de los ejes
(p. ej. [A, 1]) o coordenadas numéricas (p. ej. [2.40, 8.00]).
"""

from dataclasses import dataclass, field

from .normas.e070 import Muro

Punto = tuple[float, float]

LADO_COLUMNA_CONFINAMIENTO = 0.25  # m, dimensión mínima de práctica a lo largo del muro


@dataclass
class Columna:
    id: str
    centro: Punto
    dx: float  # m
    dy: float  # m
    tipo: str = "confinamiento"  # o "aislada"


@dataclass
class Viga:
    id: str
    inicio: Punto
    fin: Punto
    b: float
    h: float

    @property
    def luz(self) -> float:
        return _distancia(self.inicio, self.fin)


@dataclass
class Losa:
    inicio: Punto  # esquina
    fin: Punto  # esquina opuesta
    tipo: str  # "aligerado" o "maciza"
    h: float
    direccion: str  # dirección de las viguetas: "x" o "y"


@dataclass
class Hueco:
    inicio: Punto
    fin: Punto
    nombre: str = ""
    # Escaleras: carga en planta (tonf/m²) que se reparte por igual entre los muros de apoyo.
    carga_muerta: float = 0.0
    carga_viva: float = 0.0
    apoyos: list[str] = field(default_factory=list)  # ids de paños de muro o de vigas
    escalera: dict = field(default_factory=dict)  # descanso_m, paso_m, garganta_m (diseño E.060)

    @property
    def area(self) -> float:
        return abs(self.fin[0] - self.inicio[0]) * abs(self.fin[1] - self.inicio[1])


@dataclass
class Geometria:
    ejes_x: dict[str, float]
    ejes_y: dict[str, float]
    columnas: list[Columna] = field(default_factory=list)
    vigas: list[Viga] = field(default_factory=list)
    losas: list[Losa] = field(default_factory=list)
    huecos: list[Hueco] = field(default_factory=list)


def _distancia(a: Punto, b: Punto) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def resolver_punto(valor, ejes_x: dict[str, float], ejes_y: dict[str, float]) -> Punto:
    if not isinstance(valor, (list, tuple)) or len(valor) != 2:
        raise ValueError(f"Punto inválido {valor!r}: use [eje_x, eje_y] o [x, y].")

    def coord(v, ejes, nombre):
        # Un entero que coincide con el nombre de un eje (p. ej. 1) se toma como eje;
        # para una coordenada en esa posición escriba 1.0.
        if isinstance(v, int) and not isinstance(v, bool) and str(v) in ejes:
            return ejes[str(v)]
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return float(v)
        clave = str(v)
        if clave not in ejes:
            raise ValueError(f"Eje {nombre} {clave!r} no definido; ejes: {', '.join(ejes)}.")
        return ejes[clave]

    return coord(valor[0], ejes_x, "x"), coord(valor[1], ejes_y, "y")


def direccion_segmento(inicio: Punto, fin: Punto) -> str:
    if abs(inicio[1] - fin[1]) < 1e-9 and abs(inicio[0] - fin[0]) > 1e-9:
        return "x"
    if abs(inicio[0] - fin[0]) < 1e-9 and abs(inicio[1] - fin[1]) > 1e-9:
        return "y"
    raise ValueError(f"El segmento {inicio}–{fin} debe ser paralelo a X o a Y.")


def leer_geometria(datos: dict) -> Geometria:
    ejes = datos.get("ejes") or {}
    ejes_x = {str(k): float(v) for k, v in (ejes.get("x") or {}).items()}
    ejes_y = {str(k): float(v) for k, v in (ejes.get("y") or {}).items()}

    def p(v):
        return resolver_punto(v, ejes_x, ejes_y)

    geo = Geometria(ejes_x, ejes_y)
    for c in datos.get("columnas") or []:
        geo.columnas.append(
            Columna(str(c["id"]), p(c["en"]), float(c["dx_m"]), float(c["dy_m"]), c.get("tipo", "aislada"))
        )
    for v in datos.get("vigas") or []:
        inicio, fin = p(v["desde"]), p(v["hasta"])
        direccion_segmento(inicio, fin)
        geo.vigas.append(Viga(str(v["id"]), inicio, fin, float(v["b_m"]), float(v["h_m"])))
    for losa in datos.get("losas") or []:
        geo.losas.append(
            Losa(
                p(losa["desde"]),
                p(losa["hasta"]),
                losa.get("tipo", "aligerado"),
                float(losa["h_m"]),
                str(losa.get("direccion", "x")).lower(),
            )
        )
    for h in datos.get("huecos") or []:
        geo.huecos.append(
            Hueco(
                p(h["desde"]),
                p(h["hasta"]),
                h.get("nombre", ""),
                float(h.get("carga_muerta_tonf_m2", 0.0)),
                float(h.get("carga_viva_tonf_m2", 0.0)),
                [str(a) for a in h.get("apoyos") or []],
                dict(h.get("escalera") or {}),
            )
        )
    return geo


def columnas_confinamiento(muros: list[Muro]) -> list[Columna]:
    """Columnas en los extremos de los muros de albañilería, una por nodo y orientación."""
    vistas: set[tuple[float, float, str]] = set()
    columnas = []
    for m in muros:
        if m.material != "albanileria" or m.inicio is None or m.fin is None:
            continue
        for nodo in (m.inicio, m.fin):
            clave = (round(nodo[0], 3), round(nodo[1], 3), m.direccion)
            if clave in vistas:
                continue
            vistas.add(clave)
            if m.direccion == "x":
                dx, dy = LADO_COLUMNA_CONFINAMIENTO, m.espesor
            else:
                dx, dy = m.espesor, LADO_COLUMNA_CONFINAMIENTO
            columnas.append(Columna("C-1", nodo, dx, dy))
    return columnas


def luz_libre_losa(losa: Losa) -> float:
    """Luz entre ejes de apoyo en la dirección de las viguetas (aproximación a la luz libre)."""
    if losa.direccion == "x":
        return abs(losa.fin[0] - losa.inicio[0])
    return abs(losa.fin[1] - losa.inicio[1])
