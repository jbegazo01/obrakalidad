"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { LogoUploader } from "@/components/logo-uploader";
import { useAppData } from "@/lib/app-data-context";
import type { Proyecto } from "@/lib/types";

export function ProyectoPdfConfigCard({ proyecto }: { proyecto: Proyecto }) {
  const { proyectoPdfConfig, updateProyectoPdfConfig } = useAppData();
  const config = proyectoPdfConfig[proyecto.id] ?? {};

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{proyecto.nombre}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="space-y-1.5">
          <Label className="text-xs text-muted-foreground">
            Nombre oficial del proyecto (aparece en el encabezado)
          </Label>
          <Textarea
            placeholder={proyecto.nombre}
            defaultValue={config.nombreOficial ?? ""}
            onBlur={(e) =>
              updateProyectoPdfConfig(proyecto.id, { nombreOficial: e.target.value })
            }
            className="text-sm"
          />
        </div>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label className="text-xs text-muted-foreground">Código CUI</Label>
            <Input
              placeholder="Ej. 2610634"
              defaultValue={config.cui ?? ""}
              onBlur={(e) => updateProyectoPdfConfig(proyecto.id, { cui: e.target.value })}
            />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs text-muted-foreground">Supervisión</Label>
            <Input
              placeholder="Ej. Meta Control"
              defaultValue={config.supervision ?? ""}
              onBlur={(e) => updateProyectoPdfConfig(proyecto.id, { supervision: e.target.value })}
            />
          </div>
        </div>
        <div className="space-y-1.5">
          <Label className="text-xs text-muted-foreground">Logo del cliente</Label>
          <LogoUploader
            logo={config.logoCliente}
            onChange={(logo) => updateProyectoPdfConfig(proyecto.id, { logoCliente: logo })}
            label="Subir logo del cliente"
          />
        </div>
      </CardContent>
    </Card>
  );
}
