"use client";

import { useRouter } from "next/navigation";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ChevronRight, Lock } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Inspeccion } from "@/lib/types";

interface InspectionRegistroTableProps {
  inspecciones: Inspeccion[];
  density: "normal" | "compact" | "ultra";
  selectedIds: Set<string>;
  onSelectionChange: (id: string, selected: boolean) => void;
  onSelectAll: (selected: boolean) => void;
}

const densityConfig = {
  normal: { rowHeight: "h-16", textSize: "text-sm", padding: "px-4 py-3" },
  compact: { rowHeight: "h-12", textSize: "text-xs", padding: "px-3 py-2" },
  ultra: { rowHeight: "h-10", textSize: "text-xs", padding: "px-2 py-1" },
};

const stateColors = {
  Nuevo: "bg-slate-50 text-slate-700 border-slate-200",
  "En Proceso": "bg-amber-50 text-amber-700 border-amber-200",
  Aprobado: "bg-emerald-50 text-emerald-700 border-emerald-200",
  Falla: "bg-red-50 text-red-700 border-red-200",
};

const typeColors = {
  Concreto: "bg-blue-50 text-blue-700 border-blue-100",
  Acero: "bg-slate-100 text-slate-700 border-slate-200",
  Encofrado: "bg-slate-50 text-slate-700 border-slate-200",
  Instalaciones: "bg-indigo-50 text-indigo-700 border-indigo-100",
  Geotecnia: "bg-green-50 text-green-700 border-green-100",
};

