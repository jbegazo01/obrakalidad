"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { LogoUploader } from "@/components/logo-uploader";
import { ProyectoPdfConfigCard } from "@/components/proyecto-pdf-config-card";
import { useAppData } from "@/lib/app-data-context";
import { proyectos } from "@/lib/mock-data";

export default function PlantillaPdfPage() {
  const { empresa, updateEmpresa } = useAppData();

  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground">
        Estos datos arman el encabezado, las firmas y el panel fotográfico del PDF exportado o
        impreso de cada inspección.
      </p>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Datos de la empresa</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-1.5">
            <Label className="text-xs text-muted-foreground">Nombre de la empresa</Label>
            <Input
              placeholder="Ej. Constructora Andina S.A.C."
              defaultValue={empresa.nombre}
              onBlur={(e) => updateEmpresa({ nombre: e.target.value })}
            />
          </div>
          <div className="space-y-1.5">
            <Label className="text-xs text-muted-foreground">Logo del contratista</Label>
            <LogoUploader
              logo={empresa.logo}
              onChange={(logo) => updateEmpresa({ logo })}
              label="Subir logo del contratista"
            />
          </div>
        </CardContent>
      </Card>

      <div>
        <h2 className="mb-2 text-sm font-medium">Datos por proyecto</h2>
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {proyectos.map((p) => (
            <ProyectoPdfConfigCard key={p.id} proyecto={p} />
          ))}
        </div>
      </div>
    </div>
  );
}
