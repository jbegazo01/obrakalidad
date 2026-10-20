"""Ficha del proyecto: datos de entrada del diseño estructural, en un archivo YAML."""

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .normas import e030, e070
from .normas.e070 import Muro


@dataclass
class Nivel:
    nombre: str
    altura_entrepiso: float  # m
    area: float  # m², área techada del nivel
    carga_muerta: float  # tonf/m², incluye losa, vigas, muros y acabados
    carga_viva: float  # tonf/m²
    azotea: bool = False


@dataclass
class Ficha:
    nombre: str
    categoria: str
    uso: str
    ubicacion: dict
    propietario: str
    norma_e030: str
    zona: int
    perfil_suelo: str
    vs30: float | None
    ts: float | None
    capacidad_portante: float | None  # kgf/cm²
    sistema_x: str
    sistema_y: str
    ct_x: float | None
    ct_y: float | None
    aislamiento: bool
    cobertura_liviana: bool
    irregularidades: list[str]
    dimension_x: float | None  # m, dimensión total en planta
    dimension_y: float | None
    unidad_albanileria: str | None
    fc: float  # kgf/cm²
    fy: float  # kgf/cm²
    niveles: list[Nivel]
    muros: list[Muro] = field(default_factory=list)

    @property
    def n_pisos(self) -> int:
        return len(self.niveles)

    @property
    def altura_total(self) -> float:
        return sum(n.altura_entrepiso for n in self.niveles)

    @property
    def regular(self) -> bool:
        return not self.irregularidades


class FichaInvalida(ValueError):
    pass


def _requerido(datos: dict, clave: str, seccion: str):
    if datos.get(clave) is None:
        raise FichaInvalida(f"Falta '{seccion}.{clave}' en la ficha.")
    return datos[clave]


def leer_ficha(ruta: str | Path) -> Ficha:
    with open(ruta, encoding="utf-8") as f:
        datos = yaml.safe_load(f) or {}
    return ficha_desde_dict(datos)


def ficha_desde_dict(datos: dict) -> Ficha:
    proyecto = datos.get("proyecto") or {}
    sitio = datos.get("sitio") or {}
    estructura = datos.get("estructura") or {}
    materiales = datos.get("materiales") or {}

    niveles = []
    for i, n in enumerate(datos.get("niveles") or [], start=1):
        seccion = f"niveles[{i}]"
        niveles.append(
            Nivel(
                nombre=n.get("nombre", f"Piso {i}"),
                altura_entrepiso=float(_requerido(n, "altura_entrepiso_m", seccion)),
                area=float(_requerido(n, "area_m2", seccion)),
                carga_muerta=float(_requerido(n, "carga_muerta_tonf_m2", seccion)),
                carga_viva=float(_requerido(n, "carga_viva_tonf_m2", seccion)),
                azotea=bool(n.get("azotea", False)),
            )
        )
    if not niveles:
        raise FichaInvalida("La ficha debe tener al menos un nivel en 'niveles'.")

    muros = [
        Muro(
            id=str(_requerido(m, "id", "muros")),
            direccion=str(_requerido(m, "direccion", "muros")).lower(),
            longitud=float(_requerido(m, "longitud_m", "muros")),
            espesor=float(_requerido(m, "espesor_m", "muros")),
            material=m.get("material", "albanileria"),
        )
        for m in datos.get("muros") or []
    ]

    sistema = estructura.get("sistema")
    return Ficha(
        nombre=_requerido(proyecto, "nombre", "proyecto"),
        categoria=str(_requerido(proyecto, "categoria", "proyecto")),
        uso=proyecto.get("uso", ""),
        ubicacion=proyecto.get("ubicacion") or {},
        propietario=proyecto.get("propietario", ""),
        norma_e030=str(proyecto.get("norma_e030", e030.VERSION)),
        zona=int(_requerido(sitio, "zona", "sitio")),
        perfil_suelo=str(_requerido(sitio, "perfil_suelo", "sitio")),
        vs30=sitio.get("vs30_m_s"),
        ts=sitio.get("ts_s"),
        capacidad_portante=sitio.get("capacidad_portante_kgf_cm2"),
        sistema_x=estructura.get("sistema_x", sistema),
        sistema_y=estructura.get("sistema_y", sistema),
        ct_x=estructura.get("ct_x"),
        ct_y=estructura.get("ct_y"),
        aislamiento=bool(estructura.get("aislamiento", False)),
        cobertura_liviana=bool(estructura.get("cobertura_liviana", False)),
        irregularidades=list(estructura.get("irregularidades") or []),
        dimension_x=estructura.get("dimension_x_m"),
        dimension_y=estructura.get("dimension_y_m"),
        unidad_albanileria=materiales.get("unidad_albanileria"),
        fc=float(materiales.get("fc_kgf_cm2", 210)),
        fy=float(materiales.get("fy_kgf_cm2", 4200)),
        niveles=niveles,
        muros=muros,
    )


