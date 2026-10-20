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
from dataclasses import dataclass

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
                and all(v.q_max <= INCREMENTO_SISMO * self.q_neta + 1e-9 and v.q_min >= 0 for v in self.sismo))


def _arriba(x: float, paso: float) -> float:
    return round(math.ceil(x / paso - 1e-9) * paso, 3)


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
    if any(c.tipo == "placa" for c in cimientos):
        observaciones.append("Cimientos de placas: ancho preliminar; unirlos a la retícula de cimientos corridos "
                             "y diseñar su refuerzo con la E.060.")
    return ResultadoCimentacion(q_adm, q_neta, op, cimientos, sismo, observaciones)


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
