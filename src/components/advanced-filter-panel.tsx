"use client";

import { useState } from "react";
import { ChevronDown, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { ResultadoInspeccion, EstadoRevisionInspeccion, EstadoInspeccion } from "@/lib/types";

interface AdvancedFilterPanelProps {
  searchTerm: string;
  onSearchChange: (value: string) => void;
  resultado: string;
  onResultadoChange: (value: string) => void;
  estadoRevision: string;
  onEstadoRevisionChange: (value: string) => void;
  inspector: string;
  onInspectorChange: (value: string) => void;
  tipo: string;
  onTipoChange: (value: string) => void;
  estadoSolucion: string;
  onEstadoSolucionChange: (value: string) => void;
  fechaDesde: string;
  onFechaDesdeChange: (value: string) => void;
  fechaHasta: string;
  onFechaHastaChange: (value: string) => void;
  tiposDisponibles: string[];
  inspectoresDisponibles: string[];
  onClearFilters: () => void;
  activeFilterCount: number;
}

export function AdvancedFilterPanel({
  searchTerm,
  onSearchChange,
  resultado,
  onResultadoChange,
  estadoRevision,
  onEstadoRevisionChange,
  inspector,
  onInspectorChange,
  tipo,
  onTipoChange,
  estadoSolucion,
  onEstadoSolucionChange,
  fechaDesde,
  onFechaDesdeChange,
  fechaHasta,
  onFechaHastaChange,
  tiposDisponibles,
  inspectoresDisponibles,
  onClearFilters,
  activeFilterCount,
}: AdvancedFilterPanelProps) {
  const [expanded, setExpanded] = useState(false);

  const hasActiveFilters =
    searchTerm ||
    resultado !== "todos" ||
    estadoRevision !== "todos" ||
    inspector !== "todos" ||
    tipo !== "todos" ||
    estadoSolucion !== "todos" ||
    fechaDesde ||
    fechaHasta;

  return (
    <div className="space-y-3">
      {/* Barra de búsqueda y botón de filtros */}
      <div className="flex gap-2">
        <div className="flex-1 relative">
          <Input
            type="search"
            placeholder="Buscar por código, ubicación, inspector..."
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-10"
          />
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={() => setExpanded(!expanded)}
          className={cn(
            "gap-2",
            hasActiveFilters && "border-blue-300 bg-blue-50"
          )}
        >
          <svg
            className="h-4 w-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
            />
          </svg>
          Filtros
          {activeFilterCount > 0 && (
            <Badge variant="secondary" className="ml-1">
              {activeFilterCount}
            </Badge>
          )}
          <ChevronDown
            className={cn("h-4 w-4 transition-transform", {
              "rotate-180": expanded,
            })}
          />
        </Button>
      </div>

      {/* Panel desplegable de filtros */}
      {expanded && (
        <div className="rounded-lg border bg-card p-4 space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {/* Resultado */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Resultado</label>
              <Select value={resultado} onValueChange={onResultadoChange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="todos">Todos</SelectItem>
                  <SelectItem value="Nuevo">Nuevo</SelectItem>
                  <SelectItem value="En Proceso">En Proceso</SelectItem>
                  <SelectItem value="Aprobado">Aprobado</SelectItem>
                  <SelectItem value="Falla">Falla</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Estado de Revisión */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Estado Revisión</label>
              <Select value={estadoRevision} onValueChange={onEstadoRevisionChange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="todos">Todos</SelectItem>
                  <SelectItem value="Nueva">Nueva</SelectItem>
                  <SelectItem value="En Revisión">En Revisión</SelectItem>
                  <SelectItem value="Revisiones Completadas">Revisiones Completadas</SelectItem>
                  <SelectItem value="Finalizada">Finalizada</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Inspector */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Inspector</label>
              <Select value={inspector} onValueChange={onInspectorChange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="todos">Todos</SelectItem>
                  {inspectoresDisponibles.map((insp) => (
                    <SelectItem key={insp} value={insp}>
                      {insp}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Tipo/Partida */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Tipo/Partida</label>
              <Select value={tipo} onValueChange={onTipoChange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="todos">Todos</SelectItem>
                  {tiposDisponibles.map((t) => (
                    <SelectItem key={t} value={t}>
                      {t}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Estado de Solución */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Estado Solución</label>
              <Select value={estadoSolucion} onValueChange={onEstadoSolucionChange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="todos">Todos</SelectItem>
                  <SelectItem value="Pendiente">Pendiente</SelectItem>
                  <SelectItem value="Solucionado">Solucionado</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Fecha Desde */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Desde</label>
              <Input
                type="date"
                value={fechaDesde}
                onChange={(e) => onFechaDesdeChange(e.target.value)}
              />
            </div>

            {/* Fecha Hasta */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Hasta</label>
              <Input
                type="date"
                value={fechaHasta}
                onChange={(e) => onFechaHastaChange(e.target.value)}
              />
            </div>
          </div>

          {/* Botón de limpiar filtros */}
          {hasActiveFilters && (
            <div className="flex justify-end pt-2 border-t">
              <Button
                variant="ghost"
                size="sm"
                onClick={onClearFilters}
                className="gap-1 text-muted-foreground hover:text-foreground"
              >
                <X className="h-4 w-4" />
                Limpiar filtros
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
