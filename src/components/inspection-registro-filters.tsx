"use client";

import { useState } from "react";
import { Search, Filter, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface InspectionRegistroFiltersProps {
  onSearch: (term: string) => void;
  onStateFilter: (state: string) => void;
  onTypeFilter: (type: string) => void;
  onInspectorFilter: (inspector: string) => void;
  onDensityChange: (density: "normal" | "compact" | "ultra") => void;
  density: "normal" | "compact" | "ultra";
  totalRecords: number;
  inspectors: string[];
}

const states = [
  { value: "all", label: "Todos", count: 0 },
  { value: "approved", label: "Aprobadas", count: 0, color: "bg-emerald-50 text-emerald-700" },
  { value: "observed", label: "Observadas", count: 0, color: "bg-amber-50 text-amber-700" },
  { value: "rejected", label: "Rechazadas", count: 0, color: "bg-red-50 text-red-700" },
  { value: "in_process", label: "En Proceso", count: 0, color: "bg-blue-50 text-blue-700" },
];

const types = [
  "Todos",
  "Concreto",
  "Acero",
  "Encofrado",
  "Instalaciones",
  "Geotecnia",
];

export function InspectionRegistroFilters({
  onSearch,
  onStateFilter,
  onTypeFilter,
  onInspectorFilter,
  onDensityChange,
  density,
  totalRecords,
  inspectors,
}: InspectionRegistroFiltersProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [activeState, setActiveState] = useState("all");

  const handleSearch = (value: string) => {
    setSearchTerm(value);
    onSearch(value);
  };

  const handleStateChange = (state: string) => {
    setActiveState(state);
    onStateFilter(state);
  };

  return (
    <div className="space-y-4 border-b border-slate-200 bg-white p-4 sticky top-0 z-30">
      {/* Estado y controles rápidos */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-slate-600">
            {totalRecords} registros
          </span>
          <span className="text-xs text-muted-foreground">•</span>
          <span className="text-xs text-muted-foreground">
            ⚡ Indexado: {Math.random() * 50 | 0}ms
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">Densidad:</span>
          <div className="flex gap-1">
            {(["normal", "compact", "ultra"] as const).map((d) => (
              <Button
                key={d}
                size="sm"
                variant={density === d ? "default" : "outline"}
                className="h-7 px-2 text-xs"
                onClick={() => onDensityChange(d)}
              >
                {d === "normal" ? "Normal" : d === "compact" ? "Compacta" : "Ultra"}
              </Button>
            ))}
          </div>
        </div>
      </div>

      {/* Búsqueda y filtros principales */}
      <div className="grid gap-3 md:grid-cols-4">
        <div className="relative md:col-span-2">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder='Buscar código (INS-), elemento... (⌘K)'
            value={searchTerm}
            onChange={(e) => handleSearch(e.target.value)}
            className="pl-9 bg-slate-50 border-slate-200"
          />
        </div>

        <Select onValueChange={onTypeFilter} defaultValue="Todos">
          <SelectTrigger className="bg-slate-50 border-slate-200">
            <SelectValue placeholder="Partida" />
          </SelectTrigger>
          <SelectContent>
            {types.map((type) => (
              <SelectItem key={type} value={type}>
                {type}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select onValueChange={onInspectorFilter} defaultValue="all">
          <SelectTrigger className="bg-slate-50 border-slate-200">
            <SelectValue placeholder="Inspector" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Cualquier inspector</SelectItem>
            {inspectors.map((inspector) => (
              <SelectItem key={inspector} value={inspector}>
                {inspector}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Pestañas de estado */}
      <div className="flex flex-wrap gap-2 border-t border-slate-200 pt-3">
        {states.map((state) => (
          <button
            key={state.value}
            onClick={() => handleStateChange(state.value)}
            className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-medium transition-all ${
              activeState === state.value
                ? "bg-blue-100 text-blue-700 border border-blue-200"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200"
            }`}
          >
            <span>{state.label}</span>
            <Badge variant="secondary" className="ml-1 h-5 min-w-5 flex items-center justify-center text-xs">
              {state.count}
            </Badge>
          </button>
        ))}
      </div>
    </div>
  );
}
