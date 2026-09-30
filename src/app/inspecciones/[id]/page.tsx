"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, FileText, Lock, MessageSquare, Paperclip, Printer } from "lucide-react";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { EvidenceUploader } from "@/components/evidence-uploader";
import { MatrizGrid } from "@/components/matriz-grid";
import { Badge } from "@/components/ui/badge";
import { Table2 } from "lucide-react";
import { nombreProyecto } from "@/lib/mock-data";
import { useAppData } from "@/lib/app-data-context";
import { useAuth } from "@/lib/auth-context";
import { EstadoInspeccionBadge, FinalizadaBadge, ResultadoBadge } from "@/components/status-badges";
import { cn } from "@/lib/utils";
import { esMatriz as esRegistroMatriz, progresoSolucion, puedeMarcarComoSolucionada } from "@/lib/inspeccion-utils";
import type { Evidencia, RespuestaCriterio, EstadoRevisionInspeccion } from "@/lib/types";
import { toast } from "sonner";
import { CheckCircle2, Circle } from "lucide-react";

const opcionesRespuesta: { value: RespuestaCriterio; label: string }[] = [
  { value: "cumple", label: "Cumple" },
  { value: "no_cumple", label: "No cumple" },
  { value: "no_aplica", label: "No aplica" },
];

type DialogoActivo = { itemId: string; tipo: "comentario" | "evidencia" };

function EvidenciaThumbs({ evidencias }: { evidencias: Evidencia[] }) {
  if (evidencias.length === 0) return null;
  return (
    <div className="mt-1.5 flex flex-wrap gap-1.5">
      {evidencias.map((ev) => (
        <a
          key={ev.id}
          href={ev.url}
          target="_blank"
          rel="noreferrer"
          className="block h-14 w-14 overflow-hidden rounded border bg-muted"
          title={ev.nombre}
        >
          {ev.tipo === "imagen" ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={ev.url} alt={ev.nombre} className="h-full w-full object-cover" />
          ) : (
            <div className="flex h-full w-full items-center justify-center">
              <FileText className="h-4 w-4 text-muted-foreground" />
            </div>
          )}
        </a>
      ))}
    </div>
  );
}

function formatearFecha(iso?: string) {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("es-PE");
}

