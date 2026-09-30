"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Maximize2, Download, Plus, ChevronLeft } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useAppData } from "@/lib/app-data-context";
import { useProjectSelection } from "@/lib/project-selection-context";
import { InspectionRegistroFilters } from "@/components/inspection-registro-filters";
import { InspectionRegistroTable } from "@/components/inspection-registro-table";
import { nombreProyecto } from "@/lib/mock-data";
import Link from "next/link";
import type { Inspeccion } from "@/lib/types";

type DensityType = "normal" | "compact" | "ultra";

export default function InspeccionesRegistroPage() {
  const router = useRouter();
  const { inspecciones, usuarios } = useAppData();
  const { proyectoSeleccionado } = useProjectSelection();

  const [density, setDensity] = useState<DensityType>("normal");
  const [searchTerm, setSearchTerm] = useState("");
  const [stateFilter, setStateFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("Todos");
  const [inspectorFilter, setInspectorFilter] = useState("all");
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [kpiCollapsed, setKpiCollapsed] = useState(false);

  const itemsPerPage = 50;

  // Filtrar inspecciones por proyecto
  const proyectoInspecciones = inspecciones.filter(
    (i) => i.proyectoId === proyectoSeleccionado
  );

  // Aplicar filtros
  const filteredInspecciones = proyectoInspecciones.filter((insp) => {
    // Filtro de búsqueda
    const searchMatch =
      insp.codigo.toLowerCase().includes(searchTerm.toLowerCase()) ||
      insp.ubicacion.toLowerCase().includes(searchTerm.toLowerCase()) ||
      insp.inspector.toLowerCase().includes(searchTerm.toLowerCase());

    // Filtro de estado
    let stateMatch = true;
    if (stateFilter !== "all") {
      const resultadoMap = {
        approved: "Aprobado",
        observed: "Falla",
        rejected: "Falla",
        in_process: "En Proceso",
      };
      stateMatch =
        insp.resultado === resultadoMap[stateFilter as keyof typeof resultadoMap];
    }

    // Filtro de tipo/partida
    const typeMatch =
      typeFilter === "Todos" || insp.tipo === typeFilter;

    // Filtro de inspector
    const inspectorMatch =
      inspectorFilter === "all" ||
      insp.inspector.toLowerCase() === inspectorFilter.toLowerCase();

    return searchMatch && stateMatch && typeMatch && inspectorMatch;
  });

  // Paginación
  const totalPages = Math.ceil(filteredInspecciones.length / itemsPerPage);
  const startIdx = (currentPage - 1) * itemsPerPage;
  const endIdx = startIdx + itemsPerPage;
  const paginatedInspecciones = filteredInspecciones.slice(startIdx, endIdx);

  // Obtener lista de inspectores únicos
  const uniqueInspectors = Array.from(
    new Set(inspecciones.map((i) => i.inspector))
  );

  // Contar por estado
  const countByState = {
    all: proyectoInspecciones.length,
    approved: proyectoInspecciones.filter((i) => i.resultado === "Aprobado").length,
    observed: proyectoInspecciones.filter((i) => i.resultado === "Falla").length,
    rejected: proyectoInspecciones.filter((i) => i.resultado === "Falla").length,
    in_process: proyectoInspecciones.filter((i) => i.resultado === "En Proceso").length,
  };

  const handleSelectionChange = (id: string, selected: boolean) => {
    const newSelection = new Set(selectedIds);
    if (selected) {
      newSelection.add(id);
    } else {
      newSelection.delete(id);
    }
    setSelectedIds(newSelection);
  };

  const handleSelectAll = (selected: boolean) => {
    if (selected) {
      setSelectedIds(new Set(paginatedInspecciones.map((i) => i.id)));
    } else {
      setSelectedIds(new Set());
    }
  };

  const handleExport = () => {
    // Generar CSV
    const headers = [
      "Código",
      "Frente",
      "Elemento",
      "Partida",
      "Fecha",
      "Inspector",
      "Cumplimiento",
      "Estado",
    ];
    const rows = filteredInspecciones.map((i) => [
      i.codigo,
      i.ubicacion,
      i.unidadControl,
      i.tipo,
      i.fecha,
      i.inspector,
      `${i.cumplimiento}%`,
      i.resultado,
    ]);

    const csv = [
      headers.join(","),
      ...rows.map((row) => row.map((cell) => `"${cell}"`).join(",")),
    ].join("\n");

    const blob = new Blob([csv], { type: "text/csv" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `inspecciones-${new Date().toISOString().split("T")[0]}.csv`;
    a.click();
  };

  return (
    <div className="flex flex-col h-screen bg-slate-50">
      {/* Banner Modo Enfoque */}
      {!kpiCollapsed && (
        <div className="bg-blue-50/70 border-b border-blue-100 px-4 py-2.5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Maximize2 className="h-4 w-4 text-blue-600" />
            <div>
              <p className="text-sm font-bold text-blue-900">MODO ENFOQUE ACTIVO</p>
              <p className="text-xs text-blue-700">
                KPIs de cabecera colapsados (+420px de espacio vertical maximizado)
              </p>
            </div>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={() => setKpiCollapsed(!kpiCollapsed)}
            className="gap-1"
          >
            Expandir Resumen KPI
          </Button>
        </div>
      )}

      {/* Header */}
      <div className="border-b border-slate-200 bg-white px-6 py-4">
        <div className="flex items-start justify-between gap-4 mb-4">
          <div>
            <div className="flex items-center gap-3">
              <Link href="/inspecciones">
                <Button variant="ghost" size="sm" className="gap-1 h-8 px-2">
                  <ChevronLeft className="h-4 w-4" />
                </Button>
              </Link>
              <div>
                <h1 className="text-2xl font-bold tracking-tight">
                  Registro General de Inspecciones
                </h1>
                <p className="text-sm text-muted-foreground mt-1">
                  Consola operativa de auditoría QA/QC en tiempo real.
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2 mt-3">
              <Badge variant="secondary" className="bg-blue-100 text-blue-700">
                • {filteredInspecciones.length} registros
              </Badge>
              <Badge variant="secondary" className="bg-slate-100 text-slate-700">
                V-GRID 50/LOTE
              </Badge>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Select defaultValue="30days">
              <SelectTrigger className="w-[200px] bg-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="7days">Últimos 7 días</SelectItem>
                <SelectItem value="30days">Últimos 30 días</SelectItem>
                <SelectItem value="90days">Últimos 90 días</SelectItem>
                <SelectItem value="all">Todo el tiempo</SelectItem>
              </SelectContent>
            </Select>

            <Button variant="outline" size="sm" className="gap-2">
              Columnas (10/10)
            </Button>

            <Button variant="outline" size="sm" className="gap-2">
              Densidad
            </Button>

            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={handleExport}
            >
              <Download className="h-4 w-4" />
              Exportar
            </Button>

            <Button size="sm" className="gap-2">
              <Plus className="h-4 w-4" />
              Nueva Auditoría
            </Button>
          </div>
        </div>
      </div>

      {/* Filtros */}
      <InspectionRegistroFilters
        onSearch={setSearchTerm}
        onStateFilter={setStateFilter}
        onTypeFilter={setTypeFilter}
        onInspectorFilter={setInspectorFilter}
        onDensityChange={setDensity}
        density={density}
        totalRecords={filteredInspecciones.length}
        inspectors={uniqueInspectors}
      />

      {/* Tabla */}
      <div className="flex-1 overflow-auto bg-white">
        <InspectionRegistroTable
          inspecciones={paginatedInspecciones}
          density={density}
          selectedIds={selectedIds}
          onSelectionChange={handleSelectionChange}
          onSelectAll={handleSelectAll}
        />
      </div>

      {/* Footer de Paginación */}
      <div className="border-t border-slate-200 bg-white px-6 py-4 flex items-center justify-between">
        <div className="text-sm text-slate-600">
          Mostrando{" "}
          <span className="font-semibold">
            {startIdx + 1} a {Math.min(endIdx, filteredInspecciones.length)}
          </span>{" "}
          de{" "}
          <span className="font-semibold">{filteredInspecciones.length}</span>{" "}
          inspecciones •{" "}
          <span className="text-emerald-600 font-medium">● Sync Local Cache</span>
        </div>

        <div className="flex items-center gap-2">
          <Select value={String(itemsPerPage)}>
            <SelectTrigger className="w-[120px] bg-white">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="25">25 por página</SelectItem>
              <SelectItem value="50">50 por página</SelectItem>
              <SelectItem value="100">100 por página</SelectItem>
            </SelectContent>
          </Select>

          <Button
            variant="outline"
            size="sm"
            disabled={currentPage === 1}
            onClick={() => setCurrentPage(1)}
          >
            |&lt;
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={currentPage === 1}
            onClick={() => setCurrentPage(currentPage - 1)}
          >
            &lt;
          </Button>

          <div className="flex items-center gap-1">
            {Array.from({ length: Math.min(3, totalPages) }).map((_, i) => {
              const pageNum = i + 1;
              return (
                <Button
                  key={pageNum}
                  size="sm"
                  variant={currentPage === pageNum ? "default" : "outline"}
                  onClick={() => setCurrentPage(pageNum)}
                >
                  {pageNum}
                </Button>
              );
            })}
            {totalPages > 3 && (
              <span className="text-sm text-muted-foreground">
                ... {totalPages}
              </span>
            )}
          </div>

          <Button
            variant="outline"
            size="sm"
            disabled={currentPage === totalPages}
            onClick={() => setCurrentPage(currentPage + 1)}
          >
            &gt;
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={currentPage === totalPages}
            onClick={() => setCurrentPage(totalPages)}
          >
            &gt;|
          </Button>
        </div>
      </div>
    </div>
  );
}
