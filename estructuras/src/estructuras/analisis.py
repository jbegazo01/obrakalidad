"""Cálculos sobre la ficha del proyecto: análisis sísmico estático y densidad de muros."""

from dataclasses import dataclass

from .normas import e030, e060, e070
from .proyecto import Ficha


@dataclass
class Direccion:
    eje: str
    sistema: e030.Sistema
    Ia: float
    Ip: float
    R: float
    CT: float | None
    T: float
    C: float
    cortante: e030.CortanteBasal
    fuerzas: list[float]  # tonf por nivel, de abajo hacia arriba
    excentricidad: float | None
    factor_desplazamiento: float
    deriva_max: float


@dataclass
class ResultadoSismico:
    sitio: e030.ParametrosSitio
    U: float
    pesos: list[float]  # tonf por nivel
    alturas: list[float]  # m, cota de cada nivel desde la base
    direcciones: list[Direccion]
    estatico_aplicable: bool
    separacion_minima: float
    coef_sismo_vertical: float

    @property
    def peso_total(self) -> float:
        return sum(self.pesos)


def pesos_sismicos(ficha: Ficha) -> list[float]:
    """Peso por nivel según el art. 31: CM + fracción de la CV, o el peso dado en la ficha."""
    return [
        n.peso
        if n.peso is not None
        else n.area * (n.carga_muerta + e030.fraccion_carga_viva(ficha.categoria, n.azotea) * n.carga_viva)
        for n in ficha.niveles
    ]


def cotas(ficha: Ficha) -> list[float]:
    resultado, h = [], 0.0
    for n in ficha.niveles:
        h += n.altura_entrepiso
        resultado.append(h)
    return resultado


def analisis_estatico(ficha: Ficha, pesos: list[float] | None = None) -> ResultadoSismico:
    """Análisis estático E.030. `pesos` (tonf por nivel) reemplaza a la estimación de la ficha,
    p. ej. con los pesos del metrado."""
    sitio = e030.parametros_sitio(ficha.zona, ficha.perfil_suelo, ficha.vs30)
    U = e030.factor_uso(ficha.categoria, ficha.zona, ficha.aislamiento)
    Ia, Ip = e030.factores_irregularidad(ficha.irregularidades)
    pesos = pesos if pesos is not None else pesos_sismicos(ficha)
    alturas = cotas(ficha)
    P = sum(pesos)
    hn = ficha.altura_total

    direcciones = []
    for eje, clave, ct, periodo, dim_perp in (
        ("X", ficha.sistema_x, ficha.ct_x, ficha.periodo_x, ficha.dimension_y),
        ("Y", ficha.sistema_y, ficha.ct_y, ficha.periodo_y, ficha.dimension_x),
    ):
        s = e030.sistema(clave)
        CT = ct or s.CT
        if CT is None and periodo is None:
            raise ValueError(f"Dirección {eje}: indique 'estructura.ct_{eje.lower()}' para {s.nombre}.")
        R = e030.coeficiente_R(s.R0, Ia, Ip)
        T = periodo if periodo is not None else e030.periodo_fundamental(hn, CT)
        C = e030.factor_C_estatico(T, sitio.TP, sitio.TL)
        cortante = e030.cortante_basal(sitio.Z, U, C, sitio.S, R, P)
        direcciones.append(
            Direccion(
                eje=eje,
                sistema=s,
                Ia=Ia,
                Ip=Ip,
                R=R,
                CT=CT,
                T=T,
                C=C,
                cortante=cortante,
                fuerzas=e030.distribucion_en_altura(pesos, alturas, cortante.V, T),
                excentricidad=e030.excentricidad_accidental(dim_perp) if dim_perp else None,
                factor_desplazamiento=e030.factor_desplazamiento(R, ficha.regular),
                deriva_max=s.deriva_max,
            )
        )

    return ResultadoSismico(
        sitio=sitio,
        U=U,
        pesos=pesos,
        alturas=alturas,
        direcciones=direcciones,
        estatico_aplicable=e030.estatico_aplicable(
            ficha.zona, ficha.regular, hn, [d.sistema for d in direcciones]
        ),
        separacion_minima=e030.separacion_minima(sitio.Z, sitio.S, hn),
        coef_sismo_vertical=e030.coeficiente_sismo_vertical(sitio.Z, U, sitio.S),
    )


@dataclass
class DensidadDireccion:
    eje: str
    area_muros: float  # Σ L·t, m²
    densidad: float
    requerida: float

    @property
    def cumple(self) -> bool:
        return self.densidad >= self.requerida


@dataclass
class ResultadoDensidad:
    area_planta: float
    Ec_sobre_Em: float
    espesor_minimo: float
    muros_delgados: list[str]
    muros_cortos: list[str]
    direcciones: list[DensidadDireccion]


def verificar_densidad(ficha: Ficha) -> ResultadoDensidad:
    """E.070 art. 19: densidad mínima de muros y espesor efectivo mínimo, en el primer piso."""
    if ficha.unidad_albanileria is None:
        raise ValueError("Falta 'materiales.unidad_albanileria'.")
    if not ficha.muros:
        raise ValueError("La ficha no tiene muros en 'muros'.")
    sitio = e030.parametros_sitio(ficha.zona, ficha.perfil_suelo, ficha.vs30)
    U = e030.factor_uso(ficha.categoria, ficha.zona, ficha.aislamiento)
    unidad = e070.unidad(ficha.unidad_albanileria)
    Ec_sobre_Em = e060.modulo_elasticidad(ficha.fc) / e070.modulo_elasticidad(unidad.fm)
    area = ficha.niveles[0].area
    if area is None:
        raise ValueError("Falta 'area_m2' del primer nivel.")
    requerida = e070.densidad_requerida(sitio.Z, U, sitio.S, ficha.n_pisos)
    # La altura libre del muro se aproxima con la altura de entrepiso del primer piso.
    t_min = e070.espesor_minimo(ficha.niveles[0].altura_entrepiso, ficha.zona)

    direcciones = []
    for eje in ("x", "y"):
        densidad = e070.densidad_muros(ficha.muros, eje, area, Ec_sobre_Em)
        direcciones.append(DensidadDireccion(eje.upper(), densidad * area, densidad, requerida))

    return ResultadoDensidad(
        area_planta=area,
        Ec_sobre_Em=Ec_sobre_Em,
        espesor_minimo=t_min,
        muros_delgados=[
            m.id for m in ficha.muros if m.material == "albanileria" and m.espesor < t_min - 1e-9
        ],
        muros_cortos=[m.id for m in ficha.muros if m.longitud <= e070.LONGITUD_MINIMA_MURO],
        direcciones=direcciones,
    )
