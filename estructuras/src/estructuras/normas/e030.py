"""Norma Técnica E.030 Diseño Sismorresistente, texto modificado por R.M. N° 183-2026-VIVIENDA.

Cada función cita el artículo o la tabla de la norma que implementa. Unidades: tonf, m, s.
"""

from dataclasses import dataclass, field

VERSION = "2026"

# Tabla N° 1 (art. 11)
FACTOR_ZONA = {4: 0.45, 3: 0.35, 2: 0.25, 1: 0.10}

PERFILES = ("S0", "S1", "S2", "S3", "S4", "S5")

NOMBRE_PERFIL = {
    "S0": "Roca",
    "S1": "Suelos muy rígidos",
    "S2": "Suelos rígidos",
    "S3": "Suelos intermedios",
    "S4": "Suelos blandos",
    "S5": "Suelos excepcionales",
}

# Tabla N° 3: intervalo de Vs30 (m/s) de cada perfil, (mínimo, máximo).
VS30_PERFIL = {
    "S0": (800.0, None),
    "S1": (550.0, 800.0),
    "S2": (350.0, 550.0),
    "S3": (200.0, 350.0),
    "S4": (None, 200.0),
}

# Tabla N° 4. En S2 y S3 el valor es un intervalo (borde rígido, borde flexible) que se
# interpola con Vs30. None: requiere análisis de respuesta de sitio.
_FACTOR_S = {
    4: {"S0": 0.80, "S1": 1.00, "S2": (1.00, 1.10), "S3": (1.10, 1.20), "S4": None},
    3: {"S0": 0.80, "S1": 1.00, "S2": (1.00, 1.15), "S3": (1.15, 1.20), "S4": 1.30},
    2: {"S0": 0.80, "S1": 1.00, "S2": (1.00, 1.30), "S3": (1.30, 1.40), "S4": 1.70},
    1: {"S0": 0.80, "S1": 1.00, "S2": (1.00, 1.30), "S3": (1.30, 1.60), "S4": 2.40},
}

# Tabla N° 5, mismo criterio de intervalos (borde rígido, borde flexible).
_TP = {"S0": 0.3, "S1": 0.4, "S2": (0.4, 0.6), "S3": (0.6, 0.9), "S4": 1.2}
_TL = {"S0": 3.0, "S1": 2.5, "S2": (2.5, 2.0), "S3": (2.0, 1.6), "S4": 1.6}


@dataclass
class ParametrosSitio:
    zona: int
    Z: float
    perfil: str
    S: float
    TP: float
    TL: float
    vs30: float | None
    advertencias: list[str] = field(default_factory=list)


def _valor_tabla(valor, vs30: float | None, perfil: str) -> float:
    if not isinstance(valor, tuple):
        return valor
    rigido, flexible = valor
    if vs30 is None:
        # Nota (*) de las Tablas 4 y 5: sin Vs30 se toma el valor más desfavorable.
        return flexible
    vs_min, vs_max = VS30_PERFIL[perfil]
    t = (vs_max - vs30) / (vs_max - vs_min)
    return rigido + t * (flexible - rigido)


def parametros_sitio(zona: int, perfil: str, vs30: float | None = None) -> ParametrosSitio:
    """Factor Z (Tabla 1), S (Tabla 4), TP y TL (Tabla 5), art. 11 y 17."""
    if zona not in FACTOR_ZONA:
        raise ValueError(f"Zona sísmica {zona} no existe; debe ser 1, 2, 3 o 4.")
    if perfil not in PERFILES:
        raise ValueError(f"Perfil de suelo {perfil!r} no existe; use uno de {', '.join(PERFILES)}.")
    if perfil == "S5":
        raise ValueError(
            "Perfil S5 (suelos excepcionales): la norma prohíbe construir sin un estudio "
            "específico de sitio (Tabla 2). No se pueden obtener S, TP ni TL de las tablas."
        )
    if _FACTOR_S[zona][perfil] is None:
        raise ValueError("Suelo S4 en zona 4: la Tabla 4 exige un análisis de respuesta de sitio.")

    advertencias = []
    if vs30 is not None:
        vs_min, vs_max = VS30_PERFIL[perfil]
        if (vs_min is not None and vs30 < vs_min) or (vs_max is not None and vs30 >= vs_max):
            raise ValueError(
                f"Vs30 = {vs30:g} m/s no corresponde al perfil {perfil} según la Tabla 3."
            )
    elif perfil in ("S2", "S3"):
        advertencias.append(
            f"Sin Vs30 se usan los valores más desfavorables del intervalo del perfil {perfil} "
            "(nota de las Tablas 4 y 5)."
        )

    return ParametrosSitio(
        zona=zona,
        Z=FACTOR_ZONA[zona],
        perfil=perfil,
        S=_valor_tabla(_FACTOR_S[zona][perfil], vs30, perfil),
        TP=_valor_tabla(_TP[perfil], vs30, perfil),
        TL=_valor_tabla(_TL[perfil], vs30, perfil),
        vs30=vs30,
        advertencias=advertencias,
    )


