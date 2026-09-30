"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  MoreHorizontal,
  Lock,
  Eye,
  Table2,
  ChevronRight,
} from "lucide-react";
import { EstadoInspeccionBadge } from "@/components/status-badges";
import { esMatriz } from "@/lib/inspeccion-utils";
import { nombreProyecto } from "@/lib/mock-data";
import type { Inspeccion } from "@/lib/types";

interface InspectionTableEnhancedProps {
  inspecciones: Inspeccion[];
  isLoading?: boolean;
}

export function InspectionTableEnhanced({
  inspecciones,
  isLoading,
}: InspectionTableEnhancedProps) {
  const router = useRouter();

  const handleRowClick = (id: string) => {
    router.push(`/inspecciones/${id}`);
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-muted-foreground">Cargando inspecciones...</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden border-0 shadow-sm">
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="border-b bg-slate-50 hover:bg-slate-50">
                <TableHead className="font-semibold text-slate-700">CÓDIGO</TableHead>
                <TableHead className="font-semibold text-slate-700">PROYECTO / FRENTE</TableHead>
                <TableHead className="font-semibold text-slate-700">UBICACIÓN / ELEMENTO</TableHead>
                <TableHead className="font-semibold text-slate-700">PARTIDA</TableHead>
                <TableHead className="font-semibold text-slate-700">FECHA Y HORA</TableHead>
                <TableHead className="font-semibold text-slate-700">INSPECTOR A CARGO</TableHead>
                <TableHead className="font-semibold text-slate-700 text-right">CUMPLIMIENTO</TableHead>
                <TableHead className="font-semibold text-slate-700">ESTADO</TableHead>
                <TableHead className="w-10" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {inspecciones.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="py-12 text-center">
                    <div className="flex flex-col items-center gap-2">
                      <Eye className="h-8 w-8 text-muted-foreground/40" />
                      <p className="text-sm text-muted-foreground">
                        No hay inspecciones en esta categoría
                      </p>
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                inspecciones.map((insp) => (
                  <TableRow
                    key={insp.id}
                    className="cursor-pointer border-b transition-colors hover:bg-slate-50 active:bg-slate-100"
                    onClick={() => handleRowClick(insp.id)}
                  >
                    <TableCell className="font-mono font-semibold text-slate-900">
                      {insp.codigo}
                    </TableCell>
                    <TableCell className="max-w-[200px] truncate text-sm text-slate-700">
                      {nombreProyecto(insp.proyectoId)}
                    </TableCell>
                    <TableCell className="max-w-[200px] truncate text-sm text-slate-600">
                      <span className="font-medium">{insp.ubicacion}</span>
                      <span className="text-muted-foreground"> / {insp.unidadControl}</span>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="bg-slate-100 text-slate-700 border-slate-200">
                        {insp.tipo}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-slate-600 whitespace-nowrap">
                      {insp.fecha}
                    </TableCell>
                    <TableCell className="text-sm text-slate-600">
                      <div className="flex items-center gap-2">
                        <div className="h-6 w-6 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center text-xs font-semibold text-white">
                          {insp.inspector?.charAt(0) || "?"}
                        </div>
                        <span className="truncate">{insp.inspector}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      {esMatriz(insp) ? (
                        <span className="text-xs text-muted-foreground font-medium">—</span>
                      ) : (
                        <div className="flex items-center justify-end gap-2">
                          <div className="h-2 w-20 overflow-hidden rounded-full bg-slate-200">
                            <div
                              className="h-full rounded-full transition-all duration-300"
                              style={{
                                width: `${insp.cumplimiento}%`,
                                backgroundColor:
                                  insp.cumplimiento >= 80
                                    ? "#10B981"
                                    : insp.cumplimiento >= 50
                                      ? "#F59E0B"
                                      : "#EF4444",
                              }}
                            />
                          </div>
                          <span className="min-w-[3ch] text-right text-xs font-semibold text-slate-700">
                            {insp.cumplimiento}%
                          </span>
                        </div>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1.5">
                        {esMatriz(insp) ? (
                          <Badge
                            variant="outline"
                            className="gap-1 bg-violet-50 text-violet-700 border-violet-200 hover:bg-violet-50"
                          >
                            <Table2 className="h-3 w-3" />
                            Matriz
                          </Badge>
                        ) : (
                          <EstadoInspeccionBadge inspeccion={insp} />
                        )}
                        {insp.finalizada && (
                          <Lock
                            className="h-4 w-4 text-amber-600 flex-shrink-0"
                            title="Inspección finalizada"
                          />
                        )}
                      </div>
                    </TableCell>
                    <TableCell onClick={(e) => e.stopPropagation()} className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0 hover:bg-slate-100"
                        asChild
                      >
                        <Link href={`/inspecciones/${insp.id}`}>
                          <ChevronRight className="h-4 w-4 text-muted-foreground" />
                        </Link>
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>

        {inspecciones.length > 0 && (
          <div className="border-t bg-slate-50 px-6 py-3 text-xs text-muted-foreground">
            Mostrando <span className="font-semibold text-slate-700">{inspecciones.length}</span> de{" "}
            <span className="font-semibold text-slate-700">{inspecciones.length}</span> inspecciones
          </div>
        )}
      </CardContent>
    </Card>
  );
}
