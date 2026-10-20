"""Ficha del proyecto: datos de entrada del diseño estructural, en un archivo YAML."""

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .geometria import Geometria, direccion_segmento, leer_geometria, resolver_punto
from .normas import e030, e070, zonificacion
from .normas.e070 import Muro


@dataclass
class Nivel:
    nombre: str
    altura_entrepiso: float  # m
    area: float | None  # m², área techada del nivel
    carga_muerta: float | None  # tonf/m², incluye losa, vigas, muros y acabados
    carga_viva: float | None  # tonf/m²
    azotea: bool = False
    peso: float | None = None  # tonf, peso sísmico ya calculado (p. ej. de ETABS)


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
    periodo_x: float | None  # s, periodo de un análisis (art. 36.2); reemplaza hn/CT
    periodo_y: float | None
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
    geometria: Geometria | None = None
    cargas: dict = field(default_factory=dict)  # opciones del metrado (ver metrado.OpcionesMetrado)
    cimentacion: dict = field(default_factory=dict)  # opciones de cimentación
    capacidad_portante_supuesta: bool = False

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


def _zona(sitio: dict, ubicacion: dict) -> int:
    """Zona sísmica de la ficha o, si falta, la del distrito según el Anexo II de la E.030.
    Si se dan ambas y no coinciden, es un error."""
    distrito = ubicacion.get("distrito")
    zona_distrito = None
    if distrito:
        try:
            zona_distrito = zonificacion.zona_de(distrito, ubicacion.get("provincia"), ubicacion.get("departamento"))
        except ValueError as e:
            if sitio.get("zona") is None:
                raise FichaInvalida(str(e)) from e
    if sitio.get("zona") is None:
        if zona_distrito is None:
            raise FichaInvalida("Falta 'sitio.zona' o 'proyecto.ubicacion.distrito'.")
        return zona_distrito
    zona = int(sitio["zona"])
    if zona_distrito is not None and zona != zona_distrito:
        raise FichaInvalida(f"sitio.zona = {zona} no coincide con el distrito {distrito} (zona {zona_distrito}, "
                            "E.030 Anexo II).")
    return zona


def _leer_muro(m: dict, geometria: Geometria | None) -> Muro:
    id_ = str(_requerido(m, "id", "muros"))
    espesor = float(_requerido(m, "espesor_m", f"muros[{id_}]"))
    material = m.get("material", "albanileria")
    if "desde" in m or "hasta" in m:
        if geometria is None:
            raise FichaInvalida(f"Muro {id_}: 'desde'/'hasta' requieren la sección 'geometria.ejes'.")
        try:
            inicio = resolver_punto(m.get("desde"), geometria.ejes_x, geometria.ejes_y)
            fin = resolver_punto(m.get("hasta"), geometria.ejes_x, geometria.ejes_y)
            direccion = direccion_segmento(inicio, fin)
        except ValueError as e:
            raise FichaInvalida(f"Muro {id_}: {e}") from e
        longitud = abs(fin[0] - inicio[0]) + abs(fin[1] - inicio[1])
        return Muro(id_, direccion, longitud, espesor, material, inicio, fin)
    return Muro(
        id=id_,
        direccion=str(_requerido(m, "direccion", f"muros[{id_}]")).lower(),
        longitud=float(_requerido(m, "longitud_m", f"muros[{id_}]")),
        espesor=espesor,
        material=material,
    )


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
        peso = n.get("peso_sismico_tonf")
        if peso is None:
            area = float(_requerido(n, "area_m2", seccion))
            cm = float(_requerido(n, "carga_muerta_tonf_m2", seccion))
            cv = float(_requerido(n, "carga_viva_tonf_m2", seccion))
        else:
            area, cm, cv = n.get("area_m2"), None, None
        niveles.append(
            Nivel(
                nombre=n.get("nombre", f"Piso {i}"),
                altura_entrepiso=float(_requerido(n, "altura_entrepiso_m", seccion)),
                area=area,
                carga_muerta=cm,
                carga_viva=cv,
                azotea=bool(n.get("azotea", False)),
                peso=float(peso) if peso is not None else None,
            )
        )
    if not niveles:
        raise FichaInvalida("La ficha debe tener al menos un nivel en 'niveles'.")

    geometria = None
    if datos.get("geometria"):
        try:
            geometria = leer_geometria(datos["geometria"])
        except (ValueError, KeyError) as e:
            raise FichaInvalida(f"geometria: {e}") from e

    muros = [_leer_muro(m, geometria) for m in datos.get("muros") or []]

    sistema = estructura.get("sistema")
    return Ficha(
        nombre=_requerido(proyecto, "nombre", "proyecto"),
        categoria=str(_requerido(proyecto, "categoria", "proyecto")),
        uso=proyecto.get("uso", ""),
        ubicacion=proyecto.get("ubicacion") or {},
        propietario=proyecto.get("propietario", ""),
        norma_e030=str(proyecto.get("norma_e030", e030.VERSION)),
        zona=_zona(sitio, proyecto.get("ubicacion") or {}),
        perfil_suelo=str(_requerido(sitio, "perfil_suelo", "sitio")),
        vs30=sitio.get("vs30_m_s"),
        ts=sitio.get("ts_s"),
        capacidad_portante=sitio.get("capacidad_portante_kgf_cm2"),
        sistema_x=estructura.get("sistema_x", sistema),
        sistema_y=estructura.get("sistema_y", sistema),
        ct_x=estructura.get("ct_x"),
        ct_y=estructura.get("ct_y"),
        periodo_x=estructura.get("periodo_x_s"),
        periodo_y=estructura.get("periodo_y_s"),
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
        geometria=geometria,
        cargas=datos.get("cargas") or {},
        cimentacion=datos.get("cimentacion") or {},
        capacidad_portante_supuesta=bool(sitio.get("capacidad_portante_supuesta", False)),
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
        separacion = e070.separacion_maxima_columnas(ficha.niveles[0].altura_entrepiso)
        if m.material == "albanileria" and m.longitud > separacion + 1e-9:
            advertencias.append(
                f"Muro {m.id} (L = {m.longitud:g} m): requiere columnas de confinamiento a no más "
                f"de {separacion:g} m (E.070 art. 20.1b); divídalo en paños."
            )

    if ficha.dimension_x is None or ficha.dimension_y is None:
        advertencias.append(
            "Faltan 'estructura.dimension_x_m' y 'dimension_y_m': no se calcula la "
            "excentricidad accidental."
        )
    if ficha.capacidad_portante is None:
        advertencias.append("Falta la capacidad portante del EMS (sitio.capacidad_portante_kgf_cm2).")

    return errores, advertencias