def perfil_por_vs30(vs30: float) -> str:
    """Clasificación del perfil con la Tabla 3 a partir de Vs30 (m/s)."""
    for perfil, (vs_min, vs_max) in VS30_PERFIL.items():
        if (vs_min is None or vs30 >= vs_min) and (vs_max is None or vs30 < vs_max):
            return perfil
    raise ValueError(vs30)


def verificar_ts(categoria: str, zona: int, perfil: str, TP: float, ts: float | None) -> list[str]:
    """Numerales 14.2 y 14.8: periodo predominante Ts (H/V) para categorías A y B en zona 4."""
    if not (categoria.startswith(("A", "B")) and zona == 4 and perfil in ("S1", "S2", "S3", "S4")):
        return []
    if ts is None:
        return [
            "Categorías A y B en zona 4: se debe medir el periodo predominante Ts mediante "
            "vibraciones ambientales (H/V), mínimo 3 mediciones de 30 min (num. 14.2 y 15.4)."
        ]
    if ts > 0.65 * TP:
        return [
            f"Ts = {ts:g} s > 0,65·TP = {0.65 * TP:.3f} s: se debe tomar el perfil siguiente más "
            "desfavorable o realizar un estudio de sitio (num. 14.8)."
        ]
    return []


# Tabla N° 7 (art. 19). A1 se resuelve en factor_uso().
FACTOR_USO = {"A2": 1.5, "B": 1.3, "C": 1.0}
CATEGORIAS = ("A1", "A2", "B", "C")


def factor_uso(categoria: str, zona: int, aislamiento: bool = False) -> float:
    """Factor U, Tabla 7 y su nota."""
    if categoria == "A1":
        if zona in (3, 4):
            if not aislamiento:
                raise ValueError(
                    "Categoría A1 en zonas 3 y 4 requiere aislamiento sísmico en la base (Tabla 7)."
                )
            return 1.0
        return 1.0 if aislamiento else 1.5
    if categoria not in FACTOR_USO:
        raise ValueError(f"Categoría {categoria!r} no existe; use una de {', '.join(CATEGORIAS)}.")
    return FACTOR_USO[categoria]


def fraccion_carga_viva(categoria: str, azotea: bool = False) -> float:
    """Porcentaje de carga viva para el peso sísmico P, art. 31 a), b) y d)."""
    if azotea:
        return 0.25
    return 0.50 if categoria.startswith(("A", "B")) else 0.25


@dataclass(frozen=True)
class Sistema:
    clave: str
    nombre: str
    material: str
    R0: float
    CT: float | None
    deriva_max: float
    muros_portantes: bool = False


# Tabla N° 10 (R0), art. 36 (CT) y Tabla N° 14 (deriva).
SISTEMAS = {
    s.clave: s
    for s in (
        Sistema("acero_smf", "Acero – Pórticos especiales resistentes a momentos (SMF)", "acero", 8, 35, 0.010),
        Sistema("acero_imf", "Acero – Pórticos intermedios resistentes a momentos (IMF)", "acero", 5, 35, 0.010),
        Sistema("acero_omf", "Acero – Pórticos ordinarios resistentes a momentos (OMF)", "acero", 4, 35, 0.010),
        Sistema("acero_scbf", "Acero – Pórticos especiales concéntricamente arriostrados (SCBF)", "acero", 7, 45, 0.010),
        Sistema("acero_ocbf", "Acero – Pórticos ordinarios concéntricamente arriostrados (OCBF)", "acero", 4, 45, 0.010),
        Sistema("acero_ebf", "Acero – Pórticos excéntricamente arriostrados (EBF)", "acero", 8, 45, 0.010),
        Sistema("ca_porticos", "Concreto armado – Pórticos", "concreto", 8, 35, 0.007),
        Sistema("ca_dual", "Concreto armado – Dual", "concreto", 7, 60, 0.007),
        Sistema("ca_muros", "Concreto armado – Muros estructurales", "concreto", 6, 60, 0.007, True),
        Sistema("ca_emdl", "Concreto armado – Muros de ductilidad limitada (EMDL)", "concreto", 3.5, 60, 0.004, True),
        Sistema("albanileria", "Albañilería armada o confinada", "albanileria", 3, 60, 0.005, True),
        Sistema("madera", "Madera (esfuerzos admisibles)", "madera", 7, None, 0.010),
    )
}

