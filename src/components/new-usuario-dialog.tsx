"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useAppData } from "@/lib/app-data-context";
import type { RolUsuario } from "@/lib/types";
import { toast } from "sonner";

const roles: RolUsuario[] = [
  "Calidad",
  "Producción",
  "Residente",
  "Supervisor",
  "Subcontratista",
  "Visualizador",
];

export function NewUsuarioDialog() {
  const { addUsuario } = useAppData();
  const [open, setOpen] = useState(false);
  const [nombre, setNombre] = useState("");
  const [email, setEmail] = useState("");
  const [rol, setRol] = useState<RolUsuario | "">("");

  const puedeGuardar = nombre && email && rol;

  function resetForm() {
    setNombre("");
    setEmail("");
    setRol("");
  }

  function handleSubmit() {
    if (!puedeGuardar) return;
    addUsuario({ nombre, email, rol: rol as RolUsuario });
    toast.success(`${nombre} fue invitado como ${rol}`);
    resetForm();
    setOpen(false);
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        setOpen(o);
        if (!o) resetForm();
      }}
    >
      <DialogTrigger
        render={
          <Button>
            <Plus className="h-4 w-4" />
            Nuevo usuario
          </Button>
        }
      />
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Invitar usuario</DialogTitle>
          <DialogDescription>
            Se le enviará una invitación para crear su cuenta con el perfil asignado.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label>Nombre completo</Label>
            <Input
              placeholder="Ej. Ing. Paola Ríos"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label>Correo electrónico</Label>
            <Input
              type="email"
              placeholder="nombre@empresa.pe"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label>Perfil</Label>
            <Select value={rol} onValueChange={(v) => setRol((v ?? "") as RolUsuario)}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Selecciona un perfil" />
              </SelectTrigger>
              <SelectContent>
                {roles.map((r) => (
                  <SelectItem key={r} value={r}>
                    {r}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancelar
          </Button>
          <Button onClick={handleSubmit} disabled={!puedeGuardar}>
            Enviar invitación
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
