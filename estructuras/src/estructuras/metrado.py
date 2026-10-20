"""Metrado de cargas de gravedad por paño de muro, columna y nivel (E.020).

Criterios (E.070 art. 24.1 permite "cualquier método racional"):
- Losa aligerada en una dirección: la carga va a los apoyos perpendiculares a las viguetas
  (muros y vigas), mitad a cada lado del paño. Los muros y vigas paralelos a las viguetas
  reciben una franja de losa (por defecto 4 veces el espesor de la losa, repartida a ambos
  lados) que se descuenta de la carga de los apoyos principales.
- Losa maciza: igual que el aligerado, en la dirección indicada.
- Vigas: simplemente apoyadas; sus reacciones bajan como cargas puntuales a muros,
  columnas u otras vigas.
- Escaleras (huecos con carga): mitad de la carga a cada muro de apoyo indicado.
- Peso propio de muros por entrepiso, con tarrajeo en ambas caras.
Unidades: tonf, m.
"""

from dataclasses import dataclass, field

from .geometria import Geometria, Losa, Viga
from .normas import e020, e030
from .normas.e070 import Muro
from .proyecto import Ficha

TOL = 1e-6
G_CONCRETO = 2.4


@dataclass
class OpcionesMetrado:
    piso_terminado: float = 0.10  # tonf/m²
    tabiqueria: float = 0.10  # tonf/m², tabiquería repartida equivalente (no en azotea)
    acabados_azotea: float = 0.10  # tonf/m²
    sobrecarga: float = 0.20  # tonf/m², E.020 vivienda
    sobrecarga_azotea: float = 0.10  # tonf/m², E.020 techos
    peso_albanileria: float = 1.80  # tonf/m³, E.020 Anexo 1 (unidades sólidas)
    tarrajeo: float = 0.02  # m por cara
    peso_mortero: float = 2.00  # tonf/m³
    franja_paralela: float | None = None  # m; None = 4 × espesor de losa

    @classmethod
    def desde_ficha(cls, ficha: Ficha) -> "OpcionesMetrado":
        c = ficha.cargas
        uso = c.get("uso_sobrecarga") or ficha.uso or "vivienda"
        sobrecarga = c.get("sobrecarga_tonf_m2")
        if sobrecarga is None:
            sobrecarga = e020.carga_viva(uso) if uso in e020.CARGAS_VIVAS else 0.20
        return cls(
            piso_terminado=c.get("piso_terminado_tonf_m2", 0.10),
            tabiqueria=c.get("tabiqueria_tonf_m2", 0.10),
            acabados_azotea=c.get("acabados_azotea_tonf_m2", 0.10),
            sobrecarga=sobrecarga,
            sobrecarga_azotea=c.get("sobrecarga_azotea_tonf_m2", e020.carga_viva("techo")),
            peso_albanileria=c.get("peso_albanileria_tonf_m3", 1.80),
            tarrajeo=c.get("tarrajeo_m", 0.02),
            peso_mortero=c.get("peso_mortero_tonf_m3", 2.00),
            franja_paralela=c.get("franja_muros_paralelos_m"),
        )


@dataclass
class Carga:
    D: float = 0.0
    L: float = 0.0

    def __iadd__(self, o: "Carga"):
        self.D += o.D
        self.L += o.L
        return self

    def __add__(self, o: "Carga") -> "Carga":
        return Carga(self.D + o.D, self.L + o.L)

    def escalar(self, f: float) -> "Carga":
        return Carga(self.D * f, self.L * f)


@dataclass
class CargaPuntual:
    punto: tuple[float, float]
    carga: Carga


@dataclass
class Metrado:
    n: int  # número de niveles
    # Carga repartida que llega a cada paño en cada nivel (losa, franjas, escaleras).
    panos: dict[str, list[Carga]]
    # Cargas puntuales (reacciones de vigas) sobre cada paño, por nivel.
    puntuales: dict[str, list[list[CargaPuntual]]]
    # Peso propio de cada paño en cada entrepiso (tonf).
    peso_propio: dict[str, list[float]]
    # Cargas sobre columnas aisladas, por nivel.
    columnas: dict[str, list[Carga]]
    # Peso sísmico (D + fracción de L) y centro de masas de cada nivel.
    pesos_sismicos: list[float]
    centros_masa: list[tuple[float, float]]
    advertencias: list[str] = field(default_factory=list)
    # Cargas de cada viga por nivel: (carga repartida total con peso propio, [(s, carga puntual)]).
    vigas: dict[str, list[tuple[Carga, list[tuple[float, Carga]]]]] = field(default_factory=dict)

    def total_pano(self, pano: str, nivel: int) -> Carga:
        """Carga en el nivel (repartida + puntuales) sin peso propio."""
        c = Carga(self.panos[pano][nivel].D, self.panos[pano][nivel].L)
        for p in self.puntuales[pano][nivel]:
            c += p.carga
        return c


