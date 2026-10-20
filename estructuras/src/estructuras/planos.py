"""Planos en DXF (se abren en AutoCAD). Dibujo en metros, lámina A1 a escala 1/50."""

import datetime
from pathlib import Path

import ezdxf
from ezdxf.enums import TextEntityAlignment

from . import __version__
from .analisis import ResultadoSismico
from .geometria import Columna, Geometria, columnas_confinamiento, luz_libre_losa
from .normas import e030, e070
from .predimensionamiento import cuatro_barras, espesor_aligerado, seccion_viga
from .proyecto import Ficha

ESCALA = 50
LAMINA_A1 = (0.841 * ESCALA, 0.594 * ESCALA)  # m en el modelo
FUENTE = "OpenSans"
FUENTE_TITULO = "OpenSans-Bold"

CAPAS = {
    # nombre: (color ACI, tipo de línea, grosor en centésimas de mm)
    "EST-EJES": (1, "DASHDOT", 13),
    "EST-COTAS": (4, "Continuous", 13),
    "EST-MUROS": (7, "Continuous", 35),
    "EST-MUROS-ACHURADO": (8, "Continuous", 9),
    "EST-PLACAS": (7, "Continuous", 35),
    "EST-COLUMNAS": (7, "Continuous", 35),
    "EST-VIGAS": (3, "DASHED", 25),
    "EST-LOSAS": (6, "Continuous", 18),
    "EST-HUECOS": (2, "Continuous", 18),
    "EST-TEXTOS": (7, "Continuous", 18),
    "EST-CUADROS": (7, "Continuous", 18),
    "EST-MARCO": (7, "Continuous", 50),
}

H_TEXTO = 0.125  # 2,5 mm impresos a 1/50
H_ETIQUETA = 0.15
H_SUBTITULO = 0.25
H_TITULO = 0.35


def _f(x: float, dec: int = 2) -> str:
    return f"{x:.{dec}f}"


def _sec(b: float, h: float) -> str:
    """Sección en notación de plano: .25x.40"""
    return f"{_f(b).lstrip('0')}x{_f(h).lstrip('0')}"


class Plano:
    def __init__(self):
        self.doc = ezdxf.new("R2010", setup=True)
        self.doc.units = ezdxf.units.M
        self.doc.header["$LTSCALE"] = 0.15
        for nombre, (color, linetype, grosor) in CAPAS.items():
            self.doc.layers.add(nombre, color=color, linetype=linetype, lineweight=grosor)
        self.msp = self.doc.modelspace()

    def texto(self, s, x, y, h=H_TEXTO, capa="EST-TEXTOS", alin=TextEntityAlignment.LEFT, rot=0.0, fuente=FUENTE):
        self.msp.add_text(
            s, height=h, rotation=rot, dxfattribs={"layer": capa, "style": fuente}
        ).set_placement((x, y), align=alin)

    def linea(self, p1, p2, capa):
        self.msp.add_line(p1, p2, dxfattribs={"layer": capa})

    def rectangulo(self, x1, y1, x2, y2, capa, relleno=None, color_relleno=None, escala_patron=0.0125):
        puntos = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
        if relleno:
            atributos = {"layer": capa}
            if color_relleno is not None:
                atributos["color"] = color_relleno
            hatch = self.msp.add_hatch(dxfattribs=atributos)
            if relleno == "SOLID":
                hatch.set_solid_fill(color=color_relleno if color_relleno is not None else 7)
            else:
                hatch.set_pattern_fill(relleno, scale=escala_patron)
            hatch.paths.add_polyline_path(puntos, is_closed=True)
        self.msp.add_lwpolyline(puntos, close=True, dxfattribs={"layer": capa})

    def cota(self, p1, p2, base, angulo):
        dim = self.msp.add_linear_dim(
            base=base,
            p1=p1,
            p2=p2,
            angle=angulo,
            dimstyle="EZDXF",
            override={
                "dimtxt": H_ETIQUETA,
                "dimasz": 0.08,
                "dimexe": 0.08,
                "dimexo": 0.08,
                "dimdec": 2,
                "dimlfac": 1.0,
                "dimzin": 0,
                "dimtad": 1,
                "dimgap": 0.04,
                "dimtxsty": FUENTE,
            },
            dxfattribs={"layer": "EST-COTAS"},
        )
        dim.render()

    def tabla(self, x, y, anchos, filas, titulo=None, h=H_TEXTO, alto_fila=0.32):
        """Dibuja una tabla con su esquina superior izquierda en (x, y). Devuelve la y final."""
        if titulo:
            self.texto(titulo, x, y + 0.15, h=H_SUBTITULO, fuente=FUENTE_TITULO)
        ancho_total = sum(anchos)
        yy = y
        for i, fila in enumerate(filas):
            self.linea((x, yy), (x + ancho_total, yy), "EST-CUADROS")
            xx = x
            for celda, ancho in zip(fila, anchos):
                self.texto(
                    str(celda), xx + 0.08, yy - alto_fila / 2, h=h, alin=TextEntityAlignment.MIDDLE_LEFT,
                    fuente=FUENTE_TITULO if i == 0 else FUENTE,
                )
                xx += ancho
            yy -= alto_fila
        self.linea((x, yy), (x + ancho_total, yy), "EST-CUADROS")
        xx = x
        for ancho in [0, *anchos]:
            xx += ancho
            self.linea((xx, y), (xx, yy), "EST-CUADROS")
        return yy

    def guardar(self, ruta: Path):
        ruta.parent.mkdir(parents=True, exist_ok=True)
        self.doc.saveas(ruta)

    def exportar_png(self, ruta: Path, dpi: int = 150):
        from ezdxf.addons.drawing.matplotlib import qsave

        qsave(self.msp, str(ruta), bg="#FFFFFF", dpi=dpi)


