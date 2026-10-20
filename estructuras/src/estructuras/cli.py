"""Interfaz de línea de comandos: `estructuras <comando>`."""

import argparse
import shutil
import sys
from importlib import resources
from pathlib import Path

from . import analisis
from .geometria import luz_libre_losa
from .normas import e030, e070, vigencia
from .predimensionamiento import espesor_aligerado, seccion_viga
from .proyecto import FichaInvalida, leer_ficha, validar


def _f(x: float, dec: int = 3) -> str:
    return f"{x:.{dec}f}".replace(".", ",")


def cmd_normas(_args) -> int:
    print(f"Normas implementadas (revisión de vigencia: {vigencia.FECHA_REVISION})\n")
    for n in vigencia.NORMAS:
        print(f"{n.codigo} {n.titulo}")
        for d in n.dispositivos:
            print(f"    · {d}")
        print(f"    Implementado: {n.implementada}")
        for nota in n.notas:
            print(f"    Nota: {nota}")
        print()
    return 0


def cmd_sistemas(_args) -> int:
    print(f"{'Clave':<14}{'R0':>5}{'CT':>5}{'Deriva':>8}  Sistema (E.030 Tablas 10 y 14)")
    for s in e030.SISTEMAS.values():
        ct = f"{s.CT:g}" if s.CT else "—"
        print(f"{s.clave:<14}{s.R0:>5g}{ct:>5}{_f(s.deriva_max):>8}  {s.nombre}")
    return 0


def cmd_irregularidades(_args) -> int:
    print(f"{'Clave':<24}{'Tipo':<8}{'Factor':>7}  Irregularidad (E.030 Tablas 11 y 12)")
    for i in e030.IRREGULARIDADES.values():
        extrema = "  [extrema]" if i.extrema else ""
        print(f"{i.clave:<24}{i.tipo:<8}{_f(i.factor, 2):>7}  {i.nombre}{extrema}")
    return 0


def cmd_zona(args) -> int:
    from .normas import zonificacion

    encontrados = zonificacion.buscar(args.distrito, args.provincia, args.departamento)
    if not encontrados:
        print(f"Distrito {args.distrito!r} no figura en el Anexo II de la E.030.", file=sys.stderr)
        return 1
    for d in encontrados:
        print(f"{d.distrito} ({d.provincia}, {d.departamento}): zona {d.zona}, Z = {_f(e030.FACTOR_ZONA[d.zona], 2)}")
    return 0


def cmd_nuevo(args) -> int:
    destino = Path(args.archivo)
    if destino.exists():
        print(f"El archivo {destino} ya existe; no se sobrescribe.", file=sys.stderr)
        return 1
    with resources.as_file(resources.files("estructuras") / "plantillas" / "ficha.yaml") as origen:
        shutil.copy(origen, destino)
    print(f"Ficha creada en {destino}. Complete los datos y ejecute: estructuras validar {destino}")
    return 0


