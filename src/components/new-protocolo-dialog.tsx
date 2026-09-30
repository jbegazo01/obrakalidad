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
import type { TipoProtocolo } from "@/lib/types";
import { toast } from "sonner";

const tiposProtocolo: { value: TipoProtocolo; label: string; descripcion: string }[] = [
  {
    value: "checklist",
    label: "Checklist de conformidad",
    descripcion: "Criterios Cumple / No cumple / No aplica, con % de cumplimiento y resultado.",
  },
  {
    value: "matriz",
    label: "Matriz de datos",
    descripcion: "Tabla libre (filas x columnas) para tomar información. No calcula cumplimiento.",
  },
];

export function NewProtocoloDialog() {
  const { addProtocolo, etapasConstructivas } = useAppData();
  const [open, setOpen] = useState(false);
  const [nombre, setNombre] = useState("");
  const [tipo, setTipo] = useState<TipoProtocolo>("checklist");
  const [etapaId, setEtapaId] = useState<string>(
    etapasConstructivas[0]?.id || "etapa-1"
  );

  function handleSubmit() {
    if (!nombre.trim() || !etapaId) return;
    addProtocolo(nombre.trim(), tipo, etapaId);
    toast.success(`Protocolo "${nombre.trim()}" creado`);
    setNombre("");
    setTipo("checklist");
    setEtapaId(etapasConstructivas[0]?.id || "");
    setOpen(false);
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger
        render={
          <Button>
            <Plus className="h-4 w-4" />
            Nuevo protocolo
          </Button>
        }
      />
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>Nuevo protocolo de inspección</DialogTitle>
          <DialogDescription>
            Ej. Pintura, Carpintería metálica, Control de niveles. Luego agrega sus criterios o su
            estructura de tabla.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label>Nombre del protocolo</Label>
            <Input
              placeholder="Ej. Pintura"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            />
          </div>
          <div className="space-y-1.5">
            <Label>Etapa constructiva</Label>
            <Select value={etapaId} onValueChange={(v) => setEtapaId(v ?? "etapa-1")}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {etapasConstructivas.map((etapa) => (
                  <SelectItem key={etapa.id} value={etapa.id}>
                    {etapa.nombre}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>Tipo de protocolo</Label>
            <Select value={tipo} onValueChange={(v) => setTipo((v ?? "checklist") as TipoProtocolo)}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {tiposProtocolo.map((t) => (
                  <SelectItem key={t.value} value={t.value}>
                    {t.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              {tiposProtocolo.find((t) => t.value === tipo)?.descripcion}
            </p>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancelar
          </Button>
          <Button onClick={handleSubmit} disabled={!nombre.trim()}>
            Crear
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
