"""Cimentación superficial de edificios de muros (E.050, E.060 y práctica usual).

- Cimientos corridos de concreto ciclópeo bajo muros: ancho para las cargas de servicio con
  la capacidad portante neta.
- Sismo: los cimientos corridos forman una retícula continua que resiste el momento de
  volteo en conjunto. Se verifica la presión en las esquinas de la retícula con P (D + L) y el
  momento del sismo moderado (E.070 art. 25.1), combinación 100 % + 30 %, admitiendo un
  incremento del 30 % en la capacidad portante y sin tracciones.
- Bajo placas el cimiento se ensancha (mínimo 0,80 m) y se une a la retícula; su refuerzo y
  el de las zapatas aisladas se diseñan con la E.060.
Unidades: tonf, m.
"""

import math
from dataclasses import dataclass, field

from .albanileria import ResultadoAlbanileria, gravedad_muro

INCREMENTO_SISMO = 1.30


@dataclass
class OpcionesCimentacion:
    df: float = 1.00  # m, profundidad de cimentación
    h_cimiento: float = 0.80  # m
    h_sobrecimiento: float = 0.40  # m
    gamma_promedio: float = 2.0  # tonf/m³, suelo + concreto sobre el fondo
    ancho_minimo: float = 0.40  # m
    paso: float = 0.05  # m, redondeo de dimensiones
    linderos: tuple[str, ...] = ()  # ejes sobre el límite de propiedad: cimientos excéntricos

    @classmethod
    def desde_ficha(cls, datos: dict) -> "OpcionesCimentacion":
        return cls(
            df=datos.get("df_m", 1.00),
            h_cimiento=datos.get("h_cimiento_m", 0.80),
            h_sobrecimiento=datos.get("h_sobrecimiento_m", 0.40),
            gamma_promedio=datos.get("gamma_promedio_tonf_m3", 2.0),
            ancho_minimo=datos.get("ancho_minimo_m", 0.40),
            linderos=tuple(str(e) for e in datos.get("linderos") or ()),
        )


@dataclass
class Cimiento:
    elemento: str
    tipo: str  # "corrido", "placa" o "aislada"
    centro: tuple[float, float]
    direccion: str  # "x" o "y" (zapatas aisladas: "x")
    largo: float  # m, en la dirección del elemento
    ancho: float  # m
    peralte: float  # m
    P: float  # tonf, carga de servicio D + L
    q_servicio: float  # tonf/m²
    excentrico: bool = False  # cimiento en lindero, desplazado hacia el interior del lote
    componentes: list[str] = field(default_factory=list)  # elementos de un cimiento combinado
    M_sismo: float = 0.0  # tonf·m, momento del sismo moderado en el plano del cimiento combinado
    q_sismo: float = 0.0  # tonf/m², presión máxima con sismo

    @property
    def area(self) -> float:
        return self.largo * self.ancho

    def dimensiones_xy(self) -> tuple[float, float]:
        return (self.largo, self.ancho) if self.direccion == "x" else (self.ancho, self.largo)


@dataclass
class VerificacionSismo:
    direccion: str
    P: float
    M: float  # tonf·m, momento de volteo del sismo moderado en la dirección principal
    q_max: float
    q_min: float


@dataclass
class ResultadoCimentacion:
    q_admisible: float  # tonf/m²
    q_neta: float
    opciones: OpcionesCimentacion
    cimientos: list[Cimiento]
    sismo: list[VerificacionSismo]
    observaciones: list[str]

    @property
    def cumple(self) -> bool:
        return (all(c.q_servicio <= self.q_neta + 1e-9 for c in self.cimientos)
                and all(c.q_sismo <= INCREMENTO_SISMO * self.q_neta + 1e-9 for c in self.cimientos)
                and all(v.q_max <= INCREMENTO_SISMO * self.q_neta + 1e-9 and v.q_min >= 0 for v in self.sismo))


def _arriba(x: float, paso: float) -> float:
    return round(math.ceil(x / paso - 1e-9) * paso, 3)


def presion_maxima(P: float, M: float, B: float, L: float) -> float:
    """Presión máxima bajo una zapata B × L con momento en la dirección de L: distribución
    trapezoidal, o triangular si la excentricidad supera L/6 (infinito si e ≥ L/2)."""
    e = abs(M) / P if P > 0 else float("inf")
    if e <= L / 6:
        return P / (B * L) * (1 + 6 * e / L)
    if e >= L / 2:
        return float("inf")
    return 2 * P / (3 * B * (L / 2 - e))


