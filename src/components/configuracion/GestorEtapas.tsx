"use client";

import { useState } from "react";
import { Plus, Trash2, Edit2 } from "lucide-react";
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
import { useAppData } from "@/lib/app-data-context";
import { toast } from "sonner";

export function GestorEtapas() {
  const { etapasConstructivas, addEtapa, deleteEtapa, updateEtapa } = useAppData();
  const [open, setOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [nombre, setNombre] = useState("");
  const [descripcion, setDescripcion] = useState("");

  function handleSubmit() {
    if (!nombre.trim()) return;

    if (editingId) {
      updateEtapa(editingId, { nombre: nombre.trim(), descripcion: descripcion.trim() });
      toast.success(`Etapa "${nombre.trim()}" actualizada`);
      setEditingId(null);
    } else {
      addEtapa(nombre.trim(), descripcion.trim());
      toast.success(`Etapa "${nombre.trim()}" creada`);
    }

    setNombre("");
    setDescripcion("");
    setOpen(false);
  }

  function handleEdit(etapaId: string) {
    const etapa = etapasConstructivas.find((e) => e.id === etapaId);
    if (etapa) {
      setEditingId(etapaId);
      setNombre(etapa.nombre);
      setDescripcion(etapa.descripcion || "");
      setOpen(true);
    }
  }

  function handleDelete(etapaId: string) {
    const etapa = etapasConstructivas.find((e) => e.id === etapaId);
    if (etapa && confirm(`¿Eliminar etapa "${etapa.nombre}" y sus protocolos asociados?`)) {
      deleteEtapa(etapaId);
      toast.success(`Etapa "${etapa.nombre}" eliminada`);
    }
  }

  function handleOpenChange(isOpen: boolean) {
    if (!isOpen) {
      setEditingId(null);
      setNombre("");
      setDescripcion("");
    }
    setOpen(isOpen);
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">Etapas constructivas</h3>
        <Dialog open={open} onOpenChange={handleOpenChange}>
          <DialogTrigger
            render={
              <Button size="sm">
                <Plus className="h-4 w-4 mr-1" />
                Nueva etapa
              </Button>
            }
          />
          <DialogContent className="sm:max-w-sm">
            <DialogHeader>
              <DialogTitle>{editingId ? "Editar etapa" : "Nueva etapa constructiva"}</DialogTitle>
              <DialogDescription>
                Ej. ESTRUCTURAS, ACABADOS, INSTALACIONES. Define las etapas de tu proyecto.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="space-y-1.5">
                <Label>Nombre de la etapa</Label>
                <Input
                  placeholder="Ej. ESTRUCTURAS"
                  value={nombre}
                  onChange={(e) => setNombre(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
                />
              </div>
              <div className="space-y-1.5">
                <Label>Descripción (opcional)</Label>
                <Textarea
                  placeholder="Ej. Concreto, encofrado, acero y trabajos estructurales"
                  value={descripcion}
                  onChange={(e) => setDescripcion(e.target.value)}
                  className="min-h-20"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => handleOpenChange(false)}>
                Cancelar
              </Button>
              <Button onClick={handleSubmit} disabled={!nombre.trim()}>
                {editingId ? "Guardar" : "Crear"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <div className="space-y-2">
        {etapasConstructivas.length === 0 ? (
          <p className="text-sm text-muted-foreground py-8 text-center">
            No hay etapas definidas. Crea una para comenzar.
          </p>
        ) : (
          <div className="space-y-2">
            {etapasConstructivas.map((etapa) => (
              <div
                key={etapa.id}
                className="flex items-start justify-between p-3 border rounded-lg hover:bg-muted/50 transition"
              >
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm">{etapa.nombre}</p>
                  {etapa.descripcion && (
                    <p className="text-xs text-muted-foreground mt-1">{etapa.descripcion}</p>
                  )}
                </div>
                <div className="flex gap-2 ml-4 flex-shrink-0">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleEdit(etapa.id)}
                    title="Editar"
                  >
                    <Edit2 className="h-4 w-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    className="text-destructive hover:text-destructive"
                    onClick={() => handleDelete(etapa.id)}
                    title="Eliminar"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
