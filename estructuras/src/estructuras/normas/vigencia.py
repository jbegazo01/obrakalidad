"""Registro de las normas técnicas del RNE usadas por el programa y su vigencia.

Cada entrada indica el dispositivo legal que la aprueba o modifica y la fecha en que
se verificó por última vez. Revisar este registro antes de emitir un expediente.
"""

from dataclasses import dataclass, field

FECHA_REVISION = "2026-10-20"


@dataclass(frozen=True)
class Norma:
    codigo: str
    titulo: str
    dispositivos: tuple[str, ...]
    implementada: str
    notas: tuple[str, ...] = field(default_factory=tuple)


NORMAS: tuple[Norma, ...] = (
    Norma(
        codigo="E.020",
        titulo="Cargas",
        dispositivos=("D.S. N° 011-2006-VIVIENDA",),
        implementada="Cargas vivas mínimas y pesos unitarios usuales (Anexo 1).",
        notas=("No se encontró modificación posterior a 2006 al " + FECHA_REVISION + ".",),
    ),
    Norma(
        codigo="E.030",
        titulo="Diseño Sismorresistente",
        dispositivos=(
            "D.S. N° 011-2006-VIVIENDA",
            "R.M. N° 355-2018-VIVIENDA",
            "R.M. N° 183-2026-VIVIENDA (El Peruano, 03/05/2026)",
            "R.M. N° 217-2026-VIVIENDA (El Peruano, 03/06/2026): modifica la Disposición "
            "Complementaria Transitoria",
        ),
        implementada=(
            "Texto modificado por R.M. 183-2026: zonificación, perfiles S0–S5, S/TP/TL con "
            "interpolación por Vs30, factor C (Tabla 6), U, sistemas y R0, irregularidades, "
            "restricciones, análisis estático, espectro, derivas y junta sísmica."
        ),
        notas=(
            "Proyectos con expediente en elaboración o aprobado, licencia en trámite o "
            "aprobada, o anteproyecto en consulta antes de la vigencia pueden seguir con el "
            "texto anterior (R.M. 217-2026). Ese texto anterior aún no está implementado.",
            "Anexo II (zona por distrito) aún no está cargado: la zona se ingresa manualmente.",
        ),
    ),
    Norma(
        codigo="E.050",
        titulo="Suelos y Cimentaciones",
        dispositivos=("R.M. N° 406-2018-VIVIENDA",),
        implementada="Aún no implementada (fase 2).",
    ),
    Norma(
        codigo="E.060",
        titulo="Concreto Armado",
        dispositivos=("D.S. N° 010-2009-VIVIENDA",),
        implementada="Propiedades básicas del concreto y acero.",
        notas=(
            "R.M. N° 066-2025-VIVIENDA creó un grupo de trabajo para su actualización; al "
            + FECHA_REVISION
            + " no se encontró una nueva versión aprobada.",
        ),
    ),
    Norma(
        codigo="E.070",
        titulo="Albañilería",
        dispositivos=("D.S. N° 011-2006-VIVIENDA",),
        implementada=(
            "Resistencias de unidades de arcilla (Tabla 9), espesor efectivo mínimo, densidad "
            "mínima de muros, esfuerzo axial máximo, resistencia al corte y control de fisuración."
        ),
        notas=(
            "La E.070 fue calibrada con la zonificación de la E.030 de 2003 (3 zonas). Se usa "
            "el factor Z vigente de la E.030, lo que resulta conservador en la zona 4.",
        ),
    ),
    Norma(
        codigo="E.090",
        titulo="Estructuras Metálicas",
        dispositivos=("D.S. N° 011-2006-VIVIENDA",),
        implementada="Aún no implementada (fase 5).",
    ),
)


def buscar(codigo: str) -> Norma:
    for norma in NORMAS:
        if norma.codigo == codigo:
            return norma
    raise KeyError(codigo)
