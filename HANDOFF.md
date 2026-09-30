# Handoff — ObraCalidad

Documento de contexto para el ingeniero/a de software que continúe este proyecto. Escrito al
cierre de la etapa de prototipo frontend (construido con asistencia de Claude Code por un
ingeniero civil, sin experiencia previa de desarrollo).

## 1. Qué es esto

ObraCalidad es un SaaS de gestión de calidad para empresas constructoras peruanas. La idea de
negocio: digitalizar los protocolos de inspección de calidad que hoy se llenan en papel
(checklists de conformidad, matrices de control, no conformidades), con evidencia fotográfica,
firmas, y exportación a PDF en el formato que ya usan las constructoras.

Alcance planeado a futuro (no construido todavía): gestión de seguridad, producción de obra,
valorizaciones. Se empezó por calidad porque es el dolor que mejor conoce el fundador.

## 2. Qué es esto (y qué NO es)

Es un **prototipo de frontend**, construido para validar el producto y la experiencia de
usuario con clientes reales antes de invertir en un backend. **No tiene servidor, base de
datos, ni autenticación real.** Todo el estado vive en memoria del navegador (React Context) y
se pierde al recargar la página. Esto fue una decisión deliberada para poder iterar rápido en
UI/UX — no un descuido — pero es la primera pieza que hay que reemplazar.

## 3. Stack técnico