def _cargar(ruta: str):
    try:
        ficha = leer_ficha(ruta)
    except (FichaInvalida, OSError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return None, None
    errores, advertencias = validar(ficha)
    for a in advertencias:
        print(f"Advertencia: {a}")
    for e in errores:
        print(f"Error: {e}", file=sys.stderr)
    if advertencias or errores:
        print()
    return ficha, errores


def cmd_validar(args) -> int:
    ficha, errores = _cargar(args.ficha)
    if ficha is None or errores:
        return 1
    print(f"Ficha válida: {ficha.nombre} ({ficha.n_pisos} niveles, hn = {_f(ficha.altura_total, 2)} m).")
    return 0


def cmd_sismo(args) -> int:
    ficha, errores = _cargar(args.ficha)
    if ficha is None or errores:
        return 1
    r = analisis.analisis_estatico(ficha)
    s = r.sitio

    print(f"ANÁLISIS SÍSMICO ESTÁTICO – E.030 ({e030.VERSION})")
    print(f"Proyecto: {ficha.nombre}\n")
    print("Parámetros de sitio")
    print(f"  Zona {s.zona}: Z = {_f(s.Z, 2)} (Tabla 1)")
    vs = f", Vs30 = {s.vs30:g} m/s" if s.vs30 else ""
    print(f"  Perfil {s.perfil} – {e030.NOMBRE_PERFIL[s.perfil]}{vs}")
    print(f"  S = {_f(s.S)}, TP = {_f(s.TP, 2)} s, TL = {_f(s.TL, 2)} s (Tablas 4 y 5)")
    print(f"  Categoría {ficha.categoria}: U = {_f(r.U, 2)} (Tabla 7)\n")

    print("Peso sísmico (art. 31)")
    for n, p in zip(ficha.niveles, r.pesos):
        print(f"  {n.nombre:<12} {_f(p, 2):>10} tonf")
    print(f"  {'Total P':<12} {_f(r.peso_total, 2):>10} tonf\n")

    for d in r.direcciones:
        c = d.cortante
        print(f"Dirección {d.eje}: {d.sistema.nombre}")
        print(f"  R0 = {d.sistema.R0:g}, Ia = {_f(d.Ia, 2)}, Ip = {_f(d.Ip, 2)} → R = {_f(d.R, 2)} (art. 26)")
        periodo = ficha.periodo_x if d.eje == "X" else ficha.periodo_y
        if periodo is not None:
            print(f"  T = {_f(d.T)} s, del análisis de la estructura (art. 36.2)")
        else:
            print(f"  T = hn/CT = {_f(ficha.altura_total, 2)}/{d.CT:g} = {_f(d.T)} s (art. 36.1)")
        print(f"  C = {_f(d.C, 3)} (art. 18.3 y 34.1)   C/R = {_f(c.C_sobre_R)}"
              + ("  (se aplicó el mínimo 0,11)" if c.minimo_aplicado else ""))
        print(f"  ZUCS/R = {_f(c.coeficiente, 4)}")
        print(f"  V = {_f(c.coeficiente, 4)} × {_f(c.P, 2)} = {_f(c.V, 2)} tonf (art. 34)")
        print(f"  Distribución en altura (art. 35), k = {_f(e030.exponente_k(d.T), 2)}:")
        for n, h, fi in zip(ficha.niveles, r.alturas, d.fuerzas):
            mt = f"   Mt = ±{_f(fi * d.excentricidad, 2)} tonf·m" if d.excentricidad else ""
            print(f"    {n.nombre:<12} h = {_f(h, 2):>6} m   F = {_f(fi, 2):>8} tonf{mt}")
        print(f"  Desplazamientos inelásticos = {_f(d.factor_desplazamiento, 3)} × elásticos (art. 50)")
        print(f"  Deriva máxima admisible = {_f(d.deriva_max)} (Tabla 14)\n")

    print("Otros")
    print(f"  Combinación direccional: 100 % + 30 % (art. 28.1 y 33.3)")
    print(f"  Análisis estático aplicable (num. 33.2): {'sí' if r.estatico_aplicable else 'no – usar modal espectral'}")
    print(f"  Junta sísmica mínima s = {_f(r.separacion_minima)} m (num. 52.2)")
    print(f"  Sismo vertical: {_f(r.coef_sismo_vertical, 4)} × peso (num. 38.1)")
    return 0


def cmd_densidad(args) -> int:
    ficha, errores = _cargar(args.ficha)
    if ficha is None or errores:
        return 1
    try:
        r = analisis.verificar_densidad(ficha)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    unidad = e070.unidad(ficha.unidad_albanileria)
    print("DENSIDAD MÍNIMA DE MUROS – E.070 art. 19.2 b)")
    print(f"Proyecto: {ficha.nombre}\n")
    print(f"  Unidad: {unidad.nombre}, f'm = {unidad.fm:g} kgf/cm², Em = {e070.modulo_elasticidad(unidad.fm):g} kgf/cm²")
    print(f"  Ec/Em = {_f(r.Ec_sobre_Em, 2)} (para transformar muros de concreto)")
    print(f"  Área en planta Ap = {_f(r.area_planta, 2)} m², N = {ficha.n_pisos} pisos\n")
    for d in r.direcciones:
        estado = "CUMPLE" if d.cumple else "NO CUMPLE"
        print(f"  Dirección {d.eje}: ΣL·t/Ap = {_f(d.area_muros, 3)}/{_f(r.area_planta, 2)} = "
              f"{_f(d.densidad, 4)}  vs  ZUSN/56 = {_f(d.requerida, 4)}  → {estado}")
    print(f"\n  Espesor efectivo mínimo (art. 19.1 a): t ≥ {_f(r.espesor_minimo, 3)} m")
    if r.muros_delgados:
        print(f"  Muros con espesor menor al mínimo: {', '.join(r.muros_delgados)}")
    if r.muros_cortos:
        print(f"  Muros con L ≤ {_f(e070.LONGITUD_MINIMA_MURO, 2)} m (no se consideran): {', '.join(r.muros_cortos)}")
    return 0 if all(d.cumple for d in r.direcciones) and not r.muros_delgados else 2


def cmd_predim(args) -> int:
    ficha, errores = _cargar(args.ficha)
    if ficha is None or errores:
        return 1
    if ficha.geometria is None:
        print("Error: la ficha no tiene 'geometria'.", file=sys.stderr)
        return 1
    geo = ficha.geometria
    ok = True
    print("PREDIMENSIONAMIENTO (criterios prácticos)\n")
    print("Losas aligeradas: h ≥ L/25")
    for i, losa in enumerate(geo.losas, start=1):
        luz = luz_libre_losa(losa)
        req = espesor_aligerado(luz)
        estado = "ok" if losa.h >= req - 1e-9 else "INSUFICIENTE"
        ok &= estado == "ok"
        print(f"  Paño {i}: L = {_f(luz, 2)} m → h ≥ {_f(req, 2)} m; adoptado {_f(losa.h, 2)} m  {estado}")
    print("\nVigas: h entre L/12 y L/10, b ≥ 0,25 m")
    for v in geo.vigas:
        sv = seccion_viga(v.luz)
        estado = "ok" if v.h >= sv.h_min - 1e-9 and v.b >= sv.b - 1e-9 else "INSUFICIENTE"
        ok &= estado == "ok"
        print(f"  {v.id}: L = {_f(v.luz, 2)} m → h = {_f(sv.h_min, 2)}–{_f(sv.h_max, 2)} m; "
              f"adoptado {_f(v.b, 2)}x{_f(v.h, 2)}  {estado}")
    return 0 if ok else 2


def cmd_plano(args) -> int:
    ficha, errores = _cargar(args.ficha)
    if ficha is None or errores:
        return 1
    from .planos import plano_estructuracion

    try:
        plano = plano_estructuracion(ficha, analisis.analisis_estatico(ficha), lamina=args.lamina)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    salida = Path(args.salida)
    plano.guardar(salida)
    print(f"Plano DXF: {salida}")
    if args.png:
        png = salida.with_suffix(".png")
        plano.exportar_png(png)
        print(f"Vista previa: {png}")
    return 0


def cmd_analizar(args) -> int:
    """Análisis y diseño completo de albañilería confinada: memoria y planos."""
    ficha, errores = _cargar(args.ficha)
    if ficha is None or errores:
        return 1
    from . import albanileria, cimentacion, memoria
    from .planos import plano_cimentacion, plano_estructuracion

    try:
        res = albanileria.analizar(ficha)
        cim = cimentacion.disenar(res)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(f"ANÁLISIS Y DISEÑO – ALBAÑILERÍA CONFINADA (E.070, E.030-{e030.VERSION})")
    print(f"Proyecto: {ficha.nombre}\n")
    print(f"Peso sísmico (metrado): P = {_f(res.sismo.P, 1)} tonf; V = {_f(res.sismo.V, 2)} tonf (R = {res.R:g})")
    for d in ("X", "Y"):
        print(f"  Deriva máx. {d}: {_f(float(res.derivas[d].max()), 4)}   "
              f"Δmax/Δprom: {_f(float(res.relacion_torsion[d].max()), 2)}")
    print("\nResistencia al corte del edificio (E.070 art. 26.4)")
    for g in res.globales:
        print(f"  {g.direccion} piso {g.piso}: ΣVm = {_f(g.suma_Vm, 1)} ≥ VE = {_f(g.VE, 1)}  "
              f"{'cumple' if g.cumple else 'NO CUMPLE'}")
    malos = [v for v in res.verificaciones if not (v.ok_axial and v.ok_fisuracion)]
    print(f"\nMuros: {len(res.verificaciones)} verificaciones por entrepiso, {len(malos)} con observaciones.")
    print(f"Columnas: {len(res.tipos_columna)} tipos; cimientos: {len(cim.cimientos)} elementos.")
    for o in res.observaciones + cim.observaciones:
        print(f"  · {o}")

    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)
    sismo = analisis.analisis_estatico(ficha, pesos=res.metrado.pesos_sismicos)
    archivos = [memoria.generar(res, cim, salida / "memoria_de_calculo.docx")]
    for plano, nombre in ((plano_estructuracion(ficha, sismo, "E-01", diseno=res), "E-01"),
                          (plano_cimentacion(ficha, res, cim, "E-02"), "E-02")):
        ruta = salida / f"{nombre}.dxf"
        plano.guardar(ruta)
        archivos.append(ruta)
        if args.png:
            plano.exportar_png(ruta.with_suffix(".png"))
            archivos.append(ruta.with_suffix(".png"))
    print("\nArchivos:")
    for a in archivos:
        print(f"  {a}")
    return 0 if res.cumple and cim.cumple else 2


