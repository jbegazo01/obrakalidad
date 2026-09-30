"use client";

import { Lock } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { EstadoNC, EstadoUsuario, Inspeccion, ResultadoInspeccion, RolUsuario } from "@/lib/types";
import { cn } from "@/lib/utils";
import { colorEtiquetaClasses } from "@/lib/color-map";
import { useAppData } from "@/lib/app-data-context";
import { estadoVisible } from "@/lib/inspeccion-utils";

const estadoStyles: Record<EstadoNC, string> = {
  Abierta: "bg-red-100 text-red-700 hover:bg-red-100",
  "En proceso": "bg-amber-100 text-amber-700 hover:bg-amber-100",
  Cerrada: "bg-emerald-100 text-emerald-700 hover:bg-emerald-100",
};

const resultadoStyles: Record<ResultadoInspeccion, string> = {
  Nuevo: "bg-slate-100 text-slate-700 hover:bg-slate-100",
  "En Proceso": "bg-amber-100 text-amber-700 hover:bg-amber-100",
  Aprobado: "bg-emerald-100 text-emerald-700 hover:bg-emerald-100",
  Falla: "bg-red-100 text-red-700 hover:bg-red-100",
};

const solucionadoStyle = "bg-blue-100 text-blue-700 hover:bg-blue-100";

const rolStyles: Record<RolUsuario, string> = {
  Calidad: "bg-blue-100 text-blue-700 hover:bg-blue-100",
  Producción: "bg-orange-100 text-orange-700 hover:bg-orange-100",
  Residente: "bg-violet-100 text-violet-700 hover:bg-violet-100",
  Supervisor: "bg-teal-100 text-teal-700 hover:bg-teal-100",
  Subcontratista: "bg-slate-100 text-slate-700 hover:bg-slate-100",
  Visualizador: "bg-gray-100 text-gray-600 hover:bg-gray-100",
};

const estadoUsuarioStyles: Record<EstadoUsuario, string> = {
  Activo: "bg-emerald-100 text-emerald-700 hover:bg-emerald-100",
  Inactivo: "bg-gray-100 text-gray-500 hover:bg-gray-100",
};

export function EstadoBadge({ estado }: { estado: EstadoNC }) {
  return <Badge className={cn("font-medium", estadoStyles[estado])}>{estado}</Badge>;
}

export function SeveridadBadge({ severidad }: { severidad: string }) {
  const { severidades } = useAppData();
  const config = severidades.find((s) => s.nombre === severidad);
  const className = config ? colorEtiquetaClasses[config.color] : "bg-slate-100 text-slate-700 hover:bg-slate-100";
  return <Badge className={cn("font-medium", className)}>{severidad}</Badge>;
}

export function ResultadoBadge({ resultado }: { resultado: ResultadoInspeccion }) {
  return <Badge className={cn("font-medium", resultadoStyles[resultado])}>{resultado}</Badge>;
}

export function EstadoInspeccionBadge({ inspeccion }: { inspeccion: Inspeccion }) {
  const estado = estadoVisible(inspeccion);
  if (estado === "Solucionado") {
    return <Badge className={cn("font-medium", solucionadoStyle)}>Solucionado</Badge>;
  }
  return <ResultadoBadge resultado={estado} />;
}

export function FinalizadaBadge() {
  return (
    <Badge className="gap-1 bg-slate-800 font-medium text-white hover:bg-slate-800">
      <Lock className="h-3 w-3" />
      Finalizada
    </Badge>
  );
}

export function RolBadge({ rol }: { rol: RolUsuario }) {
  return <Badge className={cn("font-medium", rolStyles[rol])}>{rol}</Badge>;
}

export function EstadoUsuarioBadge({ estado }: { estado: EstadoUsuario }) {
  return <Badge className={cn("font-medium", estadoUsuarioStyles[estado])}>{estado}</Badge>;
}
