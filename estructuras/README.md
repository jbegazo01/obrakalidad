# Estructuras – asistente de diseño estructural (RNE Perú)

Herramienta para preparar el expediente estructural de edificaciones de concreto armado,
albañilería confinada y acero a partir de la información del arquitecto, según el
Reglamento Nacional de Edificaciones.

> Los resultados son borradores de ingeniería. El ingeniero proyectista revisa, valida y
> firma el expediente y es el responsable del diseño.

## Instalación

```bash
cd estructuras
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
```

## Uso

```bash
estructuras normas                     # normas implementadas y su vigencia
estructuras sistemas                   # sistemas estructurales, R0, CT y derivas (E.030)
estructuras irregularidades            # claves de irregularidades (E.030 Tablas 11 y 12)
estructuras nuevo mi_proyecto.yaml     # ficha en blanco
estructuras validar mi_proyecto.yaml
estructuras sismo mi_proyecto.yaml     # análisis sísmico estático E.030
estructuras densidad mi_proyecto.yaml  # densidad mínima de muros E.070
estructuras predim mi_proyecto.yaml    # predimensionamiento de losas y vigas
estructuras plano mi_proyecto.yaml -o salida/E-01.dxf --png   # plano de estructuración
estructuras analizar mi_proyecto.yaml -o salida/ --png        # análisis y diseño completo
```

`analizar` (albañilería confinada, hasta 5 pisos o 15 m) hace el metrado por muro, el análisis
sísmico con un modelo pseudo-3D (muros en voladizo con alas y columnas transformadas, diafragma
rígido, torsión accidental y combinación 100 % + 30 %), todas las verificaciones de la E.070
(esfuerzo axial, fisuración, Vm, resistencia global, agrietamiento de pisos superiores, refuerzo
horizontal), el diseño de columnas de confinamiento (Tabla 11) y soleras, la verificación
preliminar de placas y la cimentación (cimientos corridos y retícula ante el volteo). Genera la
memoria de cálculo en Word y los planos E-01 (estructuración) y E-02 (cimentación).

Ejemplos:

| Archivo | Contenido |
|---|---|
| `ejemplos/propuesta_vivienda_8x20.yaml` | Propuesta completa con geometría: vivienda de 3 pisos en albañilería confinada (lote 8 × 20 m) |
| `ejemplos/vivienda_albanileria.yaml` | Vivienda de 3 pisos, solo muros (sin geometría) |
| `ejemplos/kora_e030_2026.yaml` | Edificio de 11 pisos de muros de concreto (memoria de 2023) recalculado con la E.030-2026 |

En `geometria` se definen los ejes; los muros, vigas, losas y huecos se ubican con puntos
`[eje_x, eje_y]` (p. ej. `[B, 3]`) o con coordenadas (`[2.40, 8.00]`). Las columnas de
confinamiento se generan solas en los extremos de cada muro de albañilería.

El plano DXF usa capas `EST-*`, metros como unidad de dibujo y lámina A1 a escala 1/50.

Unidades: tonf y m; resistencias de materiales en kgf/cm².

## Normativa

| Norma | Dispositivo | Estado |
|---|---|---|
| E.020 Cargas | D.S. 011-2006-VIVIENDA | Cargas vivas y pesos unitarios |
| E.030 Diseño Sismorresistente | R.M. 183-2026-VIVIENDA (03/05/2026), transitoria mod. por R.M. 217-2026-VIVIENDA | Implementada (estático, espectro, derivas) |
| E.050 Suelos y Cimentaciones | R.M. 406-2018-VIVIENDA | Cimientos corridos (ancho por servicio, sismo con +30 %) |
| E.060 Concreto Armado | D.S. 010-2009-VIVIENDA (en actualización, R.M. 066-2025) | Propiedades básicas |
| E.070 Albañilería | D.S. 011-2006-VIVIENDA | Cap. 7 y 8 completos (análisis y diseño de albañilería confinada) |
| E.090 Estructuras Metálicas | D.S. 011-2006-VIVIENDA | Pendiente |

Cambios de la E.030-2026 ya incorporados: perfiles S0–S5 por Vs30, N60 o Su; S, TP y TL
interpolados con Vs30; rama de C para T < 0,2·TP; verificación de Ts (H/V) para categorías
A y B en zona 4; R0 = 3,5 y deriva 0,004 para EMDL; acción sísmica 100 % + 30 %; junta
sísmica s = 0,02·Z·S·h.

Los proyectos con expediente en elaboración o aprobado, licencia en trámite o anteproyecto
en consulta antes de la vigencia pueden usar el texto anterior de la E.030 (R.M. 217-2026).
Ese texto anterior aún no está implementado.

## Hoja de ruta

| Fase | Contenido | Estado |
|---|---|---|
| 0 | Base normativa, ficha del proyecto, CLI | Hecho |
| 1 | Lectura del PDF de arquitectura → ficha | Pendiente |
| 2 | Albañilería confinada: metrado, análisis sísmico, diseño de muros, cimentación | Hecho |
| 3 | Planos DXF y memoria de cálculo (Word/PDF) | Iniciada: E-01, E-02 y memoria; faltan detalles y E.060 |
| 4 | Concreto armado aporticado y dual | Pendiente |
| 5 | Estructuras metálicas | Pendiente |
| 6 | Interfaz web | Pendiente |

## Pruebas

```bash
.venv/bin/pytest
```