def _dibujar_ejes(pl: Plano, geo: Geometria, extension: float = 2.6, radio: float = 0.30):
    xs, ys = geo.ejes_x.values(), geo.ejes_y.values()
    xmin, xmax, ymin, ymax = min(xs), max(xs), min(ys), max(ys)
    for nombre, x in geo.ejes_x.items():
        pl.linea((x, ymin - extension), (x, ymax + extension), "EST-EJES")
        for yb in (ymin - extension - radio, ymax + extension + radio):
            pl.msp.add_circle((x, yb), radio, dxfattribs={"layer": "EST-COTAS"})
            pl.texto(nombre, x, yb, h=0.28, capa="EST-COTAS", alin=TextEntityAlignment.MIDDLE_CENTER)
    for nombre, y in geo.ejes_y.items():
        pl.linea((xmin - extension, y), (xmax + extension, y), "EST-EJES")
        for xb in (xmin - extension - radio, xmax + extension + radio):
            pl.msp.add_circle((xb, y), radio, dxfattribs={"layer": "EST-COTAS"})
            pl.texto(nombre, xb, y, h=0.28, capa="EST-COTAS", alin=TextEntityAlignment.MIDDLE_CENTER)

    # Cotas parciales y totales entre ejes: arriba y a la izquierda.
    xs_ord, ys_ord = sorted(xs), sorted(ys)
    for a, b in zip(xs_ord, xs_ord[1:]):
        pl.cota((a, ymax), (b, ymax), (a, ymax + 1.0), 0)
    pl.cota((xmin, ymax), (xmax, ymax), (xmin, ymax + 1.7), 0)
    for a, b in zip(ys_ord, ys_ord[1:]):
        pl.cota((xmin, a), (xmin, b), (xmin - 1.0, a), 90)
    pl.cota((xmin, ymin), (xmin, ymax), (xmin - 1.7, ymin), 90)


