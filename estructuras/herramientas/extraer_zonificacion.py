"""Extrae el Anexo II (zonificación sísmica por distrito) de la R.M. N° 183-2026-VIVIENDA.

Uso: python herramientas/extraer_zonificacion.py RM_183-2026-VIVIENDA.pdf
Escribe src/estructuras/datos/zonificacion_e030_2026.csv (departamento, provincia, distrito, zona).
Fuente del PDF: https://cdn-web.construccion.org/normas/files/vivienda/RM_183-2026-VIVIENDA.pdf
"""

import csv
import sys
from pathlib import Path

import pdfplumber

SALIDA = Path(__file__).parent.parent / "src" / "estructuras" / "datos" / "zonificacion_e030_2026.csv"


DEPARTAMENTOS = {
    "AMAZONAS", "ÁNCASH", "APURÍMAC", "AREQUIPA", "AYACUCHO", "CAJAMARCA", "CALLAO", "CUSCO",
    "HUANCAVELICA", "HUÁNUCO", "ICA", "JUNÍN", "LA LIBERTAD", "LAMBAYEQUE", "LIMA", "LORETO",
    "MADRE DE DIOS", "MOQUEGUA", "PASCO", "PIURA", "PUNO", "SAN MARTÍN", "TACNA", "TUMBES", "UCAYALI",
}


def limpiar(texto):
    if texto is None:
        return None
    return " ".join(texto.replace("\n", " ").split()).strip() or None


def _columnas(tabla) -> tuple[int, int | None, int, int]:
    """Índices de (departamento, provincia, distrito, zona). Las tablas del PDF tienen un
    número variable de columnas porque los encabezados están partidos."""
    n = len(tabla[0])
    cuenta = [0] * n
    zona = None
    for fila in tabla:
        for k, c in enumerate(fila):
            c = limpiar(c)
            if c:
                cuenta[k] += 1
                if c.isdigit() and len(c) == 1:
                    zona = k
    distrito = max(range(n), key=lambda k: cuenta[k])
    candidatas = [k for k in range(1, distrito) if cuenta[k] > 0]
    provincia = max(candidatas) if candidatas else None
    return 0, provincia, distrito, zona


def extraer(ruta_pdf: str) -> list[tuple[str, str, str, int]]:
    filas = []
    dep = prov = zona = None
    with pdfplumber.open(ruta_pdf) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text() or ""
            if "ZONA SÍSMICA" not in texto or "PROVINCIA" not in texto:
                continue
            for tabla in pagina.extract_tables():
                i_dep, i_prov, i_dis, i_zona = _columnas(tabla)
                for fila in tabla:
                    celdas = [limpiar(c) for c in fila]
                    distrito = celdas[i_dis]
                    if not distrito or distrito in ("DISTRITO", "DIS", "DISTRI"):
                        continue
                    d = celdas[i_dep]
                    p = celdas[i_prov] if i_prov is not None else None
                    z = celdas[i_zona] if i_zona is not None else None
                    if d in DEPARTAMENTOS:
                        dep = d
                    if p:
                        prov = p
                    if z and z.isdigit():
                        zona = int(z)
                    filas.append((dep, prov, distrito, zona))
    return filas


if __name__ == "__main__":
    filas = extraer(sys.argv[1])
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with open(SALIDA, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["departamento", "provincia", "distrito", "zona"])
        w.writerows(filas)
    print(f"{len(filas)} distritos → {SALIDA}")
