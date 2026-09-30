"use client";

import { useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { AlertTriangle, CheckCircle2, Clock, Timer } from "lucide-react";
import { nombreProyecto } from "@/lib/mock-data";
import { useAppData } from "@/lib/app-data-context";
import { EstadoBadge, SeveridadBadge } from "@/components/status-badges";
import { NewNCDialog } from "@/components/new-nc-dialog";
import type { EstadoNC, NoConformidad } from "@/lib/types";
import { toast } from "sonner";

const filtros = ["Todas", "Abierta", "En proceso", "Cerrada"] as const;
const HOY = new Date("2026-09-23");

function esVencida(nc: NoConformidad) {
  return nc.estado !== "Cerrada" && new Date(nc.fechaLimite) < HOY;
}

const siguienteEstado: Record<EstadoNC, EstadoNC | null> = {
  Abierta: "En proceso",
  "En proceso": "Cerrada",
  Cerrada: null,
};

export default function NoConformidadesPage() {
  const { noConformidades, avanzarEstadoNC } = useAppData();
  const [filtro, setFiltro] = useState<(typeof filtros)[number]>("Todas");
  const [seleccionada, setSeleccionada] = useState<NoConformidad | null>(null);

  const visibles =
    filtro === "Todas" ? noConformidades : noConformidades.filter((n) => n.estado === filtro);

  const abiertas = noConformidades.filter((n) => n.estado !== "Cerrada");
  const vencidas = noConformidades.filter(esVencida);
  const enProceso = noConformidades.filter((n) => n.estado === "En proceso");
  const cerradas = noConformidades.filter((n) => n.estado === "Cerrada");

  const kpis = [
    { label: "NC abiertas", value: abiertas.length, icon: AlertTriangle, tone: "text-red-600 bg-red-50" },
    { label: "NC vencidas", value: vencidas.length, icon: Timer, tone: "text-amber-600 bg-amber-50" },
    { label: "En proceso", value: enProceso.length, icon: Clock, tone: "text-blue-600 bg-blue-50" },
    { label: "Cerradas", value: cerradas.length, icon: CheckCircle2, tone: "text-emerald-600 bg-emerald-50" },
  ];

  function avanzarEstado(nc: NoConformidad) {
    const nuevoEstado = siguienteEstado[nc.estado];
    if (!nuevoEstado) return;
    avanzarEstadoNC(nc.id, nuevoEstado);
    setSeleccionada((prev) => (prev && prev.id === nc.id ? { ...prev, estado: nuevoEstado } : prev));
    toast.success(`${nc.codigo} ahora está: ${nuevoEstado}`);
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">No Conformidades</h1>
          <p className="text-sm text-muted-foreground">
            Hallazgos de calidad registrados y su seguimiento hasta el cierre.
          </p>
        </div>
        <NewNCDialog />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {kpis.map((kpi) => (
          <Card key={kpi.label}>
            <CardContent className="flex items-center gap-4 pt-6">
              <div className={`flex h-11 w-11 items-center justify-center rounded-lg ${kpi.tone}`}>
                <kpi.icon className="h-5 w-5" />
              </div>
              <div>
                <p className="text-2xl font-semibold leading-none">{kpi.value}</p>
                <p className="mt-1 text-xs text-muted-foreground">{kpi.label}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Tabs value={filtro} onValueChange={(v) => setFiltro(v as (typeof filtros)[number])}>
        <TabsList>
          {filtros.map((f) => (
            <TabsTrigger key={f} value={f}>
              {f}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      <Card>
        <CardContent className="pt-6">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Código</TableHead>
                <TableHead>Proyecto</TableHead>
                <TableHead>Ubicación / Unidad</TableHead>
                <TableHead>Severidad</TableHead>
                <TableHead>Responsable</TableHead>
                <TableHead>Fecha límite</TableHead>
                <TableHead>Estado</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {visibles.map((nc) => (
                <TableRow
                  key={nc.id}
                  className="cursor-pointer"
                  onClick={() => setSeleccionada(nc)}
                >
                  <TableCell className="font-medium">{nc.codigo}</TableCell>
                  <TableCell className="max-w-[160px] truncate text-sm text-muted-foreground">
                    {nombreProyecto(nc.proyectoId)}
                  </TableCell>
                  <TableCell className="max-w-[220px] truncate text-sm">
                    {nc.ubicacion} / {nc.unidadControl}
                  </TableCell>
                  <TableCell>
                    <SeveridadBadge severidad={nc.severidad} />
                  </TableCell>
                  <TableCell className="text-sm">{nc.responsable}</TableCell>
                  <TableCell className="text-sm">
                    <span className={esVencida(nc) ? "font-medium text-red-600" : "text-muted-foreground"}>
                      {nc.fechaLimite}
                      {esVencida(nc) ? " (vencida)" : ""}
                    </span>
                  </TableCell>
                  <TableCell>
                    <EstadoBadge estado={nc.estado} />
                  </TableCell>
                </TableRow>
              ))}
              {visibles.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} className="py-8 text-center text-sm text-muted-foreground">
                    No hay no conformidades en esta categoría.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Dialog open={!!seleccionada} onOpenChange={(o) => !o && setSeleccionada(null)}>
        <DialogContent className="sm:max-w-lg">
          {seleccionada && (
            <>
              <DialogHeader>
                <DialogTitle>{seleccionada.codigo}</DialogTitle>
                <DialogDescription>
                  {nombreProyecto(seleccionada.proyectoId)} — {seleccionada.ubicacion} / {seleccionada.unidadControl}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-3 text-sm">
                <div className="flex items-center gap-2">
                  <SeveridadBadge severidad={seleccionada.severidad} />
                  <EstadoBadge estado={seleccionada.estado} />
                  {esVencida(seleccionada) && (
                    <span className="text-xs font-medium text-red-600">Vencida</span>
                  )}
                </div>
                <p>{seleccionada.descripcion}</p>
                <div className="grid grid-cols-2 gap-2 rounded-md bg-muted px-3 py-2 text-xs">
                  <span className="text-muted-foreground">Responsable</span>
                  <span className="text-right font-medium">{seleccionada.responsable}</span>
                  <span className="text-muted-foreground">Fecha de apertura</span>
                  <span className="text-right font-medium">{seleccionada.fechaApertura}</span>
                  <span className="text-muted-foreground">Fecha límite</span>
                  <span className="text-right font-medium">{seleccionada.fechaLimite}</span>
                  {seleccionada.inspeccionOriginId && (
                    <>
                      <span className="text-muted-foreground">Inspección origen</span>
                      <span className="text-right font-medium">{seleccionada.inspeccionOriginId}</span>
                    </>
                  )}
                </div>
              </div>
              {siguienteEstado[seleccionada.estado] && (
                <Button onClick={() => avanzarEstado(seleccionada)} className="w-full">
                  Mover a &quot;{siguienteEstado[seleccionada.estado]}&quot;
                </Button>
              )}
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
