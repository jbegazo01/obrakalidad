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


def _especificaciones(ficha: Ficha, diseno=None) -> list[str]:
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
    if diseno is not None:
        horizontales = sorted({f"{v.muro} (piso {v.piso})" for v in diseno.verificaciones if v.refuerzo_horizontal})
        if horizontales:
            lineas.append("  4. Refuerzo horizontal 1 %%c 1/4\" c/2 hiladas (soga) o c/hilada (cabeza):")
            for i in range(0, len(horizontales), 4):
                lineas.append("     " + ", ".join(horizontales[i:i + 4]))
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


def _lamina(pl: Plano, ficha: Ficha, geo: Geometria, titulo: str, nombre_plano: str, lamina: str):
    """Título del dibujo, marco A1 y membrete. Devuelve (x0, y0, ancho, alto) del marco."""
    xs, ys = list(geo.ejes_x.values()), list(geo.ejes_y.values())
    xmin, xmax, ymin = min(xs), max(xs), min(ys)
    pl.texto(titulo, (xmin + xmax) / 2, ymin - 4.0, h=H_TITULO,
             alin=TextEntityAlignment.MIDDLE_CENTER, fuente=FUENTE_TITULO)
    pl.texto(f"ESC. 1/{ESCALA}", (xmin + xmax) / 2, ymin - 4.6, h=H_SUBTITULO,
             alin=TextEntityAlignment.MIDDLE_CENTER)

    x0, y0 = xmin - 6.0, ymin - 7.0
    ancho, alto = LAMINA_A1
    pl.rectangulo(x0, y0, x0 + ancho, y0 + alto, "EST-MARCO")
    pl.rectangulo(x0 + 0.5, y0 + 0.5, x0 + ancho - 0.5, y0 + alto - 0.5, "EST-MARCO")

    mx1, my1 = x0 + ancho - 13.0, y0 + 0.5
    mx2, my2 = x0 + ancho - 0.5, y0 + 6.0
    pl.rectangulo(mx1, my1, mx2, my2, "EST-MARCO")
    ubic = ", ".join(v for v in (ficha.ubicacion.get("distrito"), ficha.ubicacion.get("provincia"),
                                  ficha.ubicacion.get("departamento")) if v)
    filas = [
        ("PROYECTO:", ficha.nombre.upper()),
        ("PROPIETARIO:", ficha.propietario or "—"),
        ("UBICACIÓN:", ubic or "—"),
        ("PLANO:", nombre_plano),
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
    return x0, y0, ancho, alto


def _bloque_texto(pl: Plano, titulo: str, lineas: list[str], x: float, y: float) -> float:
    """Título y líneas de texto; las líneas que empiezan con espacio van sangradas. Devuelve la y final."""
    pl.texto(titulo, x, y, h=H_SUBTITULO, fuente=FUENTE_TITULO)
    y -= 0.55
    for linea in lineas:
        es_titulo = not linea.startswith(" ")
        pl.texto(linea.strip(), x + (0 if es_titulo else 0.3), y, h=H_ETIQUETA,
                 fuente=FUENTE_TITULO if es_titulo else FUENTE)
        y -= 0.32
    return y


def columnas_disenadas(diseno) -> list[Columna]:
    """Columnas con la sección del diseño, ubicadas dentro del muro que gobierna su peralte."""
    resultado = []
    for tipo, datos in diseno.tipos_columna.items():
        t, d = datos["t"] / 100, datos["d"] / 100
        for nudo in datos["nodos"]:
            candidatas = [c for c in diseno.columnas
                          if abs(c.posicion[0] - nudo[0]) < 1e-3 and abs(c.posicion[1] - nudo[1]) < 1e-3]
            gobierna = max(candidatas, key=lambda c: c.d)
            w = diseno.muro(gobierna.muro)
            s = w.coordenada(nudo)
            # Dentro del muro: desde la cara del muro transversal en los extremos, centrada en el resto.
            if abs(s - w.s0) < 1e-6:
                a = s - 0.065
                b = a + d
            elif abs(s - w.s1) < 1e-6:
                b = s + 0.065
                a = b - d
            else:
                a, b = s - d / 2, s + d / 2
            centro_s = (a + b) / 2
            if w.direccion == "x":
                resultado.append(Columna(tipo, (centro_s, w.linea), d, t))
            else:
                resultado.append(Columna(tipo, (w.linea, centro_s), t, d))
    return resultado


def plano_estructuracion(ficha: Ficha, resultado: ResultadoSismico, lamina: str = "E-01", diseno=None) -> Plano:
    """Planta de estructuración. Con `diseno` (resultado de albanileria.analizar) dibuja las
    columnas diseñadas y los cuadros de columnas, soleras y placas del diseño."""
    geo = ficha.geometria
    if geo is None:
        raise ValueError("La ficha no tiene 'geometria'; no se puede dibujar el plano.")
    pl = Plano()

    _dibujar_ejes(pl, geo)
    _dibujar_losas(pl, geo)
    _dibujar_vigas(pl, geo)
    _dibujar_muros(pl, ficha)
    conf = columnas_confinamiento(ficha.muros)
    if diseno is None:
        _dibujar_columnas(pl, conf + geo.columnas)
    else:
        cols = columnas_disenadas(diseno)
        _dibujar_columnas(pl, [Columna(c.id, c.centro, c.dx, c.dy, "confinamiento") for c in cols] + geo.columnas)
        for c in cols:
            pl.texto(c.id, c.centro[0] + c.dx / 2 + 0.06, c.centro[1] + c.dy / 2 + 0.06, h=0.12,
                     capa="EST-TEXTOS")

    x0, y0, ancho, alto = _lamina(pl, ficha, geo, "PLANTA DE ESTRUCTURACIÓN – PISO TÍPICO",
                                  "ESTRUCTURAS – PLANTA DE ESTRUCTURACIÓN", lamina)
    xs = list(geo.ejes_x.values())
    xc = max(xs) + 6.0
    yy = _bloque_texto(pl, "ESPECIFICACIONES TÉCNICAS", _especificaciones(ficha, diseno), xc, y0 + alto - 1.5)

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

    # Cuadros.
    xt = xc + 11.0
    yt = y0 + alto - 1.5
    yt = pl.tabla(xt, yt, [3.0, 2.0, 2.0], _filas_sismo(resultado),
                  titulo=f"PARÁMETROS SÍSMICOS (E.030-{e030.VERSION})")

    if diseno is None:
        filas_col = [["Tipo", "Sección", "Refuerzo (preliminar)", "Estribos (preliminar)"]]
        espesores = sorted({c.dy if c.dx == 0.25 else c.dx for c in conf})
        for t in espesores:
            as_min = e070.acero_minimo_columna(ficha.fc, t * 100 * 25, ficha.fy)
            filas_col.append(["C-1 confinamiento", _sec(t, 0.25), cuatro_barras(as_min), '%%c 1/4": 1@.05, 4@.10, r@.25'])
        anchos = [2.8, 1.2, 2.4, 3.6]
    else:
        filas_col = [["Tipo", "t x d", "Refuerzo", "Estribos"]]
        for tipo, d in diseno.tipos_columna.items():
            filas_col.append([tipo, _sec(d["t"] / 100, d["d"] / 100), d["barras"], d["estribos"]])
        anchos = [1.2, 1.2, 4.2, 4.0]
    for c in geo.columnas:
        # Cuantía mínima de 1 % para columnas (E.060 art. 10.9).
        as_min = 0.01 * c.dx * c.dy * 1e4
        filas_col.append([c.id, _sec(c.dx, c.dy), cuatro_barras(as_min), '%%c 3/8": 1@.05, 5@.10, r@.25'])
    yt = pl.tabla(xt, yt - 1.2, anchos, filas_col, titulo="CUADRO DE COLUMNAS")

    if diseno is not None:
        soleras: dict[tuple, list[str]] = {}
        for mid in sorted({s.muro for s in diseno.soleras}):
            maximo = max((x for x in diseno.soleras if x.muro == mid), key=lambda x: x.As_req)
            soleras.setdefault((diseno.muro(mid).espesor, maximo.barras), []).append(mid)
        h_losa = max(l.h for l in geo.losas)
        filas = [["Tipo", "Sección", "Refuerzo", "Muros"]]
        for k, ((t, barras), muros) in enumerate(sorted(soleras.items()), start=1):
            filas.append([f"VS-{k}", _sec(t, h_losa), barras, ", ".join(muros)])
        yt = pl.tabla(xt, yt - 1.2, [1.2, 1.2, 3.6, 4.6], filas,
                      titulo='VIGAS SOLERAS (estribos %%c 1/4": 1@.05, 4@.10, r@.25)')
        if diseno.placas:
            filas = [["Placa", "t (m)", "Refuerzo mín. (E.060)", "As extremo"]]
            for pid in sorted({p.muro for p in diseno.placas}):
                pmax = max((p for p in diseno.placas if p.muro == pid), key=lambda p: p.As_extremo)
                w = diseno.muro(pid)
                filas.append([pid, _f(w.espesor), f"%%c 3/8\" @ .20 h y v (rho = {pmax.rho_h:.4f})",
                              f"{pmax.As_extremo:.1f} cm²"])
            yt = pl.tabla(xt, yt - 1.2, [1.2, 1.0, 5.0, 2.0], filas, titulo="PLACAS (preliminar, ver memoria)")

    filas_vig = [["Viga", "b x h (m)", "Luz (m)", "h = L/12 – L/10"]]
    for v in geo.vigas:
        sv = seccion_viga(v.luz)
        filas_vig.append([v.id, _sec(v.b, v.h), _f(v.luz), f"{_f(sv.h_min)} – {_f(sv.h_max)}"])
    pl.tabla(xt, yt - 1.2, [2.0, 2.0, 1.6, 3.0], filas_vig, titulo="CUADRO DE VIGAS (refuerzo por diseñar)")
    return pl


def _tipos_cimiento(cim) -> dict:
    """Agrupa los cimientos corridos por ancho y las zapatas por dimensiones."""
    tipos: dict[str, dict] = {}
    corridos = sorted({c.ancho for c in cim.cimientos if c.tipo == "corrido"})
    for k, b in enumerate(corridos, start=1):
        tipos[f"CC-{k}"] = {"ancho": b, "elementos": [c for c in cim.cimientos if c.tipo == "corrido" and c.ancho == b]}
    for k, c in enumerate([c for c in cim.cimientos if c.tipo == "placa"], start=1):
        tipos[f"ZP-{k}"] = {"ancho": c.ancho, "elementos": [c]}
    for k, c in enumerate([c for c in cim.cimientos if c.tipo == "aislada"], start=1):
        tipos[f"Z-{k}"] = {"ancho": c.ancho, "elementos": [c]}
    for c in cim.cimientos:
        if c.tipo == "combinado":
            tipos[c.elemento] = {"ancho": c.ancho, "elementos": [c]}
    return tipos


def plano_cimentacion(ficha: Ficha, diseno, cim, lamina: str = "E-02") -> Plano:
    geo = ficha.geometria
    pl = Plano()
    pl.doc.layers.add("EST-CIMIENTOS", color=5, linetype="DASHED", lineweight=25)
    _dibujar_ejes(pl, geo)
    tipos = _tipos_cimiento(cim)
    etiqueta = {id(c): k for k, d in tipos.items() for c in d["elementos"]}

    for c in cim.cimientos:
        dx, dy = c.dimensiones_xy()
        if c.tipo != "aislada":
            # El cimiento corrido se prolonga medio ancho más allá de los extremos del muro.
            if c.direccion == "x":
                dx += c.ancho
            else:
                dy += c.ancho
        x, y = c.centro
        pl.rectangulo(x - dx / 2, y - dy / 2, x + dx / 2, y + dy / 2, "EST-CIMIENTOS")
        if c.direccion == "x":
            pl.texto(f"{etiqueta[id(c)]}", x, y - c.ancho / 2 - 0.1, h=H_ETIQUETA,
                     alin=TextEntityAlignment.TOP_CENTER)
        else:
            pl.texto(f"{etiqueta[id(c)]}", x + c.ancho / 2 + 0.1, y, h=H_ETIQUETA,
                     alin=TextEntityAlignment.TOP_CENTER, rot=90)
    _dibujar_muros(pl, ficha)
    cols = columnas_disenadas(diseno)
    _dibujar_columnas(pl, [Columna(c.id, c.centro, c.dx, c.dy, "confinamiento") for c in cols] + geo.columnas)

    x0, y0, ancho, alto = _lamina(pl, ficha, geo, "PLANTA DE CIMENTACIÓN", "ESTRUCTURAS – CIMENTACIÓN", lamina)
    xc = max(geo.ejes_x.values()) + 6.0
    q = f"{ficha.capacidad_portante:g} kg/cm²" if ficha.capacidad_portante else "PENDIENTE"
    lineas = [
        "TERRENO",
        f"  Capacidad portante admisible: {q}" + (" (SUPUESTA, confirmar con EMS)" if ficha.capacidad_portante_supuesta else ""),
        f"  Profundidad de cimentación: Df = {cim.opciones.df:.2f} m bajo el terreno natural",
        "CIMIENTOS CORRIDOS",
        "  Concreto ciclópeo 1:10 + 30 % piedra grande (máx. 6\")",
        f"  Peralte {cim.opciones.h_cimiento:.2f} m",
        "SOBRECIMIENTOS",
        f"  Concreto 1:8 + 25 % piedra mediana (máx. 3\"), ancho = muro, h = {cim.opciones.h_sobrecimiento:.2f} m",
        "ZAPATAS Y CIMIENTOS DE PLACAS",
        f"  Concreto f'c = {ficha.fc:g} kg/cm², refuerzo según diseño (E.060)",
        "COLUMNAS",
        "  Refuerzo vertical anclado en el cimiento con gancho a 90° de 0.25 m",
        "NOTAS",
        "  1. No cimentar sobre relleno, material orgánico ni desmonte.",
        "  2. Los cimientos forman una retícula continua (no interrumpirlos).",
        "  3. Verificar el nivel de fondo de cimentación con el EMS.",
    ]
    yy = _bloque_texto(pl, "ESPECIFICACIONES DE CIMENTACIÓN", lineas, xc, y0 + alto - 1.5)

    xt = xc + 11.0
    yt = y0 + alto - 1.5
    filas = [["Tipo", "Ancho (m)", "Peralte (m)", "Elementos"]]
    for k, d in tipos.items():
        e = d["elementos"]
        filas.append([k, _f(d["ancho"]) if not k.startswith("Z-") else f"{_f(e[0].largo)} x {_f(e[0].ancho)}",
                      _f(e[0].peralte), ", ".join(c.elemento for c in e)])
    yt = pl.tabla(xt, yt, [1.2, 1.8, 1.6, 6.0], filas, titulo="CUADRO DE CIMIENTOS")

    # Corte típico de cimiento corrido.
    b = max(d["ancho"] for k, d in tipos.items() if k.startswith("CC-")) if any(
        k.startswith("CC-") for k in tipos) else 0.5
    _corte_tipico(pl, xt + 1.0, yt - 3.0, b, cim.opciones.h_cimiento, cim.opciones.h_sobrecimiento, cim.opciones.df)
    return pl


def _corte_tipico(pl: Plano, x: float, ytop: float, B: float, hc: float, hs: float, df: float, t: float = 0.13):
    """Corte típico de cimiento corrido, dibujado a escala 1/25 (doble del plano)."""
    k = 2.0  # factor de escala del detalle respecto de la planta
    pl.texto("CORTE TÍPICO DE CIMIENTO CORRIDO (ESC. 1/25)", x, ytop + 0.4, h=H_SUBTITULO, fuente=FUENTE_TITULO)
    base = ytop - (df + 0.5) * k
    xc = x + 2.5
    # Cimiento
    pl.rectangulo(xc - B / 2 * k, base, xc + B / 2 * k, base + hc * k, "EST-MUROS")
    pl.rectangulo(xc - B / 2 * k, base, xc + B / 2 * k, base + hc * k, "EST-MUROS-ACHURADO", relleno="AR-CONC",
                  escala_patron=0.01)
    # Sobrecimiento
    ys = base + hc * k
    pl.rectangulo(xc - t / 2 * k, ys, xc + t / 2 * k, ys + hs * k, "EST-MUROS")
    # Muro
    pl.rectangulo(xc - t / 2 * k, ys + hs * k, xc + t / 2 * k, ys + hs * k + 1.0, "EST-MUROS-ACHURADO", relleno="ANSI31")
    # Terreno natural y piso
    ntn = base + df * k
    pl.linea((xc - 2.0, ntn), (xc + 2.0, ntn), "EST-COTAS")
    pl.texto("N.T.N.", xc - 2.1, ntn, h=H_ETIQUETA, alin=TextEntityAlignment.MIDDLE_RIGHT)
    npt = ys + hs * k
    pl.linea((xc - 1.2, npt), (xc - t / 2 * k, npt), "EST-COTAS")
    pl.texto("N.P.T.", xc - 1.3, npt, h=H_ETIQUETA, alin=TextEntityAlignment.MIDDLE_RIGHT)
    pl.texto(f"B = {B:.2f}", xc, base - 0.25, h=H_ETIQUETA, alin=TextEntityAlignment.TOP_CENTER)
    pl.texto(f"h = {hc:.2f}", xc + B / 2 * k + 0.15, base + hc * k / 2, h=H_ETIQUETA,
             alin=TextEntityAlignment.MIDDLE_LEFT)
    pl.texto(f"Sobrecimiento h = {hs:.2f}", xc + t / 2 * k + 0.15, ys + hs * k * 0.75, h=H_ETIQUETA,
             alin=TextEntityAlignment.MIDDLE_LEFT)
    pl.texto(f"Df = {df:.2f}", xc - B / 2 * k - 0.15, base + hc * k / 2, h=H_ETIQUETA,
             alin=TextEntityAlignment.MIDDLE_RIGHT)
    pl.texto("Cimiento: concreto ciclópeo 1:10 + 30 % P.G.", x, base - 0.7, h=H_ETIQUETA)
    pl.texto("Sobrecimiento: concreto 1:8 + 25 % P.M.", x, base - 1.0, h=H_ETIQUETA)
    pl.texto("En linderos el cimiento es excéntrico (cara exterior a ras del muro).", x, base - 1.3, h=H_ETIQUETA)
