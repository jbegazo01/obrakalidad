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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useAppData } from "@/lib/app-data-context";
import { coloresDisponibles, colorEtiquetaDot } from "@/lib/color-map";
import type { ColorEtiqueta } from "@/lib/types";
import { toast } from "sonner";

export function NewSeveridadDialog() {
  const { addSeveridad } = useAppData();
  const [open, setOpen] = useState(false);
  const [nombre, setNombre] = useState("");
  const [color, setColor] = useState<ColorEtiqueta | "">("");
  const [diasSla, setDiasSla] = useState("7");

  const puedeGuardar = nombre.trim() && color && Number(diasSla) > 0;

  function resetForm() {
    setNombre("");
    setColor("");
    setDiasSla("7");
  }

  function handleSubmit() {
    if (!puedeGuardar) return;
    addSeveridad({ nombre: nombre.trim(), color: color as ColorEtiqueta, diasSla: Number(diasSla) });
    toast.success(`Severidad "${nombre.trim()}" creada`);
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
            Nueva severidad
          </Button>
        }
      />
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>Nueva severidad</DialogTitle>
          <DialogDescription>
            Define el estándar de clasificación de hallazgos de tu empresa.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label>Nombre</Label>
            <Input
              placeholder="Ej. Observación leve"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label>Color</Label>
            <Select
              items={Object.fromEntries(coloresDisponibles.map((c) => [c.value, c.label]))}
              value={color}
              onValueChange={(v) => setColor((v ?? "") as ColorEtiqueta)}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Selecciona un color" />
              </SelectTrigger>
              <SelectContent>
                {coloresDisponibles.map((c) => (
                  <SelectItem key={c.value} value={c.value}>
                    <span className={`inline-block h-2.5 w-2.5 rounded-full ${colorEtiquetaDot[c.value]}`} />
                    {c.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>Días para levantamiento (SLA)</Label>
            <Input
              type="number"
              min={1}
              value={diasSla}
              onChange={(e) => setDiasSla(e.target.value)}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancelar
          </Button>
          <Button onClick={handleSubmit} disabled={!puedeGuardar}>
            Crear
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