def _peso_losa(losa: Losa) -> float:
    if losa.tipo == "aligerado":
        return e020.peso_aligerado(losa.h)
    return losa.h * G_CONCRETO


def peso_muro_m2(m: Muro, op: OpcionesMetrado) -> float:
    """Peso por m² de muro, con tarrajeo en ambas caras."""
    gamma = G_CONCRETO if m.material == "concreto" else op.peso_albanileria
    return m.espesor * gamma + 2 * op.tarrajeo * op.peso_mortero


def _solape(a0, a1, b0, b1) -> float:
    return max(0.0, min(a1, b1) - max(a0, b0))


class _Acumulador:
    """Reparte cargas de un nivel sobre paños, vigas y columnas."""

    def __init__(self, muros: list[Muro], geo: Geometria):
        self.muros = muros
        self.geo = geo
        self.panos: dict[str, Carga] = {m.id: Carga() for m in muros}
        self.puntuales: dict[str, list[CargaPuntual]] = {m.id: [] for m in muros}
        self.vigas_rep: dict[str, Carga] = {v.id: Carga() for v in geo.vigas}
        self.vigas_punt: dict[str, list[tuple[float, Carga]]] = {v.id: [] for v in geo.vigas}
        self.columnas: dict[str, Carga] = {c.id: Carga() for c in geo.columnas}
        self.advertencias: list[str] = []

    # --- elementos sobre una línea ---
    def elementos_en_linea(self, direccion: str, linea: float, s0: float, s1: float):
        """Paños de muro y vigas con dirección dada sobre la línea, con su solape en [s0, s1]."""
        res = []
        for m in self.muros:
            if m.direccion != direccion:
                continue
            fija = m.inicio[1] if direccion == "x" else m.inicio[0]
            if abs(fija - linea) > TOL:
                continue
            a, b = sorted((m.inicio[0], m.fin[0]) if direccion == "x" else (m.inicio[1], m.fin[1]))
            sol = _solape(a, b, s0, s1)
            if sol > TOL:
                res.append(("muro", m.id, sol))
        for v in self.geo.vigas:
            dv = "x" if abs(v.inicio[1] - v.fin[1]) < TOL else "y"
            if dv != direccion:
                continue
            fija = v.inicio[1] if direccion == "x" else v.inicio[0]
            if abs(fija - linea) > TOL:
                continue
            a, b = sorted((v.inicio[0], v.fin[0]) if direccion == "x" else (v.inicio[1], v.fin[1]))
            sol = _solape(a, b, s0, s1)
            if sol > TOL:
                res.append(("viga", v.id, sol))
        return res

    def repartir_en_linea(self, direccion, linea, s0, s1, carga: Carga, descripcion: str):
        """Carga uniforme a lo largo de [s0, s1] sobre la línea, a muros y vigas que la cubren."""
        elementos = self.elementos_en_linea(direccion, linea, s0, s1)
        cubierto = sum(e[2] for e in elementos)
        if cubierto < TOL:
            self.advertencias.append(f"{descripcion}: no hay muro ni viga de apoyo; carga no asignada.")
            return
        if cubierto < (s1 - s0) - 1e-3:
            self.advertencias.append(
                f"{descripcion}: el apoyo cubre {cubierto:.2f} de {s1 - s0:.2f} m; "
                "la carga se reparte entre los elementos existentes."
            )
        for tipo, id_, sol in elementos:
            parte = carga.escalar(sol / cubierto)
            if tipo == "muro":
                self.panos[id_] += parte
            else:
                self.vigas_rep[id_] += parte

    # --- cargas puntuales en nodos ---
    def carga_en_punto(self, punto, carga: Carga, origen: str):
        """Asigna una carga puntual al elemento que la soporta en ese punto."""
        for c in self.geo.columnas:
            if abs(c.centro[0] - punto[0]) < TOL and abs(c.centro[1] - punto[1]) < TOL:
                self.columnas[c.id] += carga
                return
        soportes = [m for m in self.muros if _contiene(m, punto)]
        if soportes:
            for m in soportes:
                self.puntuales[m.id].append(CargaPuntual(punto, carga.escalar(1 / len(soportes))))
            return
        for v in self.geo.vigas:
            if v.id != origen and _contiene_viga(v, punto):
                s = _dist(v.inicio, punto)
                self.vigas_punt[v.id].append((s, carga))
                return
        self.advertencias.append(f"Reacción de {origen} en {punto}: sin apoyo; carga no asignada.")

    def resolver_vigas(self, peso_vigas: dict[str, float]):
        """Reacciones de vigas simplemente apoyadas, de las apoyadas a las de apoyo."""
        pendientes = {v.id: v for v in self.geo.vigas}
        for _ in range(len(pendientes) + 1):
            if not pendientes:
                return
            for vid, v in list(pendientes.items()):
                # Una viga se resuelve cuando ninguna viga pendiente descarga sobre ella.
                if any(_apoya_en(o, v) for oid, o in pendientes.items() if oid != vid):
                    continue
                total = self.vigas_rep[vid] + Carga(peso_vigas[vid], 0.0)
                ra, rb = total.escalar(0.5), total.escalar(0.5)
                for s, p in self.vigas_punt[vid]:
                    f = s / v.luz
                    ra += p.escalar(1 - f)
                    rb += p.escalar(f)
                self.carga_en_punto(v.inicio, ra, vid)
                self.carga_en_punto(v.fin, rb, vid)
                del pendientes[vid]
        self.advertencias.append(f"Vigas con apoyos circulares: {', '.join(pendientes)}.")


