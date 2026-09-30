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
import { useAppData } from "@/lib/app-data-context";
import { EstadoUsuarioBadge, RolBadge } from "@/components/status-badges";
import { NewUsuarioDialog } from "@/components/new-usuario-dialog";

export default function UsuariosPage() {
  const { usuarios, toggleEstadoUsuario } = useAppData();

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          {usuarios.length} usuario{usuarios.length !== 1 ? "s" : ""} de tu empresa.
        </p>
        <NewUsuarioDialog />
      </div>

      <Card>
        <CardContent className="pt-6">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nombre</TableHead>
                <TableHead>Correo</TableHead>
                <TableHead>Perfil</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead>Creado</TableHead>
                <TableHead className="text-right">Acciones</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {usuarios.map((u) => (
                <TableRow key={u.id}>
                  <TableCell className="font-medium">{u.nombre}</TableCell>
                  <TableCell className="text-sm text-muted-foreground">{u.email}</TableCell>
                  <TableCell>
                    <RolBadge rol={u.rol} />
                  </TableCell>
                  <TableCell>
                    <EstadoUsuarioBadge estado={u.estado} />
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">{u.fechaCreacion}</TableCell>
                  <TableCell className="text-right">
                    <Button variant="outline" size="sm" onClick={() => toggleEstadoUsuario(u.id)}>
                      {u.estado === "Activo" ? "Desactivar" : "Activar"}
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <div className="rounded-md bg-muted/50 px-4 py-3 text-xs text-muted-foreground">
        Perfiles disponibles: Calidad, Producción, Residente, Supervisor, Subcontratista y
        Visualizador. Cada perfil determinará qué módulos y acciones puede ver el usuario dentro
        de la plataforma.
      </div>
    </div>
  );
}
