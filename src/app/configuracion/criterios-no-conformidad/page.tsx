"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Trash2 } from "lucide-react";
import { useAppData } from "@/lib/app-data-context";
import { colorEtiquetaDot } from "@/lib/color-map";
import { NewSeveridadDialog } from "@/components/new-severidad-dialog";

export default function CriteriosNoConformidadPage() {
  const { severidades, removeSeveridad } = useAppData();

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Niveles de severidad y plazo (SLA) sugerido para levantar cada hallazgo.
        </p>
        <NewSeveridadDialog />
      </div>

      <Card>
        <CardContent className="pt-6">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Severidad</TableHead>
                <TableHead>Días para levantamiento</TableHead>
                <TableHead className="text-right">Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {severidades.map((s) => (
                <TableRow key={s.id}>
                  <TableCell className="flex items-center gap-2 font-medium">
                    <span className={`h-2.5 w-2.5 rounded-full ${colorEtiquetaDot[s.color]}`} />
                    {s.nombre}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {s.diasSla} día{s.diasSla !== 1 ? "s" : ""}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      className="text-muted-foreground hover:text-destructive"
                      onClick={() => removeSeveridad(s.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <div className="rounded-md bg-muted/50 px-4 py-3 text-xs text-muted-foreground">
        Al registrar una no conformidad, la fecha límite se sugiere automáticamente según el SLA
        de la severidad elegida.
      </div>
    </div>
  );
}