export function InspectionRegistroTable({
  inspecciones,
  density,
  selectedIds,
  onSelectionChange,
  onSelectAll,
}: InspectionRegistroTableProps) {
  const router = useRouter();
  const config = densityConfig[density];

  const getStateColor = (resultado: string) =>
    stateColors[resultado as keyof typeof stateColors] || "bg-gray-50 text-gray-700";

  const getTypeColor = (tipo: string) =>
    typeColors[tipo as keyof typeof typeColors] || "bg-gray-50 text-gray-700";

  const getScoreColor = (score: number) => {
    if (score >= 80) return "#10B981";
    if (score >= 50) return "#F59E0B";
    return "#EF4444";
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead className="sticky top-16 z-20 bg-slate-50 border-b border-slate-200">
          <tr>
            <th className={`${config.padding} w-10 text-left`}>
              <Checkbox
                checked={
                  inspecciones.length > 0 && selectedIds.size === inspecciones.length
                }
                onCheckedChange={(checked) => onSelectAll(checked as boolean)}
              />
            </th>
            <th className={`${config.padding} text-left font-semibold text-slate-700 ${config.textSize}`}>
              CÓDIGO
            </th>
            <th className={`${config.padding} text-left font-semibold text-slate-700 ${config.textSize}`}>
              FRENTE / UBICACIÓN
            </th>
            <th className={`${config.padding} text-left font-semibold text-slate-700 ${config.textSize}`}>
              ELEMENTO
            </th>
            <th className={`${config.padding} text-left font-semibold text-slate-700 ${config.textSize}`}>
              PARTIDA
            </th>
            <th className={`${config.padding} text-left font-semibold text-slate-700 ${config.textSize}`}>
              FECHA
            </th>
            <th className={`${config.padding} text-left font-semibold text-slate-700 ${config.textSize}`}>
              INSPECTOR
            </th>
            <th className={`${config.padding} text-right font-semibold text-slate-700 ${config.textSize}`}>
              CUMPL.
            </th>
            <th className={`${config.padding} text-left font-semibold text-slate-700 ${config.textSize}`}>
              ESTADO
            </th>
            <th className={`${config.padding} w-10`} />
          </tr>
        </thead>
        <tbody>
          {inspecciones.length === 0 ? (
            <tr>
              <td
                colSpan={10}
                className="text-center py-12 text-muted-foreground text-sm"
              >
                No hay inspecciones que coincidan
              </td>
            </tr>
          ) : (
            inspecciones.map((insp) => (
              <tr
                key={insp.id}
                className={`border-b border-slate-100 hover:bg-blue-50/30 transition-colors cursor-pointer group ${config.rowHeight}`}
                onClick={() => router.push(`/inspecciones/${insp.id}`)}
              >
                <td
                  className={`${config.padding}`}
                  onClick={(e) => e.stopPropagation()}
                >
                  <Checkbox
                    checked={selectedIds.has(insp.id)}
                    onCheckedChange={(checked) =>
                      onSelectionChange(insp.id, checked as boolean)
                    }
                  />
                </td>

                {/* CÓDIGO */}
                <td className={`${config.padding} font-mono font-semibold text-blue-600`}>
                  <div>{insp.codigo}</div>
                  {density !== "ultra" && (
                    <div className={`text-muted-foreground ${density === "normal" ? "text-xs" : "text-[10px]"}`}>
                      Protocolo V-28
                    </div>
                  )}
                </td>

                {/* FRENTE / UBICACIÓN */}
                <td className={`${config.padding} ${config.textSize}`}>
                  <div className="font-medium text-slate-900">{insp.ubicacion}</div>
                  {density !== "ultra" && (
                    <div className="text-muted-foreground text-[11px]">
                      Sector 02 (Ejes C-7 a D-9)
                    </div>
                  )}
                </td>

                {/* ELEMENTO */}
                <td className={`${config.padding} ${config.textSize} max-w-xs`}>
                  <div className="font-medium text-slate-900">{insp.unidadControl}</div>
                  {density === "normal" && (
                    <div className="text-muted-foreground text-[11px]">
                      f'c = 280 kg/cm²
                    </div>
                  )}
                </td>

                {/* PARTIDA */}
                <td className={`${config.padding}`}>
                  <Badge
                    variant="outline"
                    className={`${getTypeColor(insp.tipo)} border ${density === "ultra" ? "text-[10px] px-1.5 py-0.5" : ""}`}
                  >
                    {density === "ultra" ? insp.tipo.substring(0, 3) : insp.tipo}
                  </Badge>
                </td>

                {/* FECHA */}
                <td className={`${config.padding} ${config.textSize} text-slate-600`}>
                  {density === "normal" ? (
                    <>
                      <div>Hoy, 10:45 AM</div>
                      <div className="text-muted-foreground text-[11px]">
                        {insp.fecha}
                      </div>
                    </>
                  ) : (
                    <div className="truncate">{insp.fecha}</div>
                  )}
                </td>

                {/* INSPECTOR */}
                <td className={`${config.padding} ${config.textSize}`}>
                  <div className="flex items-center gap-1.5">
                    <div className={`h-6 w-6 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-white font-bold ${density === "ultra" ? "text-[9px]" : "text-xs"}`}>
                      {insp.inspector?.charAt(0)}
                    </div>
                    {density !== "ultra" && (
                      <div className="truncate">
                        <div className="font-medium text-slate-900">
                          {insp.inspector?.split(" ")[0]}
                        </div>
                        <div className="text-[10px] text-muted-foreground">
                          Estructural Sr.
                        </div>
                      </div>
                    )}
                  </div>
                </td>

                {/* CUMPLIMIENTO */}
                <td className={`${config.padding} text-right`}>
                  <div className="flex items-center justify-end gap-2">
                    {density !== "ultra" && (
                      <div className="h-1.5 w-12 overflow-hidden rounded-full bg-slate-200">
                        <div
                          className="h-full rounded-full transition-all"
                          style={{ width: `${insp.cumplimiento}%`, backgroundColor: getScoreColor(insp.cumplimiento) }}
                        />
                      </div>
                    )}
                    <span className={`min-w-8 text-right font-semibold text-slate-700 ${config.textSize}`}>
                      {insp.cumplimiento}%
                    </span>
                  </div>
                </td>

                {/* ESTADO */}
                <td className={`${config.padding}`}>
                  <div className="flex items-center gap-1">
                    <Badge
                      variant="outline"
                      className={`${getStateColor(insp.resultado)} border ${density === "ultra" ? "text-[10px] px-1.5 py-0.5" : ""}`}
                    >
                      {density === "ultra"
                        ? insp.resultado.substring(0, 3)
                        : insp.resultado}
                    </Badge>
                    {insp.finalizada && (
                      <Lock className="h-3.5 w-3.5 text-amber-600" />
                    )}
                  </div>
                </td>

                {/* ACCIÓN */}
                <td className={`${config.padding} text-right`}>
                  <ChevronRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