def construir_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="estructuras", description="Asistente de diseño estructural (RNE Perú).")
    sub = p.add_subparsers(dest="comando", required=True)

    sub.add_parser("normas", help="Normas implementadas y su vigencia").set_defaults(func=cmd_normas)
    sub.add_parser("sistemas", help="Sistemas estructurales de la E.030").set_defaults(func=cmd_sistemas)
    sub.add_parser("irregularidades", help="Irregularidades de la E.030").set_defaults(func=cmd_irregularidades)

    zona = sub.add_parser("zona", help="Zona sísmica de un distrito (E.030 Anexo II)")
    zona.add_argument("distrito")
    zona.add_argument("--provincia")
    zona.add_argument("--departamento")
    zona.set_defaults(func=cmd_zona)

    nuevo = sub.add_parser("nuevo", help="Crear una ficha de proyecto en blanco")
    nuevo.add_argument("archivo")
    nuevo.set_defaults(func=cmd_nuevo)

    for nombre, ayuda, func in (
        ("validar", "Validar una ficha de proyecto", cmd_validar),
        ("sismo", "Análisis sísmico estático (E.030)", cmd_sismo),
        ("densidad", "Densidad mínima de muros (E.070)", cmd_densidad),
        ("predim", "Predimensionamiento de losas y vigas", cmd_predim),
    ):
        sp = sub.add_parser(nombre, help=ayuda)
        sp.add_argument("ficha")
        sp.set_defaults(func=func)

    plano = sub.add_parser("plano", help="Plano de estructuración en DXF")
    plano.add_argument("ficha")
    plano.add_argument("-o", "--salida", default="salida/E-01.dxf")
    plano.add_argument("--lamina", default="E-01")
    plano.add_argument("--png", action="store_true", help="Generar también una vista previa PNG")
    plano.set_defaults(func=cmd_plano)

    analizar = sub.add_parser("analizar", help="Análisis y diseño de albañilería confinada: memoria y planos")
    analizar.add_argument("ficha")
    analizar.add_argument("-o", "--salida", default="salida")
    analizar.add_argument("--png", action="store_true", help="Generar vistas previas PNG de los planos")
    analizar.set_defaults(func=cmd_analizar)
    return p


def main(argv: list[str] | None = None) -> int:
    args = construir_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
