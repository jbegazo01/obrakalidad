"use client";

import { useEffect, useState } from "react";
import { useAppData } from "@/lib/app-data-context";
import { EstructuraConfigForm } from "@/components/estructura-config-form";
import { UnidadesGrid } from "@/components/unidades-grid";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { proyectos } from "@/lib/mock-data";

export default function EstructuraUbicacionPage() {
  const { estructurasConfig, addEstructura, updateEstructura, removeEstructura, unidadesPlanificadas, addUnidadPlanificada, updateUnidadPlanificada, removeUnidadPlanificada } = useAppData();

  const [selectedProyectoId, setSelectedProyectoId] = useState<string>("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (proyectos.length > 0 && !selectedProyectoId) {
      setSelectedProyectoId(proyectos[0].id);
    }
  }, [proyectos, selectedProyectoId]);

  const selectedProyecto = proyectos.find((p) => p.id === selectedProyectoId);
  const estructura = estructurasConfig.find((e) => e.proyectoId === selectedProyectoId);
  const unidadesDeProy = unidadesPlanificadas.filter((u) => {
    const est = estructurasConfig.find((e) => e.id === u.estructuraId);
    return est?.proyectoId === selectedProyectoId;
  });

  const handleSaveEstructura = (data: { labelUbicacion: string; labelUnidadControl: string }) => {
    setLoading(true);
    try {
      if (estructura) {
        updateEstructura(estructura.id, data);
      } else {
        addEstructura({ proyectoId: selectedProyectoId, ...data });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleAddUnidad = (data: { ubicacion: string; unidadControl: string }) => {
    if (estructura) {
      addUnidadPlanificada({
        estructuraId: estructura.id,
        ubicacion: data.ubicacion,
        unidadControl: data.unidadControl,
      });
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-2">Estructura y Ubicación</h1>
        <p className="text-slate-600">Configura cómo se nombran las ubicaciones y unidades de control en tus inspecciones</p>
      </div>

      <div className="mb-6">
        <label className="block text-sm font-medium text-slate-700 mb-2">Proyecto</label>
        <Select value={selectedProyectoId} onValueChange={(v) => setSelectedProyectoId(v || "")}>
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

      {selectedProyecto && (
        <Tabs defaultValue="estructura" className="w-full">
          <TabsList className="grid w-full grid-cols-2 mb-6">
            <TabsTrigger value="estructura">Configurar estructura</TabsTrigger>
            <TabsTrigger value="unidades">Unidades planificadas</TabsTrigger>
          </TabsList>

          <TabsContent value="estructura" className="space-y-6">
            <div className="bg-white p-6 rounded-lg border border-slate-200">
              <h2 className="text-lg font-semibold text-slate-900 mb-4">
                {estructura ? "Editar estructura" : "Crear estructura"}
              </h2>
              <p className="text-slate-600 mb-6">
                Define los nombres que usarás para las ubicaciones (ej. Piso, Avenida) y las unidades de control (ej. Departamento, Progresiva)
              </p>
              <EstructuraConfigForm
                estructura={estructura}
                onSave={handleSaveEstructura}
                isLoading={loading}
              />
              {estructura && (
                <div className="mt-6 pt-6 border-t border-slate-200">
                  <Button
                    onClick={() => removeEstructura(estructura.id)}
                    variant="destructive"
                    size="sm"
                  >
                    Eliminar estructura
                  </Button>
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="unidades" className="space-y-6">
            <div className="bg-white p-6 rounded-lg border border-slate-200">
              <h2 className="text-lg font-semibold text-slate-900 mb-2">
                Unidades de control planificadas
              </h2>
              <p className="text-slate-600 mb-6">
                Agrega las unidades que esperas inspeccionar. Te ayudará a medir qué porcentaje ya fue inspeccionado.
              </p>

              {!estructura ? (
                <p className="text-slate-500 py-8 text-center">
                  Primero configura la estructura en la pestaña anterior
                </p>
              ) : (
                <UnidadesGrid
                  unidades={unidadesDeProy}
                  estructura={estructura}
                  onAdd={handleAddUnidad}
                  onUpdate={(id, data) => updateUnidadPlanificada(id, data)}
                  onRemove={removeUnidadPlanificada}
                />
              )}
            </div>
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
}
