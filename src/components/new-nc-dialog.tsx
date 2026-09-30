"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { proyectos } from "@/lib/mock-data";
import { useAppData } from "@/lib/app-data-context";
import { toast } from "sonner";

function sumarDias(fechaISO: string, dias: number) {
  const fecha = new Date(fechaISO);
  fecha.setDate(fecha.getDate() + dias);
  return fecha.toISOString().slice(0, 10);
}

export function NewNCDialog() {
  const { severidades, addNoConformidad } = useAppData();
  const [open, setOpen] = useState(false);
  const [proyectoId, setProyectoId] = useState("");
  const [partida, setPartida] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [severidad, setSeveridad] = useState("");
  const [responsable, setResponsable] = useState("");
  const [fechaLimite, setFechaLimite] = useState("");
  const [fechaLimiteEditada, setFechaLimiteEditada] = useState(false);

  const puedeGuardar = proyectoId && partida && descripcion && severidad && responsable && fechaLimite;

  function resetForm() {
    setProyectoId("");
    setPartida("");
    setDescripcion("");
    setSeveridad("");
    setResponsable("");
    setFechaLimite("");
    setFechaLimiteEditada(false);
  }

  function handleSeveridadChange(value: string | null) {
    const nombre = value ?? "";
    setSeveridad(nombre);
    const config = severidades.find((s) => s.nombre === nombre);
    if (config && !fechaLimiteEditada) {
      setFechaLimite(sumarDias(new Date().toISOString().slice(0, 10), config.diasSla));
    }
  }

  function handleSubmit() {
    if (!puedeGuardar) return;
    const nueva = addNoConformidad({
      proyectoId,
      partida,
      descripcion,
      severidad,
      responsable,
      fechaLimite,
    });
    toast.success(`${nueva.codigo} registrada`);
    resetForm();
    setOpen(false);
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        setOpen(o);
        if (!o) resetForm();
      }}
    >
      <DialogTrigger
        render={
          <Button>
            <Plus className="h-4 w-4" />
            Nueva No Conformidad
          </Button>
        }
      />
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Registrar no conformidad</DialogTitle>
          <DialogDescription>
            Documenta el hallazgo para hacer seguimiento hasta su cierre.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label>Proyecto</Label>
              <Select
                items={Object.fromEntries(proyectos.map((p) => [p.id, p.nombre]))}
                value={proyectoId}
                onValueChange={(v) => setProyectoId(v ?? "")}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Selecciona un proyecto" />
                </SelectTrigger>
                <SelectContent>
                  {proyectos.map((p) => (
                    <SelectItem key={p.id} value={p.id}>
                      {p.nombre}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Severidad</Label>
              <Select value={severidad} onValueChange={handleSeveridadChange}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Selecciona severidad" />
                </SelectTrigger>
                <SelectContent>
                  {severidades.map((s) => (
                    <SelectItem key={s.id} value={s.nombre}>
                      {s.nombre}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-1.5">
            <Label>Partida</Label>
            <Input
              placeholder="Ej. Acero de refuerzo - Zapatas sector B"
              value={partida}
              onChange={(e) => setPartida(e.target.value)}
            />
          </div>

          <div className="space-y-1.5">
            <Label>Descripción del hallazgo</Label>
            <Textarea
              placeholder="Describe la desviación encontrada respecto a la especificación..."
              value={descripcion}
              onChange={(e) => setDescripcion(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label>Responsable</Label>
              <Input
                placeholder="Ej. Ing. Carlos Mendoza"
                value={responsable}
                onChange={(e) => setResponsable(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label>Fecha límite de levantamiento</Label>
              <Input
                type="date"
                value={fechaLimite}
                onChange={(e) => {
                  setFechaLimiteEditada(true);
                  setFechaLimite(e.target.value);
                }}
              />
              {severidad && (
                <p className="text-xs text-muted-foreground">
                  Sugerida según SLA de &quot;{severidad}&quot;. Puedes ajustarla.
                </p>
              )}
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancelar
          </Button>
          <Button onClick={handleSubmit} disabled={!puedeGuardar}>
            Registrar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
