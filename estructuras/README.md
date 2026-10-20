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
```

Ejemplo completo: `estructuras sismo ejemplos/vivienda_albanileria.yaml`.

Unidades: tonf y m; resistencias de materiales en kgf/cm².

## Normativa

| Norma | Dispositivo | Estado |
|---|---|---|
| E.020 Cargas | D.S. 011-2006-VIVIENDA | Cargas vivas y pesos unitarios |
| E.030 Diseño Sismorresistente | R.M. 183-2026-VIVIENDA (03/05/2026), transitoria mod. por R.M. 217-2026-VIVIENDA | Implementada (estático, espectro, derivas) |
| E.050 Suelos y Cimentaciones | R.M. 406-2018-VIVIENDA | Pendiente |
| E.060 Concreto Armado | D.S. 010-2009-VIVIENDA (en actualización, R.M. 066-2025) | Propiedades básicas |
| E.070 Albañilería | D.S. 011-2006-VIVIENDA | Densidad, espesor, axial, corte |
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
| 2 | Albañilería confinada: metrado, análisis sísmico, diseño de muros, cimentación | Pendiente |
| 3 | Planos DXF y memoria de cálculo (Word/PDF) | Pendiente |
| 4 | Concreto armado aporticado y dual | Pendiente |
| 5 | Estructuras metálicas | Pendiente |
| 6 | Interfaz web | Pendiente |

## Pruebas

```bash
.venv/bin/pytest
```