def _dibujar_muros(pl: Plano, ficha: Ficha):
    for m in ficha.muros:
        if m.inicio is None:
            continue
        (x1, y1), (x2, y2) = m.inicio, m.fin
        t2 = m.espesor / 2
        if m.direccion == "x":
            rect = (min(x1, x2), y1 - t2, max(x1, x2), y1 + t2)
            xm, ym, rot = (x1 + x2) / 2, y1 - t2 - 0.08, 0.0
            alin = TextEntityAlignment.TOP_CENTER
        else:
            rect = (x1 - t2, min(y1, y2), x1 + t2, max(y1, y2))
            xm, ym, rot = x1 + t2 + 0.08, (y1 + y2) / 2, 90.0
            alin = TextEntityAlignment.TOP_CENTER
        if m.material == "concreto":
            pl.rectangulo(*rect, "EST-PLACAS", relleno="SOLID", color_relleno=8)
        else:
            pl.rectangulo(*rect, "EST-MUROS")
            pl.rectangulo(*rect, "EST-MUROS-ACHURADO", relleno="ANSI31")
        pl.texto(f"{m.id} (t={_f(m.espesor)})", xm, ym, h=0.11, alin=alin, rot=rot)


def _dibujar_columnas(pl: Plano, columnas: list[Columna]):
    for c in columnas:
        x, y = c.centro
        pl.rectangulo(x - c.dx / 2, y - c.dy / 2, x + c.dx / 2, y + c.dy / 2, "EST-COLUMNAS",
                      relleno="SOLID", color_relleno=7)
        if c.tipo != "confinamiento":
            pl.texto(c.id, x + c.dx / 2 + 0.08, y - c.dy / 2 - 0.08, h=H_ETIQUETA, alin=TextEntityAlignment.TOP_LEFT)


def _dibujar_vigas(pl: Plano, geo: Geometria):
    for v in geo.vigas:
        (x1, y1), (x2, y2) = v.inicio, v.fin
        b2 = v.b / 2
        etiqueta = f"{v.id} ({_sec(v.b, v.h)})"
        if abs(y1 - y2) < 1e-9:
            for d in (-b2, b2):
                pl.linea((x1, y1 + d), (x2, y2 + d), "EST-VIGAS")
            pl.texto(etiqueta, (x1 + x2) / 2, y1 + b2 + 0.08, h=0.12, alin=TextEntityAlignment.BOTTOM_CENTER)
        else:
            for d in (-b2, b2):
                pl.linea((x1 + d, y1), (x2 + d, y2), "EST-VIGAS")
            pl.texto(etiqueta, x1 - b2 - 0.08, (y1 + y2) / 2, h=0.12, alin=TextEntityAlignment.BOTTOM_CENTER, rot=90)


def _flecha(pl: Plano, punta, direccion, largo=0.18, ancho=0.07):
    (x, y), (dx, dy) = punta, direccion
    base = (x - dx * largo, y - dy * largo)
    puntos = [(x, y), (base[0] - dy * ancho, base[1] + dx * ancho), (base[0] + dy * ancho, base[1] - dx * ancho)]
    hatch = pl.msp.add_hatch(dxfattribs={"layer": "EST-LOSAS"})
    hatch.set_solid_fill(color=6)
    hatch.paths.add_polyline_path(puntos, is_closed=True)


def _dibujar_losas(pl: Plano, geo: Geometria):
    for losa in geo.losas:
        (x1, y1), (x2, y2) = losa.inicio, losa.fin
        xc, yc = (x1 + x2) / 2, (y1 + y2) / 2
        nombre = "ALIG." if losa.tipo == "aligerado" else "LOSA MACIZA"
        texto = f"{nombre} h={_f(losa.h).lstrip('0')}"
        h_texto = H_ETIQUETA if luz_libre_losa(losa) >= 2.5 else 0.09
        if losa.direccion == "x":
            mitad = abs(x2 - x1) * 0.32
            a, b = (xc - mitad, yc), (xc + mitad, yc)
            pl.linea(a, b, "EST-LOSAS")
            _flecha(pl, a, (-1, 0))
            _flecha(pl, b, (1, 0))
            pl.texto(texto, xc, yc + 0.08, h=h_texto, capa="EST-LOSAS", alin=TextEntityAlignment.BOTTOM_CENTER)
        else:
            mitad = abs(y2 - y1) * 0.32
            a, b = (xc, yc - mitad), (xc, yc + mitad)
            pl.linea(a, b, "EST-LOSAS")
            _flecha(pl, a, (0, -1))
            _flecha(pl, b, (0, 1))
            pl.texto(texto, xc - 0.08, yc, h=h_texto, capa="EST-LOSAS",
                     alin=TextEntityAlignment.BOTTOM_CENTER, rot=90)
    for h in geo.huecos:
        (x1, y1), (x2, y2) = h.inicio, h.fin
        pl.rectangulo(min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2), "EST-HUECOS")
        pl.linea((x1, y1), (x2, y2), "EST-HUECOS")
        pl.linea((x1, y2), (x2, y1), "EST-HUECOS")
        if h.nombre:
            pl.texto(h.nombre, (x1 + x2) / 2, (y1 + y2) / 2 + 0.25, h=H_ETIQUETA,
                     capa="EST-HUECOS", alin=TextEntityAlignment.MIDDLE_CENTER)