export default function DetalleInspeccionPage() {
  const { id } = useParams<{ id: string }>();
  const { usuarioActual } = useAuth();
  const {
    inspecciones,
    marcarCriterioSolucionado,
    marcarInspeccionSolucionada,
    actualizarItemCriterio,
    actualizarGeneral,
    actualizarValorMatriz,
    finalizarInspeccion,
    agregarRegistroRevision,
    obtenerRolesDeRevision,
  } = useAppData();
  const inspeccion = inspecciones.find((i) => i.id === id);
  const [dialogoActivo, setDialogoActivo] = useState<DialogoActivo | null>(null);
  const [dialogoCambioRevisionAbierto, setDialogoCambioRevisionAbierto] = useState(false);
  const [comentarioRevision, setComentarioRevision] = useState("");

  // Función para agregar registro de revisión
  const handleAgregarRevision = () => {
    if (!inspeccion || !usuarioActual) return;
    agregarRegistroRevision({
      inspeccionId: inspeccion.id,
      rol: usuarioActual.rol,
      nombreRevisor: usuarioActual.nombre,
      comentario: comentarioRevision.trim() || undefined,
    });
    toast.success(`Revisión registrada como ${usuarioActual.rol}`);
    setDialogoCambioRevisionAbierto(false);
    setComentarioRevision("");
  };

  // Verificar si el usuario ya revisó
  const usuarioYaReviso = usuarioActual
    ? (inspeccion?.registrosRevision ?? []).some((r) => r.rol === usuarioActual.rol)
    : false;

  if (!inspeccion) {
    return (
      <div className="flex flex-col items-center gap-3 py-16 text-center">
        <p className="text-sm text-muted-foreground">
          No se encontró la inspección. Es posible que la página se haya recargado y se perdieran
          los datos de esta sesión de demostración.
        </p>
        <Link href="/inspecciones" className="text-sm font-medium text-primary hover:underline">
          Volver a Inspecciones
        </Link>
      </div>
    );
  }

  const bloqueada = inspeccion.finalizada;
  const esMatriz = esRegistroMatriz(inspeccion);
  const progreso = progresoSolucion(inspeccion);
  const puedeMarcar = puedeMarcarComoSolucionada(inspeccion);
  const tieneHallazgos = inspeccion.resultado !== "Aprobado";
  const itemActivo = inspeccion.items.find((i) => i.id === dialogoActivo?.itemId) ?? null;
  const mostrarObservacionesGenerales =
    !bloqueada || inspeccion.comentarioGeneral || inspeccion.evidenciasGenerales.length > 0;

  // Lógica para determinar si se puede finalizar
  const puedeFinalizar = esMatriz
    ? true
    : inspeccion.cumplimiento === 100 && inspeccion.resultado === "Aprobado";
  const razonNoFinalizar = !esMatriz && inspeccion.cumplimiento !== 100
    ? "El cumplimiento debe ser 100% para finalizar"
    : !esMatriz && inspeccion.resultado !== "Aprobado"
    ? "La inspección solo se puede finalizar si el resultado es Aprobado"
    : null;

  function handleMarcarSolucionada() {
    marcarInspeccionSolucionada(inspeccion!.id);
    toast.success(`${inspeccion!.codigo} marcada como Solucionada`);
  }

  function handleFinalizar() {
    finalizarInspeccion(inspeccion!.id);
    toast.success(`${inspeccion!.codigo} finalizada y archivada`);
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="/inspecciones"
            className={cn(buttonVariants({ variant: "outline", size: "icon" }))}
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">{inspeccion.codigo}</h1>
            <p className="text-sm text-muted-foreground">
              {nombreProyecto(inspeccion.proyectoId)} — {inspeccion.ubicacion} / {inspeccion.unidadControl}
            </p>
          </div>
        </div>
        <Link
          href={`/inspecciones/${inspeccion.id}/imprimir`}
          className={cn(buttonVariants({ variant: "outline" }))}
        >
          <Printer className="h-4 w-4" />
          Exportar PDF / Imprimir
        </Link>
      </div>

      <Card>
        <CardContent className="flex flex-wrap items-center justify-between gap-3 pt-6 text-sm">
          <span>
            Inspector: <span className="font-medium">{inspeccion.inspector}</span> · {inspeccion.fecha}
            {!esMatriz && (
              <>
                {" · "}
                Cumplimiento: <span className="font-medium">{inspeccion.cumplimiento}%</span>
              </>
            )}
          </span>
          <div className="flex items-center gap-2">
            {esMatriz ? (
              <Badge className="gap-1 bg-violet-100 text-violet-700 hover:bg-violet-100">
                <Table2 className="h-3 w-3" />
                Matriz de datos
              </Badge>
            ) : (
              <>
                {inspeccion.estado === "Solucionado" && (
                  <ResultadoBadge resultado={inspeccion.resultado} />
                )}
                <EstadoInspeccionBadge inspeccion={inspeccion} />
              </>
            )}
            {bloqueada && <FinalizadaBadge />}
          </div>
        </CardContent>
      </Card>

      {/* Panel de Revisiones */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Estado de Revisión</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Estado actual:</p>
              <Badge className="mt-1 bg-blue-100 text-blue-700 hover:bg-blue-100">
                {inspeccion.estadoRevision}
              </Badge>
            </div>

            <div>
              <p className="text-sm font-medium text-muted-foreground mb-2">Historial de revisiones:</p>
              <div className="space-y-2">
                {(inspeccion.registrosRevision ?? []).length > 0 ? (
                  (inspeccion.registrosRevision ?? []).map((registro) => (
                    <div key={registro.id} className="flex items-start gap-3 rounded-lg bg-slate-50 p-3">
                      <CheckCircle2 className="h-4 w-4 text-emerald-600 mt-0.5 shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium">
                          {registro.nombreRevisor}
                          <span className="text-muted-foreground font-normal"> ({registro.rol})</span>
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(registro.fechaHora).toLocaleDateString("es-PE")} {" "}
                          {new Date(registro.fechaHora).toLocaleTimeString("es-PE", { hour: "2-digit", minute: "2-digit" })}
                        </p>
                        {registro.comentario && <p className="text-xs mt-1">{registro.comentario}</p>}
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground">Sin revisiones aún</p>
                )}
              </div>
            </div>

            <div>
              <p className="text-sm font-medium text-muted-foreground mb-2">Roles de revisión:</p>
              <div className="space-y-2">
                {obtenerRolesDeRevision(inspeccion.proyectoId).map((rol) => {
                  const yaReviso = inspeccion.registrosRevision.some((r) => r.rol === rol);
                  return (
                    <div key={rol} className="flex items-center gap-2">
                      {yaReviso ? (
                        <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                      ) : (
                        <Circle className="h-4 w-4 text-muted-foreground" />
                      )}
                      <span className={`text-sm ${yaReviso ? "text-emerald-700 font-medium" : "text-muted-foreground"}`}>
                        {rol}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {usuarioActual && !usuarioYaReviso && (
              <Button
                onClick={() => setDialogoCambioRevisionAbierto(true)}
                className="mt-2"
              >
                Registrar revisión
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {!esMatriz && tieneHallazgos && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Trazabilidad de solución</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {inspeccion.estado === "Solucionado" ? (
              <p className="rounded-md bg-blue-50 px-3 py-2 text-sm text-blue-700">
                Inspección marcada como Solucionada el {formatearFecha(inspeccion.fechaSolucionInspeccion)}.
              </p>
            ) : (
              <>
                <div className="flex items-center gap-3">
                  <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full rounded-full bg-primary"
                      style={{
                        width: `${progreso.total === 0 ? 0 : Math.round((progreso.solucionados / progreso.total) * 100)}%`,
                      }}
                    />
                  </div>
                  <span className="shrink-0 text-xs text-muted-foreground">
                    {progreso.solucionados} de {progreso.total} criterios solucionados
                  </span>
                </div>
                {!bloqueada && (
                  <>
                    <Button onClick={handleMarcarSolucionada} disabled={!puedeMarcar}>
                      Marcar inspección como Solucionada
                    </Button>
                    {!puedeMarcar && (
                      <p className="text-xs text-muted-foreground">
                        Marca como solucionados todos los criterios &quot;No cumple&quot; de abajo
                        para habilitar este botón.
                      </p>
                    )}
                  </>
                )}
              </>
            )}
          </CardContent>
        </Card>
      )}

      {esMatriz ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Matriz de datos</CardTitle>
            {!bloqueada && (
              <p className="text-xs text-muted-foreground">
                Registro informativo — puedes seguir completando o corrigiendo celdas mientras no
                esté finalizada.
              </p>
            )}
          </CardHeader>
          <CardContent>
            <MatrizGrid
              columnas={inspeccion.matrizColumnas ?? []}
              filas={inspeccion.matrizFilas ?? []}
              valores={inspeccion.matrizValores ?? {}}
              editable={!bloqueada}
              onChange={(clave, valor) => actualizarValorMatriz(inspeccion.id, clave, valor)}
            />
          </CardContent>
        </Card>
      ) : (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Checklist</CardTitle>
          {!bloqueada && (
            <p className="text-xs text-muted-foreground">
              Puedes corregir la respuesta, el comentario o la evidencia de cualquier criterio
              mientras la inspección no esté finalizada — por ejemplo, si algo dado por conforme
              luego resultó con un error.
            </p>
          )}
        </CardHeader>
        <CardContent className="space-y-4">
          {inspeccion.items.map((item, idx) => (
            <div
              key={item.id}
              className="flex items-start justify-between gap-3 border-b pb-4 text-sm last:border-b-0 last:pb-0"
            >
              <div className="min-w-0 flex-1 space-y-2">
                <p className={item.solucionado ? "text-muted-foreground line-through" : ""}>
                  <span className="text-muted-foreground">{idx + 1}.</span> {item.descripcion}
                </p>

                {bloqueada ? (
                  <p className="text-xs font-medium text-muted-foreground">
                    {item.respuesta === "cumple" && "✓ Cumple"}
                    {item.respuesta === "no_cumple" && "✗ No cumple"}
                    {item.respuesta === "no_aplica" && "— No aplica"}
                  </p>
                ) : (
                  <RadioGroup
                    className="flex flex-wrap gap-4"
                    value={item.respuesta ?? ""}
                    onValueChange={(v) =>
                      actualizarItemCriterio(inspeccion.id, item.id, {
                        respuesta: v as RespuestaCriterio,
                      })
                    }
                  >
                    {opcionesRespuesta.map((op) => (
                      <div key={op.value} className="flex items-center gap-2">
                        <RadioGroupItem value={op.value} id={`${item.id}-${op.value}`} />
                        <Label htmlFor={`${item.id}-${op.value}`} className="text-sm font-normal">
                          {op.label}
                        </Label>
                      </div>
                    ))}
                  </RadioGroup>
                )}

                {item.comentario && <p className="text-xs text-muted-foreground">{item.comentario}</p>}
                <EvidenciaThumbs evidencias={item.evidencias} />

                {item.respuesta === "no_cumple" && (
                  <label className="mt-2 flex items-center gap-2 text-xs">
                    <Checkbox
                      checked={!!item.solucionado}
                      disabled={bloqueada}
                      onCheckedChange={(checked) =>
                        marcarCriterioSolucionado(inspeccion.id, item.id, checked === true)
                      }
                    />
                    {item.solucionado ? (
                      <span className="font-medium text-emerald-700">
                        Solucionado · {formatearFecha(item.fechaSolucion)}
                      </span>
                    ) : (
                      <span className="text-muted-foreground">Marcar como solucionado</span>
                    )}
                  </label>
                )}
              </div>

              {!bloqueada && (
                <div className="flex shrink-0 items-center gap-1 pt-0.5">
                  <Button
                    type="button"
                    variant={item.comentario ? "secondary" : "ghost"}
                    size="icon-sm"
                    title="Dejar comentario"
                    onClick={() => setDialogoActivo({ itemId: item.id, tipo: "comentario" })}
                  >
                    <MessageSquare className="h-4 w-4" />
                  </Button>
                  <Button
                    type="button"
                    variant={item.evidencias.length > 0 ? "secondary" : "ghost"}
                    size="icon-sm"
                    className="relative"
                    title="Adjuntar evidencia"
                    onClick={() => setDialogoActivo({ itemId: item.id, tipo: "evidencia" })}
                  >
                    <Paperclip className="h-4 w-4" />
                    {item.evidencias.length > 0 && (
                      <span className="absolute -top-1 -right-1 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-primary text-[9px] font-medium text-primary-foreground">
                        {item.evidencias.length}
                      </span>
                    )}
                  </Button>
                </div>
              )}
            </div>
          ))}
        </CardContent>
      </Card>
      )}

      {mostrarObservacionesGenerales && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Observaciones generales</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {bloqueada ? (
              <>
                {inspeccion.comentarioGeneral && (
                  <p className="text-sm text-muted-foreground">{inspeccion.comentarioGeneral}</p>
                )}
                <EvidenciaThumbs evidencias={inspeccion.evidenciasGenerales} />
              </>
            ) : (
              <>
                <Textarea
                  placeholder="Comentario general sobre la inspección (opcional)"
                  value={inspeccion.comentarioGeneral ?? ""}
                  onChange={(e) =>
                    actualizarGeneral(inspeccion.id, { comentarioGeneral: e.target.value })
                  }
                />
                <EvidenceUploader
                  evidencias={inspeccion.evidenciasGenerales}
                  onAdd={(nuevas) =>
                    actualizarGeneral(inspeccion.id, {
                      evidenciasGenerales: [...inspeccion.evidenciasGenerales, ...nuevas],
                    })
                  }
                  onRemove={(evId) =>
                    actualizarGeneral(inspeccion.id, {
                      evidenciasGenerales: inspeccion.evidenciasGenerales.filter((e) => e.id !== evId),
                    })
                  }
                  label="Adjuntar evidencia general"
                />
              </>
            )}
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Finalizar inspección</CardTitle>
        </CardHeader>
        <CardContent>
          {bloqueada ? (
            <p className="flex items-center gap-2 rounded-md bg-slate-100 px-3 py-2 text-sm text-slate-700">
              <Lock className="h-4 w-4 shrink-0" />
              Finalizada y archivada el {formatearFecha(inspeccion.fechaFinalizacion)}. Ya no se
              puede modificar.
            </p>
          ) : (
            <div className="space-y-2">
              <p className="text-sm text-muted-foreground">
                Una vez finalizada, la inspección queda archivada y de solo lectura — represéntalo
                como guardar la copia final en el file de obra. Hasta entonces, puedes seguir
                corrigiendo criterios y su estado de solución.
              </p>
              {!puedeFinalizar && razonNoFinalizar && (
                <p className="text-sm text-amber-600 bg-amber-50 rounded px-3 py-2">
                  {razonNoFinalizar}
                </p>
              )}
              <Button variant="outline" onClick={handleFinalizar} disabled={!puedeFinalizar}>
                <Lock className="h-4 w-4" />
                Finalizar inspección
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={!!dialogoActivo} onOpenChange={(o) => !o && setDialogoActivo(null)}>
        <DialogContent className="sm:max-w-sm">
          {itemActivo && dialogoActivo?.tipo === "comentario" && (
            <>
              <DialogHeader>
                <DialogTitle>Comentario del criterio</DialogTitle>
                <DialogDescription>{itemActivo.descripcion}</DialogDescription>
              </DialogHeader>
              <Textarea
                autoFocus
                placeholder="Escribe un comentario..."
                value={itemActivo.comentario ?? ""}
                onChange={(e) =>
                  actualizarItemCriterio(inspeccion.id, itemActivo.id, { comentario: e.target.value })
                }
              />
              <DialogFooter>
                <Button onClick={() => setDialogoActivo(null)}>Listo</Button>
              </DialogFooter>
            </>
          )}
          {itemActivo && dialogoActivo?.tipo === "evidencia" && (
            <>
              <DialogHeader>
                <DialogTitle>Evidencia fotográfica</DialogTitle>
                <DialogDescription>{itemActivo.descripcion}</DialogDescription>
              </DialogHeader>
              <EvidenceUploader
                evidencias={itemActivo.evidencias}
                onAdd={(nuevas) =>
                  actualizarItemCriterio(inspeccion.id, itemActivo.id, {
                    evidencias: [...itemActivo.evidencias, ...nuevas],
                  })
                }
                onRemove={(evId) =>
                  actualizarItemCriterio(inspeccion.id, itemActivo.id, {
                    evidencias: itemActivo.evidencias.filter((e) => e.id !== evId),
                  })
                }
              />
              <DialogFooter>
                <Button onClick={() => setDialogoActivo(null)}>Listo</Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={dialogoCambioRevisionAbierto} onOpenChange={setDialogoCambioRevisionAbierto}>
        <DialogContent className="sm:max-w-sm">
          <DialogHeader>
            <DialogTitle>Registrar revisión</DialogTitle>
            <DialogDescription>
              Registra tu revisión como {usuarioActual?.rol}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <p className="text-sm font-medium text-muted-foreground mb-2">Estado actual:</p>
              <Badge className="bg-blue-100 text-blue-700 hover:bg-blue-100">
                {inspeccion.estadoRevision}
              </Badge>
            </div>
            <div>
              <Label htmlFor="comentario-revision" className="text-sm">
                Comentario (opcional)
              </Label>
              <Textarea
                id="comentario-revision"
                placeholder="Escribe un comentario sobre tu revisión..."
                value={comentarioRevision}
                onChange={(e) => setComentarioRevision(e.target.value)}
                className="mt-2"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setDialogoCambioRevisionAbierto(false);
                setComentarioRevision("");
              }}
            >
              Cancelar
            </Button>
            <Button onClick={handleAgregarRevision}>
              Registrar revisión
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