EMDL_MAX_PISOS = 5  # Tabla 8


def sistema(clave: str) -> Sistema:
    try:
        return SISTEMAS[clave]
    except KeyError:
        raise ValueError(f"Sistema {clave!r} no existe; use uno de {', '.join(SISTEMAS)}.") from None


_PERMITIDOS_ESENCIALES = {"acero_scbf", "acero_ebf", "ca_dual", "ca_muros", "albanileria"}
_PERMITIDOS_B = {
    "acero_smf", "acero_imf", "acero_scbf", "acero_ocbf", "acero_ebf",
    "ca_porticos", "ca_dual", "ca_muros", "albanileria", "madera",
}


def sistema_permitido(
    categoria: str, zona: int, clave: str, aislamiento: bool = False, cobertura_liviana: bool = False
) -> bool:
    """Tabla N° 9 y num. 21.2."""
    if cobertura_liviana or aislamiento:
        return True
    if categoria == "A1":
        return zona in (1, 2) and clave in _PERMITIDOS_ESENCIALES
    if categoria == "A2":
        return zona == 1 or clave in _PERMITIDOS_ESENCIALES
    if categoria == "B":
        return zona == 1 or clave in _PERMITIDOS_B
    return True


@dataclass(frozen=True)
class Irregularidad:
    clave: str
    nombre: str
    tipo: str  # "altura" o "planta"
    factor: float
    extrema: bool = False


# Tablas N° 11 y 12.
IRREGULARIDADES = {
    i.clave: i
    for i in (
        Irregularidad("piso_blando", "Irregularidad de rigidez – Piso blando", "altura", 0.75),
        Irregularidad("piso_debil", "Irregularidad de resistencia – Piso débil", "altura", 0.75),
        Irregularidad("rigidez_extrema", "Irregularidad extrema de rigidez", "altura", 0.50, True),
        Irregularidad("resistencia_extrema", "Irregularidad extrema de resistencia", "altura", 0.50, True),
        Irregularidad("masa", "Irregularidad de masa o peso", "altura", 0.90),
        Irregularidad("geometrica_vertical", "Irregularidad geométrica vertical", "altura", 0.90),
        Irregularidad("discontinuidad", "Discontinuidad en los sistemas resistentes", "altura", 0.80),
        Irregularidad("discontinuidad_extrema", "Discontinuidad extrema de los sistemas resistentes", "altura", 0.60, True),
        Irregularidad("torsional", "Irregularidad torsional", "planta", 0.75),
        Irregularidad("torsional_extrema", "Irregularidad torsional extrema", "planta", 0.60, True),
        Irregularidad("esquinas_entrantes", "Esquinas entrantes", "planta", 0.90),
        Irregularidad("diafragma", "Discontinuidad del diafragma", "planta", 0.85),
        Irregularidad("no_paralelos", "Sistemas no paralelos", "planta", 0.90),
    )
}


def factores_irregularidad(claves: list[str]) -> tuple[float, float]:
    """Ia e Ip como el menor valor de las irregularidades presentes (art. 24)."""
    Ia, Ip = 1.0, 1.0
    for clave in claves:
        if clave not in IRREGULARIDADES:
            raise ValueError(f"Irregularidad {clave!r} no existe; use una de {', '.join(IRREGULARIDADES)}.")
        irr = IRREGULARIDADES[clave]
        if irr.tipo == "altura":
            Ia = min(Ia, irr.factor)
        else:
            Ip = min(Ip, irr.factor)
    return Ia, Ip


def verificar_restricciones(
    categoria: str, zona: int, claves: list[str], n_pisos: int, altura_total: float
) -> list[str]:
    """Tabla N° 13. Devuelve las infracciones encontradas."""
    if not claves:
        return []
    extremas = [IRREGULARIDADES[c].nombre for c in claves if IRREGULARIDADES[c].extrema]
    if categoria in ("A1", "A2"):
        if zona >= 2:
            return [f"Categoría {categoria} en zona {zona}: no se permiten irregularidades (Tabla 13)."]
        prohibir_extremas = True
    elif categoria == "B":
        prohibir_extremas = zona >= 2
    elif zona in (3, 4):
        prohibir_extremas = True
    elif zona == 2:
        prohibir_extremas = not (n_pisos <= 2 or altura_total <= 8.0)
    else:
        prohibir_extremas = False
    if prohibir_extremas and extremas:
        return [
            f"Categoría {categoria} en zona {zona}: no se permiten irregularidades extremas "
            f"(Tabla 13): {', '.join(extremas)}."
        ]
    return []