def _especificaciones(ficha: Ficha) -> list[str]:
    lineas = [
        "CONCRETO ARMADO (E.060)",
        f"  f'c = {ficha.fc:g} kg/cm²: columnas, vigas, losas y placas",
        "ACERO DE REFUERZO",
        f"  fy = {ficha.fy:g} kg/cm² (grado 60, ASTM A615)",
    ]
    if ficha.unidad_albanileria:
        u = e070.unidad(ficha.unidad_albanileria)
        lineas += [
            "ALBAÑILERÍA (E.070)",
            f"  Unidad: {u.nombre}, f'b = {u.fb:g} kg/cm²",
            f"  f'm = {u.fm:g} kg/cm²   v'm = {u.vm:g} kg/cm²",
            "  Mortero 1:4 (cemento:arena gruesa), juntas de 1,0 a 1,5 cm",
            "  Conexión dentada muro-columna (dientes máx. 5 cm)",
        ]
    lineas += [
        "RECUBRIMIENTOS (E.060)",
        "  Columnas y vigas: 4,0 cm   Losas: 2,0 cm   Cimentación: 7,0 cm",
        "SOBRECARGAS (E.020)",
        "  Vivienda: 200 kg/m²   Escaleras: 200 kg/m²   Azotea: 100 kg/m²",
        "TERRENO",
    ]
    if ficha.capacidad_portante:
        lineas.append(f"  Capacidad portante admisible: {ficha.capacidad_portante:g} kg/cm² (EMS)")
    else:
        lineas.append("  Capacidad portante: PENDIENTE (requiere EMS)")
    lineas += [
        "NOTAS",
        "  1. Todo muro portante lleva viga solera de ancho t y peralte igual a la losa.",
        "  2. Dimensiones de predimensionamiento: se confirman con el diseño de cada elemento.",
        "  3. Borrador generado por el programa; requiere revisión y firma del ingeniero.",
    ]
    return lineas


def _filas_sismo(r: ResultadoSismico) -> list[list[str]]:
    dx, dy = r.direcciones
    s = r.sitio
    return [
        ["Parámetro", "Dir. X", "Dir. Y"],
        ["Z (zona " + str(s.zona) + ")", _f(s.Z), _f(s.Z)],
        ["U", _f(r.U), _f(r.U)],
        ["S (" + s.perfil + ")", _f(s.S), _f(s.S)],
        ["TP / TL (s)", f"{_f(s.TP)} / {_f(s.TL)}", f"{_f(s.TP)} / {_f(s.TL)}"],
        ["R0", f"{dx.sistema.R0:g}", f"{dy.sistema.R0:g}"],
        ["R = R0·Ia·Ip", _f(dx.R), _f(dy.R)],
        ["T (s)", _f(dx.T, 3), _f(dy.T, 3)],
        ["ZUCS/R", _f(dx.cortante.coeficiente, 4), _f(dy.cortante.coeficiente, 4)],
        ["V basal (tonf)", _f(dx.cortante.V), _f(dy.cortante.V)],
        ["Deriva máx.", _f(dx.deriva_max, 3), _f(dy.deriva_max, 3)],
        ["Junta mín. (m)", _f(r.separacion_minima, 3), _f(r.separacion_minima, 3)],
    ]