def disenar(res: ResultadoAlbanileria, opciones: OpcionesCimentacion | None = None) -> ResultadoCimentacion:
    ficha = res.ficha
    op = opciones or OpcionesCimentacion.desde_ficha(ficha.cimentacion)
    if ficha.capacidad_portante is None:
        raise ValueError("Falta la capacidad portante del EMS (sitio.capacidad_portante_kgf_cm2).")
    q_adm = ficha.capacidad_portante * 10
    q_neta = q_adm - op.gamma_promedio * op.df
    observaciones = []
    if ficha.capacidad_portante_supuesta:
        observaciones.append(
            f"La capacidad portante de {ficha.capacidad_portante:g} kgf/cm² es un SUPUESTO; "
            "las dimensiones deben revisarse con el EMS."
        )

    geo = ficha.geometria
    lineas_lindero = []
    for nombre in op.linderos:
        if nombre in geo.ejes_x:
            lineas_lindero.append(("y", geo.ejes_x[nombre]))
        elif nombre in geo.ejes_y:
            lineas_lindero.append(("x", geo.ejes_y[nombre]))
        else:
            raise ValueError(f"cimentacion.linderos: eje {nombre!r} no definido.")
    centro_planta = (sum(geo.ejes_x.values()) / len(geo.ejes_x), sum(geo.ejes_y.values()) / len(geo.ejes_y))

    cimientos = []
    for w in res.muros:
        _, L_v, D_base, _ = gravedad_muro(w, res.metrado, 1)
        P = D_base + L_v
        B = _arriba(max(P / w.L / q_neta, op.ancho_minimo, w.espesor + 0.20), op.paso)
        tipo = "corrido"
        if w.material == "concreto":
            B, tipo = max(B, 0.80), "placa"
        centro = w.centro
        excentrico = any(d == w.direccion and abs(v - w.linea) < 1e-6 for d, v in lineas_lindero)
        if excentrico:
            # La cara exterior del cimiento coincide con la cara exterior del muro.
            hacia_dentro = 1 if w.linea < (centro_planta[1] if w.direccion == "x" else centro_planta[0]) else -1
            desplazamiento = hacia_dentro * (B / 2 - w.espesor / 2)
            centro = ((centro[0], centro[1] + desplazamiento) if w.direccion == "x"
                      else (centro[0] + desplazamiento, centro[1]))
        cimientos.append(Cimiento(w.id, tipo, centro, w.direccion, w.L, B, op.h_cimiento, P, P / (B * w.L),
                                  excentrico))
    if any(c.excentrico for c in cimientos):
        observaciones.append("Cimientos en linderos excéntricos (hacia el interior del lote); su excentricidad "
                             "se equilibra con la retícula de cimientos y los muros transversales.")

    for c in ficha.geometria.columnas:
        P = sum(x.D + x.L for x in res.metrado.columnas[c.id])
        lado = max(_arriba(math.sqrt(P / q_neta), op.paso), 0.80)
        cimientos.append(Cimiento(c.id, "aislada", c.centro, "x", lado, lado, 0.50, P, P / lado**2))

    cimientos = _combinar_placas(res, cimientos, q_neta, op, observaciones)

    sismo = verificar_sismo(res, cimientos)
    for c in cimientos:
        if c.q_servicio > q_neta + 1e-9:
            observaciones.append(f"NO CUMPLE: presión de servicio en {c.elemento} ({c.q_servicio:.1f} > {q_neta:.1f} tonf/m²).")
    for v in sismo:
        if v.q_max > INCREMENTO_SISMO * q_neta + 1e-9:
            observaciones.append(f"NO CUMPLE: presión con sismo en {v.direccion} ({v.q_max:.1f} > "
                                 f"{INCREMENTO_SISMO * q_neta:.1f} tonf/m²).")
        if v.q_min < 0:
            observaciones.append(f"NO CUMPLE: tracción en la cimentación con sismo en {v.direccion} "
                                 f"(q mín = {v.q_min:.1f} tonf/m²).")
    return ResultadoCimentacion(q_adm, q_neta, op, cimientos, sismo, observaciones)


def _carga_alas(res: ResultadoAlbanileria, ids: list[str]) -> float:
    from .muros import alas
    from .normas import e060, e070

    Ec_sobre_Em = e060.modulo_elasticidad(res.ficha.fc) / e070.modulo_elasticidad(
        e070.unidad(res.ficha.unidad_albanileria).fm)
    total = 0.0
    vistos = set()
    for i in ids:
        w = res.muro(i)
        for ala in alas(w, res.muros, Ec_sobre_Em):
            clave = (ala.muro, round(ala.posicion, 3), ala.lado)
            if clave in vistos:
                continue
            vistos.add(clave)
            t = res.muro(ala.muro)
            _, L_v, D_base, _ = gravedad_muro(t, res.metrado, 1)
            total += (D_base + L_v) / t.L * ala.ancho
    return total