def validar(ficha: Ficha) -> tuple[list[str], list[str]]:
    """Devuelve (errores, advertencias). Con errores no se puede calcular."""
    errores: list[str] = []
    advertencias: list[str] = []

    if ficha.norma_e030 != e030.VERSION:
        errores.append(
            f"Solo está implementada la E.030 versión {e030.VERSION} (R.M. 183-2026-VIVIENDA)."
        )

    try:
        sitio = e030.parametros_sitio(ficha.zona, ficha.perfil_suelo, ficha.vs30)
        advertencias += sitio.advertencias
        advertencias += e030.verificar_ts(ficha.categoria, ficha.zona, ficha.perfil_suelo, sitio.TP, ficha.ts)
    except ValueError as e:
        errores.append(str(e))

    try:
        e030.factor_uso(ficha.categoria, ficha.zona, ficha.aislamiento)
    except ValueError as e:
        errores.append(str(e))

    for eje, clave in (("X", ficha.sistema_x), ("Y", ficha.sistema_y)):
        if clave is None:
            errores.append(f"Falta el sistema estructural en la dirección {eje}.")
            continue
        try:
            s = e030.sistema(clave)
        except ValueError as e:
            errores.append(str(e))
            continue
        if ficha.categoria in e030.CATEGORIAS and not e030.sistema_permitido(
            ficha.categoria, ficha.zona, clave, ficha.aislamiento, ficha.cobertura_liviana
        ):
            errores.append(
                f"Dirección {eje}: el sistema '{s.nombre}' no está permitido para categoría "
                f"{ficha.categoria} en zona {ficha.zona} (Tabla 9)."
            )
        if clave == "ca_emdl" and ficha.n_pisos > e030.EMDL_MAX_PISOS:
            errores.append(f"EMDL: máximo {e030.EMDL_MAX_PISOS} pisos (Tabla 8).")
        if clave == "albanileria" and ficha.unidad_albanileria is None:
            errores.append("Falta 'materiales.unidad_albanileria' para el sistema de albañilería.")

    try:
        e030.factores_irregularidad(ficha.irregularidades)
        errores += e030.verificar_restricciones(
            ficha.categoria, ficha.zona, ficha.irregularidades, ficha.n_pisos, ficha.altura_total
        )
    except ValueError as e:
        errores.append(str(e))

    if ficha.unidad_albanileria is not None:
        try:
            e070.unidad(ficha.unidad_albanileria)
        except ValueError as e:
            errores.append(str(e))

    for m in ficha.muros:
        if m.direccion not in ("x", "y"):
            errores.append(f"Muro {m.id}: la dirección debe ser 'x' o 'y'.")
        if m.material not in ("albanileria", "concreto"):
            errores.append(f"Muro {m.id}: el material debe ser 'albanileria' o 'concreto'.")

    if ficha.dimension_x is None or ficha.dimension_y is None:
        advertencias.append(
            "Faltan 'estructura.dimension_x_m' y 'dimension_y_m': no se calcula la "
            "excentricidad accidental."
        )
    if ficha.capacidad_portante is None:
        advertencias.append("Falta la capacidad portante del EMS (sitio.capacidad_portante_kgf_cm2).")

    return errores, advertencias