def _dist(a, b) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5


def _contiene(m: Muro, p) -> bool:
    (x1, y1), (x2, y2) = m.inicio, m.fin
    if m.direccion == "x":
        return abs(p[1] - y1) < TOL and min(x1, x2) - TOL <= p[0] <= max(x1, x2) + TOL
    return abs(p[0] - x1) < TOL and min(y1, y2) - TOL <= p[1] <= max(y1, y2) + TOL


def _contiene_viga(v: Viga, p) -> bool:
    """True si el punto cae en el interior de la viga (sin contar sus extremos, que son apoyos
    compartidos con las vigas que llegan al mismo nudo)."""
    (x1, y1), (x2, y2) = v.inicio, v.fin
    if abs(y1 - y2) < TOL:
        return abs(p[1] - y1) < TOL and min(x1, x2) + TOL < p[0] < max(x1, x2) - TOL
    return abs(p[0] - x1) < TOL and min(y1, y2) + TOL < p[1] < max(y1, y2) - TOL


def _apoya_en(o: Viga, v: Viga) -> bool:
    """True si algún extremo de la viga o cae en el interior de la viga v."""
    return any(_contiene_viga(v, p) for p in (o.inicio, o.fin))


def _cargas_losa_por_m2(losa: Losa, azotea: bool, op: OpcionesMetrado) -> Carga:
    if azotea:
        return Carga(_peso_losa(losa) + op.acabados_azotea, op.sobrecarga_azotea)
    return Carga(_peso_losa(losa) + op.piso_terminado + op.tabiqueria, op.sobrecarga)


def _repartir_losa(acc: _Acumulador, losa: Losa, w: Carga, franja_total: float, idx: int):
    (x1, y1), (x2, y2) = losa.inicio, losa.fin
    x1, x2 = sorted((x1, x2))
    y1, y2 = sorted((y1, y2))
    # Dirección de apoyo principal = perpendicular a las viguetas.
    if losa.direccion == "x":
        luz, ancho = x2 - x1, y2 - y1
        apoyos = [("y", x1), ("y", x2)]
        paralela, p0, p1, b0, b1 = "x", x1, x2, y1, y2
    else:
        luz, ancho = y2 - y1, x2 - x1
        apoyos = [("x", y1), ("x", y2)]
        paralela, p0, p1, b0, b1 = "y", y1, y2, x1, x2
    area = luz * ancho
    nombre = f"Losa {idx}"

    # Franjas sobre muros y vigas paralelos a las viguetas (bordes e interiores).
    area_franjas = 0.0
    lineas = sorted(
        {round(m.inicio[1] if paralela == "x" else m.inicio[0], 6) for m in acc.muros if m.direccion == paralela}
        | {
            round(v.inicio[1] if paralela == "x" else v.inicio[0], 6)
            for v in acc.geo.vigas
            if (abs(v.inicio[1] - v.fin[1]) < TOL) == (paralela == "x")
        }
    )
    for linea in lineas:
        if linea < b0 - TOL or linea > b1 + TOL:
            continue
        en_borde = abs(linea - b0) < TOL or abs(linea - b1) < TOL
        b = franja_total / 2 if en_borde else franja_total
        for tipo, id_, sol in acc.elementos_en_linea(paralela, linea, p0, p1):
            carga = w.escalar(b * sol)
            area_franjas += b * sol
            if tipo == "muro":
                acc.panos[id_] += carga
            else:
                acc.vigas_rep[id_] += carga

    resto = max(area - area_franjas, 0.0)
    for direccion, linea in apoyos:
        acc.repartir_en_linea(direccion, linea, b0, b1, w.escalar(resto / 2), f"{nombre} (apoyo {linea:.2f})")


