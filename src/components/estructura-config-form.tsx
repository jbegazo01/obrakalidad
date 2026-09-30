"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ConfigEstructura } from "@/lib/types";

interface EstructuraConfigFormProps {
  estructura?: ConfigEstructura;
  onSave: (data: { labelUbicacion: string; labelUnidadControl: string }) => void;
  isLoading?: boolean;
}

export function EstructuraConfigForm({ estructura, onSave, isLoading }: EstructuraConfigFormProps) {
  const [labelUbicacion, setLabelUbicacion] = useState(estructura?.labelUbicacion ?? "");
  const [labelUnidadControl, setLabelUnidadControl] = useState(estructura?.labelUnidadControl ?? "");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!labelUbicacion.trim() || !labelUnidadControl.trim()) {
      return;
    }
    onSave({ labelUbicacion, labelUnidadControl });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="space-y-2">
        <label className="block text-sm font-medium text-slate-700">
          Etiqueta para "Ubicación"
        </label>
        <Input
          type="text"
          placeholder="e.g. Piso, Avenida, Nivel"
          value={labelUbicacion}
          onChange={(e) => setLabelUbicacion(e.target.value)}
          className="w-full"
        />
        <p className="text-xs text-slate-500">Nombre que aparecerá en los formularios</p>
      </div>

      <div className="space-y-2">
        <label className="block text-sm font-medium text-slate-700">
          Etiqueta para "Unidad de Control"
        </label>
        <Input
          type="text"
          placeholder="e.g. Departamento, Progresiva, Sector"
          value={labelUnidadControl}
          onChange={(e) => setLabelUnidadControl(e.target.value)}
          className="w-full"
        />
        <p className="text-xs text-slate-500">Nombre que aparecerá en los formularios</p>
      </div>

      <Button type="submit" disabled={isLoading || !labelUbicacion.trim() || !labelUnidadControl.trim()}>
        {isLoading ? "Guardando..." : "Guardar"}
      </Button>
    </form>
  );
}