def _combinar_placas(res: ResultadoAlbanileria, cimientos: list[Cimiento], q_neta: float,
                     op: OpcionesCimentacion, observaciones: list[str]) -> list[Cimiento]:
    """Las placas no pueden equilibrar su momento sísmico con un cimiento propio (poca carga
    axial). En cada eje con placas se forma un cimiento combinado continuo que une las placas,
    las columnas aisladas y los muros de ese eje, dimensionado con la carga total y la suma de
    los momentos de las placas (sismo moderado), con +30 % de capacidad (E.060 15.2.4)."""
    placas = [c for c in cimientos if c.tipo == "placa"]
    if not placas:
        return cimientos
    usados: set[int] = set()
    nuevos = []
    for k, pl in enumerate(placas, start=1):
        if id(pl) in usados:
            continue
        d = pl.direccion
        linea = pl.centro[1] if d == "x" else pl.centro[0]
        en_linea = [c for c in cimientos
                    if c.tipo in ("placa", "aislada", "corrido") and id(c) not in usados
                    and abs((c.centro[1] if d == "x" else c.centro[0]) - linea) < 1e-6
                    and (c.tipo == "aislada" or c.direccion == d)]
        a = min((c.centro[0] if d == "x" else c.centro[1]) - (c.largo / 2 if c.tipo != "aislada" else c.ancho / 2)
                for c in en_linea)
        b = max((c.centro[0] if d == "x" else c.centro[1]) + (c.largo / 2 if c.tipo != "aislada" else c.ancho / 2)
                for c in en_linea)
        largo = b - a
        P = sum(c.P for c in en_linea)
        # Los muros transversales monolíticos con los extremos del cimiento aportan su carga
        # sobre el ancho de ala del art. 24.6 de la E.070 (25 % de su longitud o 6t).
        P += _carga_alas(res, [c.elemento for c in en_linea if c.tipo != "aislada"])
        M = sum(res.modelo.combinar(c.elemento).M[0] / 2 for c in en_linea if c.tipo == "placa")
        B = max(c.ancho for c in en_linea)
        while (presion_maxima(P, M, B, largo) > INCREMENTO_SISMO * q_neta or P / (B * largo) > q_neta) and B < 3.0:
            B = round(B + op.paso, 3)
        centro = ((a + b) / 2, linea) if d == "x" else (linea, (a + b) / 2)
        nombre = f"ZC-{len(nuevos) + 1}"
        if presion_maxima(P, M, B, largo) > INCREMENTO_SISMO * q_neta:
            observaciones.append(f"NO CUMPLE: {nombre} no equilibra el momento de las placas con B ≤ 3 m; "
                                 "alargar las placas o unirlas con vigas de cimentación a otros muros.")
        nuevos.append(Cimiento(nombre, "combinado", centro, d, largo, B, 0.60, P, P / (B * largo),
                               componentes=[c.elemento for c in en_linea], M_sismo=M,
                               q_sismo=presion_maxima(P, M, B, largo)))
        usados |= {id(c) for c in en_linea}
        observaciones.append(
            f"{nombre}: cimiento combinado de concreto armado en el eje de {', '.join(c.elemento for c in en_linea)} "
            f"(B = {B:.2f} m, L = {largo:.2f} m) para el momento de las placas (M = {M:.1f} tonf·m)."
        )
    return [c for c in cimientos if id(c) not in usados] + nuevos


def verificar_sismo(res: ResultadoAlbanileria, cimientos: list[Cimiento]) -> list[VerificacionSismo]:
    """Presiones en las esquinas de la retícula de cimientos con el momento de volteo del
    sismo moderado (100 % en una dirección + 30 % en la otra)."""
    A = sum(c.area for c in cimientos)
    xc = sum(c.area * c.centro[0] for c in cimientos) / A
    yc = sum(c.area * c.centro[1] for c in cimientos) / A
    Ix = Iy = 0.0  # inercias respecto de ejes paralelos a X e Y por el centroide
    xs, ys = [], []
    for c in cimientos:
        dx, dy = c.dimensiones_xy()
        Ix += dx * dy**3 / 12 + dx * dy * (c.centro[1] - yc) ** 2
        Iy += dy * dx**3 / 12 + dx * dy * (c.centro[0] - xc) ** 2
        xs += [c.centro[0] - dx / 2, c.centro[0] + dx / 2]
        ys += [c.centro[1] - dy / 2, c.centro[1] + dy / 2]
    P = sum(c.P for c in cimientos)
    # Momento de volteo del sismo moderado en el fondo de la cimentación.
    df = res.ficha.cimentacion.get("df_m", 1.0)
    M = sum(f / 2 * (h + df) for f, h in zip(res.fuerzas, res.modelo.alturas))
    resultado = []
    for direccion, Mp, Mo in (("X", M, 0.3 * M), ("Y", 0.3 * M, M)):
        # Sismo en X produce momento alrededor de Y (varía con x); en Y, alrededor de X.
        q = [P / A + Mp * abs(x - xc) / Iy + Mo * abs(y - yc) / Ix for x in (min(xs), max(xs)) for y in (min(ys), max(ys))]
        q_min = [P / A - Mp * abs(x - xc) / Iy - Mo * abs(y - yc) / Ix for x in (min(xs), max(xs)) for y in (min(ys), max(ys))]
        resultado.append(VerificacionSismo(direccion, P, M, max(q), min(q_min)))
    return resultado