def metrar(ficha: Ficha, opciones: OpcionesMetrado | None = None) -> Metrado:
    geo = ficha.geometria
    if geo is None:
        raise ValueError("La ficha no tiene 'geometria'.")
    op = opciones or OpcionesMetrado.desde_ficha(ficha)
    n = ficha.n_pisos
    muros = ficha.muros
    if not geo.losas:
        raise ValueError("La geometría no tiene losas.")
    h_losa = max(l.h for l in geo.losas)
    franja = op.franja_paralela if op.franja_paralela is not None else 4 * h_losa
    ids_panos = {m.id for m in muros}

    panos = {m.id: [Carga() for _ in range(n)] for m in muros}
    puntuales: dict[str, list[list[CargaPuntual]]] = {m.id: [[] for _ in range(n)] for m in muros}
    columnas = {c.id: [Carga() for _ in range(n)] for c in geo.columnas}
    vigas: dict[str, list] = {v.id: [None] * n for v in geo.vigas}
    advertencias: list[str] = []
    pesos: list[float] = []
    centros: list[tuple[float, float]] = []

    peso_propio = {
        m.id: [peso_muro_m2(m, op) * (niv.altura_entrepiso - h_losa) * m.longitud for niv in ficha.niveles]
        for m in muros
    }

    for i, nivel in enumerate(ficha.niveles):
        acc = _Acumulador(muros, geo)
        beta = e030.fraccion_carga_viva(ficha.categoria, nivel.azotea)
        masa: list[tuple[float, float, float]] = []  # (peso sísmico, x, y)

        for k, losa in enumerate(geo.losas, start=1):
            w = _cargas_losa_por_m2(losa, nivel.azotea, op)
            _repartir_losa(acc, losa, w, franja, k)
            (x1, y1), (x2, y2) = losa.inicio, losa.fin
            area = abs(x2 - x1) * abs(y2 - y1)
            masa.append(((w.D + beta * w.L) * area, (x1 + x2) / 2, (y1 + y2) / 2))

        # Escaleras: su carga se reparte por igual entre sus apoyos (muros o vigas).
        ids_vigas = {v.id for v in geo.vigas}
        for h in geo.huecos:
            if not h.apoyos or (h.carga_muerta == 0 and h.carga_viva == 0):
                continue
            desconocidos = [a for a in h.apoyos if a not in ids_panos | ids_vigas]
            if desconocidos:
                raise ValueError(f"Hueco {h.nombre}: apoyos {', '.join(desconocidos)} no son muros ni vigas de la ficha.")
            total = Carga(h.carga_muerta * h.area, h.carga_viva * h.area)
            for a in h.apoyos:
                destino = acc.panos if a in ids_panos else acc.vigas_rep
                destino[a] += total.escalar(1 / len(h.apoyos))
            masa.append(((total.D + beta * total.L), (h.inicio[0] + h.fin[0]) / 2, (h.inicio[1] + h.fin[1]) / 2))

        peso_vigas = {}
        for v in geo.vigas:
            peso_vigas[v.id] = v.b * max(v.h - h_losa, 0.0) * G_CONCRETO * v.luz
            xm, ym = (v.inicio[0] + v.fin[0]) / 2, (v.inicio[1] + v.fin[1]) / 2
            masa.append((peso_vigas[v.id], xm, ym))
        acc.resolver_vigas(peso_vigas)
        for v in geo.vigas:
            # Carga de diseño de la viga: repartida total (con peso propio) y puntuales.
            vigas[v.id][i] = (acc.vigas_rep[v.id] + Carga(peso_vigas[v.id], 0.0), list(acc.vigas_punt[v.id]))

        # Muros: mitad del entrepiso inferior y mitad del superior.
        for m in muros:
            xm, ym = (m.inicio[0] + m.fin[0]) / 2, (m.inicio[1] + m.fin[1]) / 2
            mitad = peso_propio[m.id][i] / 2
            if i + 1 < n:
                mitad += peso_propio[m.id][i + 1] / 2
            masa.append((mitad, xm, ym))

        for mid in ids_panos:
            panos[mid][i] = acc.panos[mid]
            puntuales[mid][i] = acc.puntuales[mid]
        for c in geo.columnas:
            # Peso propio de la columna aislada del entrepiso que llega a este nivel.
            peso = c.dx * c.dy * (nivel.altura_entrepiso - h_losa) * G_CONCRETO
            acc.columnas[c.id] += Carga(peso, 0.0)
            masa.append((peso, *c.centro))
        for cid in columnas:
            columnas[cid][i] = acc.columnas[cid]
        advertencias += [f"Nivel {nivel.nombre}: {a}" for a in acc.advertencias]

        total = sum(p for p, _, _ in masa)
        pesos.append(total)
        centros.append((sum(p * x for p, x, _ in masa) / total, sum(p * y for p, _, y in masa) / total))

    return Metrado(n, panos, puntuales, peso_propio, columnas, pesos, centros, advertencias, vigas)