def plano_estructuracion(ficha: Ficha, resultado: ResultadoSismico, lamina: str = "E-01") -> Plano:
    geo = ficha.geometria
    if geo is None:
        raise ValueError("La ficha no tiene 'geometria'; no se puede dibujar el plano.")
    pl = Plano()

    _dibujar_ejes(pl, geo)
    _dibujar_losas(pl, geo)
    _dibujar_vigas(pl, geo)
    _dibujar_muros(pl, ficha)
    conf = columnas_confinamiento(ficha.muros)
    _dibujar_columnas(pl, conf + geo.columnas)

    xs, ys = list(geo.ejes_x.values()), list(geo.ejes_y.values())
    xmin, xmax, ymin = min(xs), max(xs), min(ys)
    pl.texto("PLANTA DE ESTRUCTURACIÓN – PISO TÍPICO", (xmin + xmax) / 2, ymin - 4.0, h=H_TITULO,
             alin=TextEntityAlignment.MIDDLE_CENTER, fuente=FUENTE_TITULO)
    pl.texto(f"ESC. 1/{ESCALA}", (xmin + xmax) / 2, ymin - 4.6, h=H_SUBTITULO,
             alin=TextEntityAlignment.MIDDLE_CENTER)

    # Marco de la lámina A1.
    x0, y0 = xmin - 6.0, ymin - 7.0
    ancho, alto = LAMINA_A1
    pl.rectangulo(x0, y0, x0 + ancho, y0 + alto, "EST-MARCO")
    pl.rectangulo(x0 + 0.5, y0 + 0.5, x0 + ancho - 0.5, y0 + alto - 0.5, "EST-MARCO")

    # Columna 1 de cuadros: especificaciones técnicas.
    xc = xmax + 6.0
    yc = y0 + alto - 1.5
    pl.texto("ESPECIFICACIONES TÉCNICAS", xc, yc, h=H_SUBTITULO, fuente=FUENTE_TITULO)
    yy = yc - 0.55
    for linea in _especificaciones(ficha):
        es_titulo = not linea.startswith(" ")
        pl.texto(linea.strip(), xc + (0 if es_titulo else 0.3), yy, h=H_ETIQUETA,
                 fuente=FUENTE_TITULO if es_titulo else FUENTE)
        yy -= 0.32

    # Leyenda.
    yy -= 0.4
    pl.texto("LEYENDA", xc, yy, h=H_SUBTITULO, fuente=FUENTE_TITULO)
    yy -= 0.7
    pl.rectangulo(xc, yy, xc + 0.8, yy + 0.25, "EST-MUROS")
    pl.rectangulo(xc, yy, xc + 0.8, yy + 0.25, "EST-MUROS-ACHURADO", relleno="ANSI31")
    pl.texto("Muro portante de albañilería", xc + 1.0, yy + 0.05, h=H_ETIQUETA)
    yy -= 0.5
    pl.rectangulo(xc, yy, xc + 0.8, yy + 0.25, "EST-PLACAS", relleno="SOLID", color_relleno=8)
    pl.texto("Placa de concreto armado", xc + 1.0, yy + 0.05, h=H_ETIQUETA)
    yy -= 0.5
    pl.rectangulo(xc + 0.25, yy, xc + 0.5, yy + 0.25, "EST-COLUMNAS", relleno="SOLID", color_relleno=7)
    pl.texto("Columna", xc + 1.0, yy + 0.05, h=H_ETIQUETA)
    yy -= 0.4
    pl.linea((xc, yy + 0.05), (xc + 0.8, yy + 0.05), "EST-VIGAS")
    pl.linea((xc, yy + 0.2), (xc + 0.8, yy + 0.2), "EST-VIGAS")
    pl.texto("Viga peraltada", xc + 1.0, yy + 0.05, h=H_ETIQUETA)

    # Columna 2 de cuadros: parámetros sísmicos, columnas y vigas.
    xt = xc + 11.0
    yt = y0 + alto - 1.5
    yt = pl.tabla(xt, yt, [3.0, 2.0, 2.0], _filas_sismo(resultado),
                  titulo=f"PARÁMETROS SÍSMICOS (E.030-{e030.VERSION})")

    filas_col = [["Tipo", "Sección", "Refuerzo (preliminar)", "Estribos (preliminar)"]]
    espesores = sorted({c.dy if c.dx == 0.25 else c.dx for c in conf})
    for t in espesores:
        as_min = e070.acero_minimo_columna(ficha.fc, t * 100 * 25, ficha.fy)
        filas_col.append(["C-1 confinamiento", _sec(t, 0.25), cuatro_barras(as_min), '%%c 1/4": 1@.05, 4@.10, r@.25'])
    for c in geo.columnas:
        # Cuantía mínima de 1 % para columnas (E.060 art. 10.9).
        as_min = 0.01 * c.dx * c.dy * 1e4
        filas_col.append([c.id, _sec(c.dx, c.dy), cuatro_barras(as_min), '%%c 3/8": 1@.05, 5@.10, r@.25'])
    yt = pl.tabla(xt, yt - 1.2, [2.8, 1.2, 2.4, 3.6], filas_col, titulo="CUADRO DE COLUMNAS")

    filas_vig = [["Viga", "b x h (m)", "Luz (m)", "h = L/12 – L/10"]]
    for v in geo.vigas:
        sv = seccion_viga(v.luz)
        filas_vig.append([v.id, _sec(v.b, v.h), _f(v.luz), f"{_f(sv.h_min)} – {_f(sv.h_max)}"])
    yt = pl.tabla(xt, yt - 1.2, [2.0, 2.0, 1.6, 3.0], filas_vig, titulo="CUADRO DE VIGAS (refuerzo por diseñar)")

    filas_los = [["Paño", "Luz (m)", "h req. = L/25", "h adoptado"]]
    for i, losa in enumerate(geo.losas, start=1):
        luz = luz_libre_losa(losa)
        filas_los.append([str(i), _f(luz), _f(espesor_aligerado(luz)), _f(losa.h)])
    pl.tabla(xt, yt - 1.2, [1.2, 1.6, 2.6, 2.2], filas_los, titulo="LOSAS ALIGERADAS")

    # Membrete.
    mx1, my1 = x0 + ancho - 13.0, y0 + 0.5
    mx2, my2 = x0 + ancho - 0.5, y0 + 6.0
    pl.rectangulo(mx1, my1, mx2, my2, "EST-MARCO")
    ubic = ", ".join(v for v in (ficha.ubicacion.get("distrito"), ficha.ubicacion.get("provincia"),
                                  ficha.ubicacion.get("departamento")) if v)
    filas = [
        ("PROYECTO:", ficha.nombre.upper()),
        ("PROPIETARIO:", ficha.propietario or "—"),
        ("UBICACIÓN:", ubic or "—"),
        ("PLANO:", "ESTRUCTURAS – PLANTA DE ESTRUCTURACIÓN"),
        ("ESCALA:", f"1/{ESCALA}"),
        ("FECHA:", datetime.date.today().strftime("%d/%m/%Y")),
        ("ING. RESPONSABLE:", "______________________   CIP N° ________"),
    ]
    yy = my2 - 0.45
    for etiqueta, valor in filas:
        pl.texto(etiqueta, mx1 + 0.3, yy, h=H_ETIQUETA, fuente=FUENTE_TITULO)
        pl.texto(valor, mx1 + 3.3, yy, h=H_ETIQUETA)
        yy -= 0.55
    pl.linea((mx2 - 3.0, my1), (mx2 - 3.0, my1 + 1.6), "EST-MARCO")
    pl.linea((mx2 - 3.0, my1 + 1.6), (mx2, my1 + 1.6), "EST-MARCO")
    pl.texto("LÁMINA", mx2 - 1.5, my1 + 1.3, h=H_ETIQUETA, alin=TextEntityAlignment.MIDDLE_CENTER)
    pl.texto(lamina, mx2 - 1.5, my1 + 0.6, h=0.5, alin=TextEntityAlignment.MIDDLE_CENTER, fuente=FUENTE_TITULO)
    pl.texto(f"Generado con estructuras v{__version__} – BORRADOR", mx1 + 0.3, my1 + 0.25, h=0.1)
    return pl