- **Next.js 16** (App Router), TypeScript, Tailwind CSS v4.
- **shadcn/ui, pero sobre [Base UI](https://base-ui.com), no Radix.** Esto importa: los
  componentes generados por `npx shadcn@latest add ...` en este proyecto usan la API de Base UI,
  que difiere de Radix en varios puntos que causaron bugs reales durante el desarrollo:
  - No existe `asChild` en triggers (Dialog, etc.) — se usa la prop `render={<Componente />}`.
  - `Select` **no** deriva la etiqueta visible del texto hijo de `SelectItem` a menos que se le
    pase la prop `items={{ valor: "Etiqueta" }}` al `Select` raíz. Si ves un `<Select>` mostrando
    el `value` crudo en vez del texto legible, es porque falta ese `items`.
  - `onValueChange` de varios componentes recibe `(value, eventDetails)`, y `value` puede venir
    `null` (no `undefined`).
- Sin librería de gestión de estado externa — todo vía React Context (ver sección 5).
- PDF/impresión: **no se usa ninguna librería de PDF.** Se construyó una página imprimible
  (`/inspecciones/[id]/imprimir`) con CSS de impresión (`@media print`, `@page`) y el usuario usa
  "Imprimir → Guardar como PDF" del navegador. Fue una decisión deliberada: cubre exportar e
  imprimir con una sola implementación, y permite pixel-matchear el formato de encabezado que
  usan las constructoras (ver `src/app/inspecciones/[id]/imprimir/page.tsx`).

## 4. Estructura de carpetas

```
src/
  app/
    login/                          Login (simulado)
    inspecciones/
      page.tsx                      Lista + KPIs
      nueva/page.tsx                Crear inspección (checklist o matriz)
      [id]/page.tsx                 Detalle — editable mientras no esté finalizada
      [id]/imprimir/page.tsx        Vista de impresión/PDF (sin sidebar)
    no-conformidades/page.tsx
    proyectos/page.tsx
    configuracion/
      usuarios/                     Alta de usuarios por empresa (roles)
      criterios-inspeccion/         Plantillas de protocolo (checklist y matriz)
      criterios-no-conformidad/     Severidades configurables (color + SLA)
      plantilla-pdf/                Logo de empresa + datos de encabezado por proyecto
  components/                       Componentes de UI (incluye ui/ = shadcn)
  lib/
    types.ts                        Todos los tipos del dominio — leer primero
    app-data-context.tsx            Fuente de la verdad de los datos (ver sección 5)
    auth-context.tsx                Sesión simulada
    inspeccion-utils.ts             Lógica derivada (estado visible, progreso de solución)
    mock-data.ts / seed-*.ts        Datos semilla
```

## 5. Arquitectura de datos actual (y por qué)

Todo pasa por dos React Context, ambos con estado 100% en memoria:

- **`AppDataProvider`** (`src/lib/app-data-context.tsx`): dueño de `inspecciones`,
  `noConformidades`, `usuarios`, `protocolos`, `severidades`, `empresa`,
  `proyectoPdfConfig`. Expone acciones (`addInspeccion`, `finalizarInspeccion`, etc.) que hacen
  `setState` con la lógica de negocio adentro (p. ej. recalcular cumplimiento al editar un
  criterio).
- **`AuthProvider`** (`src/lib/auth-context.tsx`): sesión actual. Valida contra la lista de
  `usuarios` del contexto anterior — no hay contraseñas reales.

**Para conectar un backend real**, la forma más directa es mantener la misma forma de las
funciones expuestas por `useAppData()`/`useAuth()` (incluso los mismos nombres), pero
implementarlas con `fetch`/mutations a una API en vez de `setState`. Eso minimiza el reescribir
de las ~15 páginas que ya consumen estos hooks.

### Patrón clave: Plantilla → Instancia

Se repite en dos lugares y vale la pena entenderlo antes de tocar código:

- **Protocolo → Inspección**: un `ProtocoloInspeccion` (configurado en Configuración) es una
  plantilla reusable. Al crear una inspección, se **copian** sus criterios/columnas/filas al
  registro nuevo (`items`, `matrizColumnas`, `matrizFilas`). Esto es intencional: si luego se
  edita la plantilla, las inspecciones ya creadas no cambian retroactivamente (registro
  histórico).
- **Severidad (No Conformidad)**: mismo patrón — configurable en Configuración, con SLA en días
  que autocompleta la fecha límite sugerida al crear una NC.

### Dos tipos de "protocolo" dentro de Inspecciones

`ProtocoloInspeccion.tipo` es `"checklist" | "matriz"`:

- **checklist**: criterios con respuesta Cumple/No cumple/No aplica → calcula `cumplimiento` (%)
  y `resultado` (Aprobado/Observado/Rechazado). Ver `calcularCumplimiento()` en
  `app-data-context.tsx` — los criterios "No aplica" se excluyen del cálculo.
- **matriz**: tabla libre (eje X = columnas, eje Y = filas), puramente informativa. No calcula
  cumplimiento; internamente se guarda `resultado: "Aprobado"` y `cumplimiento: 100` como
  valores neutros para no romper el resto del modelo, pero **la UI la excluye explícitamente**
  de KPIs y filtros de conformidad (ver `esMatriz()` en `inspeccion-utils.ts` y sus usos).

### Tres capas de estado sobre una Inspección (no confundir)

1. **`resultado`** (Aprobado/Observado/Rechazado): el hallazgo, recalculado cada vez que se edita
   un criterio. No se "cierra" nunca solo — refleja el estado actual de las respuestas.
2. **`estado`** (`Pendiente`/`Solucionado`): trazabilidad de si los hallazgos ya se corrigieron.
   Se activa con un botón explícito ("Marcar inspección como Solucionada"), no automáticamente,
   y se revierte solo si se vuelve a editar un criterio y ya no aplica.
3. **`finalizada`** (booleano): candado total. Mientras `false`, todo es editable (comentarios,
   evidencia, incluso cambiar una respuesta ya dada). Al finalizar, la inspección queda de solo
   lectura — es el equivalente a archivar el papel.

## 6. Lo que es "de mentira" y hay que reemplazar antes de producción

| Área | Estado actual | Qué falta |
|---|---|---|
| Persistencia | En memoria, se pierde al recargar | Backend + base de datos (relacional — el modelo ya es bastante normalizado, ver `types.ts`) |
| Autenticación | Simulada contra lista de usuarios, sin contraseñas reales | Auth real (ej. NextAuth/Auth.js, o el que se decida), sesiones, recuperación de contraseña |
| Evidencia fotográfica | `URL.createObjectURL()` — blobs locales del navegador, no sobreviven un reload | Subida real a storage (S3, Cloudinary, etc.), compresión/thumbnails, CDN |
| Multi-tenant | Una sola instancia, todas las "empresas" comparten los mismos datos de demo | Aislamiento real por empresa a nivel de base de datos |
| Firmas | Canvas dibujado a mano, se guarda como imagen base64 en memoria | Igual necesita ir a storage real; considerar validez legal de firma electrónica si se vuelve relevante |
| Listas/paginación | Todo se carga completo (asume decenas de registros) | Paginación y queries filtradas en servidor antes de que el volumen real lo obligue |
| Tests | No hay | Al menos tests de la lógica de cálculo (`calcularCumplimiento`, estados de NC, etc.) |

## 7. Roadmap sugerido (orden recomendado)

1. Backend + base de datos + migrar `AppDataProvider`/`AuthProvider` a llamadas API reales.
2. Autenticación real + aislamiento multi-tenant por empresa.
3. Storage de archivos real (fotos y firmas) con compresión.
4. Offline-first / PWA — la conectividad en obra es mala; ver conversación con el fundador sobre
   por qué esto es una ventaja competitiva real frente a la competencia (Calidad Cloud y otros).
5. Paginación y performance a medida que crece el volumen de datos.
6. Ampliar a los módulos planeados: seguridad, producción de obra, valorizaciones.

## 8. Contexto de negocio útil

- Fundador: ingeniero civil (no developer), con experiencia trabajando en calidad para
  constructoras — el producto está diseñado desde ese conocimiento del dolor del usuario final.
- Referencia de mercado explícita: "Calidad Cloud" (competidor peruano) — el diseño del
  encabezado de PDF y el login se inspiraron en su formato pero deliberadamente no son idénticos.
- Contacto: jbegazo01@gmail.com