def coeficiente_R(R0: float, Ia: float, Ip: float) -> float:
    """Art. 26: R = R0 · Ia · Ip."""
    return R0 * Ia * Ip


def periodo_fundamental(hn: float, CT: float) -> float:
    """Art. 36.1: T = hn / CT."""
    return hn / CT


def factor_C(T: float, TP: float, TL: float) -> float:
    """Factor de amplificación sísmica, Tabla N° 6 (espectro de diseño)."""
    if T < 0.2 * TP:
        return 1.0 + 7.5 * T / TP
    if T <= TP:
        return 2.5
    if T < TL:
        return 2.5 * TP / T
    return 2.5 * TP * TL / T**2


def factor_C_estatico(T: float, TP: float, TL: float) -> float:
    """Num. 18.3 y 34.1: en el análisis estático C = 2,5 para 0 ≤ T ≤ TP."""
    return 2.5 if T <= TP else factor_C(T, TP, TL)


def exponente_k(T: float) -> float:
    """Num. 35.2."""
    return 1.0 if T <= 0.5 else min(0.75 + 0.5 * T, 2.0)


C_SOBRE_R_MIN = 0.11  # num. 34.2


@dataclass
class CortanteBasal:
    Z: float
    U: float
    C: float
    S: float
    R: float
    C_sobre_R: float
    coeficiente: float  # V/P
    P: float
    V: float
    minimo_aplicado: bool


def cortante_basal(Z: float, U: float, C: float, S: float, R: float, P: float) -> CortanteBasal:
    """Art. 34: V = Z·U·C·S/R · P, con C/R ≥ 0,11."""
    c_r = C / R
    minimo = c_r < C_SOBRE_R_MIN
    if minimo:
        c_r = C_SOBRE_R_MIN
    coef = Z * U * S * c_r
    return CortanteBasal(Z, U, C, S, R, c_r, coef, P, coef * P, minimo)


def distribucion_en_altura(pesos: list[float], alturas: list[float], V: float, T: float) -> list[float]:
    """Art. 35: Fi = αi·V con αi = Pi·hi^k / Σ Pj·hj^k. Alturas medidas desde la base."""
    k = exponente_k(T)
    productos = [p * h**k for p, h in zip(pesos, alturas, strict=True)]
    total = sum(productos)
    return [V * x / total for x in productos]


def excentricidad_accidental(dimension_perpendicular: float) -> float:
    """Art. 37 y 45: 0,05 veces la dimensión perpendicular a la dirección de análisis."""
    return 0.05 * dimension_perpendicular


def estatico_aplicable(zona: int, regular: bool, altura_total: float, sistemas: list[Sistema]) -> bool:
    """Num. 33.2."""
    if zona == 1:
        return True
    if regular and altura_total <= 30.0:
        return True
    return all(s.muros_portantes for s in sistemas) and altura_total <= 15.0


def factor_desplazamiento(R: float, regular: bool) -> float:
    """Art. 50: desplazamientos inelásticos = 0,75R (regular) o 0,85R (irregular) × elásticos."""
    return (0.75 if regular else 0.85) * R


def fraccion_cortante_minimo_dinamico(regular: bool) -> float:
    """Num. 44.1."""
    return 0.80 if regular else 0.90


def separacion_minima(Z: float, S: float, h: float) -> float:
    """Num. 52.2: s = 0,02·Z·S·h ≥ 0,03 m (h en m)."""
    return max(0.02 * Z * S * h, 0.03)


def coeficiente_sismo_vertical(Z: float, U: float, S: float) -> float:
    """Num. 38.1: 2/3 · Z·U·S del peso."""
    return 2.0 / 3.0 * Z * U * S


def espectro(Z: float, U: float, S: float, R: float, TP: float, TL: float, periodos: list[float]) -> list[float]:
    """Art. 41: Sa/g = Z·U·C·S/R para cada periodo."""
    return [Z * U * factor_C(T, TP, TL) * S / R for T in periodos]


COMBINACION_DIRECCIONAL = (1.0, 0.3)  # art. 28.1, 33.3 y 43: 100 % + 30 %
