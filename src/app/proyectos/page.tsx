"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { MapPin, User } from "lucide-react";
import { proyectos } from "@/lib/mock-data";
import { useAppData } from "@/lib/app-data-context";

export default function ProyectosPage() {
  const { inspecciones, noConformidades } = useAppData();
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Proyectos</h1>
        <p className="text-sm text-muted-foreground">
          Obras activas y su estado de calidad general.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {proyectos.map((p) => {
          const insp = inspecciones.filter((i) => i.proyectoId === p.id);
          const ncAbiertas = noConformidades.filter(
            (n) => n.proyectoId === p.id && n.estado !== "Cerrada"
          );
          const cumplimiento = insp.length
            ? Math.round(insp.reduce((acc, i) => acc + i.cumplimiento, 0) / insp.length)
            : 0;

          return (
            <Card key={p.id}>
              <CardHeader>
                <CardTitle className="text-base leading-snug">{p.nombre}</CardTitle>
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <MapPin className="h-3.5 w-3.5" />
                  {p.ubicacion}
                </div>
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <User className="h-3.5 w-3.5" />
                  {p.residente}
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-xs text-muted-foreground">Cliente: {p.cliente}</p>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Inspecciones</span>
                  <span className="font-medium">{insp.length}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Cumplimiento promedio</span>
                  <span className="font-medium">{cumplimiento}%</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">NC abiertas</span>
                  {ncAbiertas.length > 0 ? (
                    <Badge className="bg-red-100 text-red-700 hover:bg-red-100">
                      {ncAbiertas.length}
                    </Badge>
                  ) : (
                    <Badge className="bg-emerald-100 text-emerald-700 hover:bg-emerald-100">
                      0
                    </Badge>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
