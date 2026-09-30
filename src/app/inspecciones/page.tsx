"use client";

import { useState } from "react";
import Link from "next/link";
import {
  CheckCircle2,
  ClipboardCheck,
  ShieldCheck,
  ThumbsDown,
  Table2,
} from "lucide-react";
import { useAppData } from "@/lib/app-data-context";
import { useProjectSelection } from "@/lib/project-selection-context";
import { esMatriz } from "@/lib/inspeccion-utils";
import { InspectionSectionHeader } from "@/components/inspection-section-header";
import { InspectionKpiCard } from "@/components/inspection-kpi-card";
import { InspectionTableEnhanced } from "@/components/inspection-table-enhanced";
import { AdvancedFilterPanel } from "@/components/advanced-filter-panel";
import { cn } from "@/lib/utils";
import type { ResultadoInspeccion } from "@/lib/types";

export default function InspeccionesPage() {
  const { inspecciones } = useAppData();
  const { proyectoSeleccionado } = useProjectSelection();

  // Estado de pestaña activa
  const [pestañaActiva, setPestañaActiva] = useState<"indicadores" | "inspecciones">("inspecciones");

  // Estados de filtros
  const [searchTerm, setSearchTerm] = useState("");
  const [resultado, setResultado] = useState("todos");
  const [estadoRevision, setEstadoRevision] = useState("todos");
  const [inspector, setInspector] = useState("todos");
  const [tipo, setTipo] = useState("todos");
  const [estadoSolucion, setEstadoSolucion] = useState("todos");
  const [fechaDesde, setFechaDesde] = useState("");
  const [fechaHasta, setFechaHasta] = useState("");

  const inspeccionesFiltradas = inspecciones.filter(
    (i) => i.proyectoId === proyectoSeleccionado
  );

  // Aplicar todos los filtros
  const visibles = inspeccionesFiltradas.filter((i) => {
    // Búsqueda
    const matchSearch =
      i.codigo.toLowerCase().includes(searchTerm.toLowerCase()) ||
      i.ubicacion.toLowerCase().includes(searchTerm.toLowerCase()) ||
      i.inspector.toLowerCase().includes(searchTerm.toLowerCase());

    // Resultado
    const matchResultado = resultado === "todos" || i.resultado === resultado;

    // Estado de Revisión
    const matchEstadoRevision = estadoRevision === "todos" || i.estadoRevision === estadoRevision;

    // Inspector
    const matchInspector = inspector === "todos" || i.inspector === inspector;

    // Tipo/Partida
    const matchTipo = tipo === "todos" || i.tipo === tipo;

    // Estado de Solución
    const matchEstadoSolucion =
      estadoSolucion === "todos" || i.estado === estadoSolucion;

    // Fechas
    const fechaInspeccion = new Date(i.fecha);
    const matchFechaDesde = !fechaDesde || fechaInspeccion >= new Date(fechaDesde);
    const matchFechaHasta = !fechaHasta || fechaInspeccion <= new Date(fechaHasta);

    return (
      matchSearch &&
      matchResultado &&
      matchEstadoRevision &&
      matchInspector &&
      matchTipo &&
      matchEstadoSolucion &&
      matchFechaDesde &&
      matchFechaHasta
    );
  });

  // Calcular cantidad de filtros activos
  const activeFilterCount = [
    searchTerm,
    resultado !== "todos",
    estadoRevision !== "todos",
    inspector !== "todos",
    tipo !== "todos",
    estadoSolucion !== "todos",
    fechaDesde,
    fechaHasta,
  ].filter(Boolean).length;

  // Limpiar filtros
  const handleClearFilters = () => {
    setSearchTerm("");
    setResultado("todos");
    setEstadoRevision("todos");
    setInspector("todos");
    setTipo("todos");
    setEstadoSolucion("todos");
    setFechaDesde("");
    setFechaHasta("");
  };

  // Cálculos de KPIs
  const deConformidad = inspeccionesFiltradas.filter((i) => !esMatriz(i));
  const cumplimientoPromedio = deConformidad.length
    ? Math.round(deConformidad.reduce((acc, i) => acc + i.cumplimiento, 0) / deConformidad.length)
    : 0;
  const aprobadas = deConformidad.filter((i) => i.resultado === "Aprobado").length;
  const enProceso = deConformidad.filter((i) => i.resultado === "En Proceso").length;
  const fallas = deConformidad.filter((i) => i.resultado === "Falla").length;

  const tiposDisponibles = Array.from(new Set(inspeccionesFiltradas.map((i) => i.tipo)));
  const inspectoresDisponibles = Array.from(new Set(inspeccionesFiltradas.map((i) => i.inspector)));

  return (
    <div className="space-y-6">
      {/* Header de sección */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <InspectionSectionHeader
            title="Inspecciones de Calidad"
            subtitle="Checklists de calidad digitalizados por partida, frente de trabajo y protocolo técnico según norma técnica y Espec. QA/QC."
            activeCount={inspeccionesFiltradas.length}
          />
        </div>
        <Link href="/inspecciones/registro">
          <button className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 text-white px-4 py-2 text-sm font-medium hover:bg-indigo-700 transition-colors mt-2">
            <Table2 className="h-4 w-4" />
            Vista Registro
          </button>
        </Link>
      </div>

      {/* Pestañas */}
      <div className="border-b border-slate-200">
        <div className="flex gap-8">
          <button
            onClick={() => setPestañaActiva("inspecciones")}
            className={cn(
              "px-1 py-3 text-sm font-medium border-b-2 transition-colors",
              pestañaActiva === "inspecciones"
                ? "text-primary border-primary"
                : "text-muted-foreground border-transparent hover:text-foreground"
            )}
          >
            Inspecciones
          </button>
          <button
            onClick={() => setPestañaActiva("indicadores")}
            className={cn(
              "px-1 py-3 text-sm font-medium border-b-2 transition-colors",
              pestañaActiva === "indicadores"
                ? "text-primary border-primary"
                : "text-muted-foreground border-transparent hover:text-foreground"
            )}
          >
            Indicadores
          </button>
        </div>
      </div>

      {/* Contenido de Inspecciones */}
      {pestañaActiva === "inspecciones" && (
        <div className="space-y-6">
          {/* Panel de filtros avanzados */}
          <AdvancedFilterPanel
            searchTerm={searchTerm}
            onSearchChange={setSearchTerm}
            resultado={resultado}
            onResultadoChange={setResultado}
            estadoRevision={estadoRevision}
            onEstadoRevisionChange={setEstadoRevision}
            inspector={inspector}
            onInspectorChange={setInspector}
            tipo={tipo}
            onTipoChange={setTipo}
            estadoSolucion={estadoSolucion}
            onEstadoSolucionChange={setEstadoSolucion}
            fechaDesde={fechaDesde}
            onFechaDesdeChange={setFechaDesde}
            fechaHasta={fechaHasta}
            onFechaHastaChange={setFechaHasta}
            tiposDisponibles={tiposDisponibles}
            inspectoresDisponibles={inspectoresDisponibles}
            onClearFilters={handleClearFilters}
            activeFilterCount={activeFilterCount}
          />

          {/* Tabla mejorada */}
          <InspectionTableEnhanced inspecciones={visibles} />
        </div>
      )}

      {/* Contenido de Indicadores */}
      {pestañaActiva === "indicadores" && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <InspectionKpiCard
            label="Inspecciones Registradas"
            value={inspeccionesFiltradas.length}
            subtitle="+2 programadas esta semana"
            icon={ClipboardCheck}
            tone="info"
            trend={{ value: "+2", direction: "up" }}
          />
          <InspectionKpiCard
            label="Cumplimiento Promedio"
            value={`${cumplimientoPromedio}%`}
            subtitle="Alineado a meta del proyecto (>85%)"
            icon={ShieldCheck}
            tone="success"
            trend={{ value: "+3.5%", direction: "up" }}
          />
          <InspectionKpiCard
            label="Liberadas Conforme"
            value={aprobadas}
            subtitle="60% del frente actual apto para colada"
            icon={CheckCircle2}
            tone="success"
          />
          <InspectionKpiCard
            label="En Proceso / Fallas"
            value={`${enProceso} / ${fallas}`}
            subtitle="Pendiente de revisión o incumplimientos"
            icon={ThumbsDown}
            tone={enProceso + fallas > 0 ? "warning" : "info"}
          />
        </div>
      )}
    </div>
  );
}
