"use client";

import { UnidadPlanificada, ConfigEstructura } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useState } from "react";
import { Trash2, Plus } from "lucide-react";

interface UnidadesGridProps {
  unidades: UnidadPlanificada[];
  estructura?: ConfigEstructura;
  onAdd: (data: { ubicacion: string; unidadControl: string }) => void;
  onUpdate: (id: string, data: Partial<UnidadPlanificada>) => void;
  onRemove: (id: string) => void;
}

export function UnidadesGrid({ unidades, estructura, onAdd, onUpdate, onRemove }: UnidadesGridProps) {
  const [newUbicacion, setNewUbicacion] = useState("");
  const [newUnidadControl, setNewUnidadControl] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);

  const handleAddClick = () => {
    if (!newUbicacion.trim() || !newUnidadControl.trim()) return;
    onAdd({ ubicacion: newUbicacion, unidadControl: newUnidadControl });
    setNewUbicacion("");
    setNewUnidadControl("");
  };

  const ubicacionLabel = estructura?.labelUbicacion ?? "Ubicación";
  const unidadControlLabel = estructura?.labelUnidadControl ?? "Unidad de Control";

  return (
    <div className="space-y-6">
      <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
        <h3 className="text-sm font-semibold text-slate-900 mb-4">Agregar nueva unidad</h3>
        <div className="grid grid-cols-2 gap-4 mb-4">
          <Input
            type="text"
            placeholder={`${ubicacionLabel}...`}
            value={newUbicacion}
            onChange={(e) => setNewUbicacion(e.target.value)}
          />
          <Input
            type="text"
            placeholder={`${unidadControlLabel}...`}
            value={newUnidadControl}
            onChange={(e) => setNewUnidadControl(e.target.value)}
          />
        </div>
        <Button
          onClick={handleAddClick}
          disabled={!newUbicacion.trim() || !newUnidadControl.trim()}
          variant="outline"
          size="sm"
          className="gap-2"
        >
          <Plus className="w-4 h-4" />
          Agregar
        </Button>
      </div>

      {unidades.length === 0 ? (
        <p className="text-center text-slate-500 py-8">No hay unidades planificadas aún</p>
      ) : (
        <div className="border border-slate-200 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-4 py-3 text-left font-semibold text-slate-900">{ubicacionLabel}</th>
                <th className="px-4 py-3 text-left font-semibold text-slate-900">{unidadControlLabel}</th>
                <th className="px-4 py-3 text-left font-semibold text-slate-900">Estado</th>
                <th className="px-4 py-3 text-right font-semibold text-slate-900">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {unidades.map((unidad) => (
                <tr key={unidad.id} className="border-b border-slate-200 hover:bg-slate-50">
                  <td className="px-4 py-3 text-slate-900">{unidad.ubicacion}</td>
                  <td className="px-4 py-3 text-slate-900">{unidad.unidadControl}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        unidad.estado === "liberada"
                          ? "bg-emerald-100 text-emerald-800"
                          : "bg-amber-100 text-amber-800"
                      }`}
                    >
                      {unidad.estado === "liberada" ? "Liberada" : "Pendiente"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Button
                      onClick={() => onRemove(unidad.id)}
                      variant="ghost"
                      size="sm"
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
