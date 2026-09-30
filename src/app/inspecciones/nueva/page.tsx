"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
import { useProjectSelection } from "@/lib/project-selection-context";
import { useAuth } from "@/lib/auth-context";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

export default function NuevaInspeccionPage() {
  const router = useRouter();
  const { protocolos, addInspeccion, etapasConstructivas } = useAppData();
  const { proyectoSeleccionado } = useProjectSelection();
  const { usuarioActual } = useAuth();

  const [proyectoId, setProyectoId] = useState(() => proyectoSeleccionado);
  const [etapaId, setEtapaId] = useState("");
  const [protocoloId, setProtocoloId] = useState("");
  const [ubicacion, setUbicacion] = useState("");
  const [unidadControl, setUnidadControl] = useState("");
  const [inspector, setInspector] = useState("");

  const protocolosFiltrados = etapaId
    ? protocolos.filter((p) => p.etapaId === etapaId)
    : [];

  const protocolo = protocolos.find((p) => p.id === protocoloId);

  const puedeGuardar = Boolean(
    proyectoId && etapaId && protocoloId && ubicacion && unidadControl && inspector
  );

  function handleSubmit() {
    if (!puedeGuardar || !protocolo || !usuarioActual) return;

    const items = protocolo.tipo === "checklist"
      ? protocolo.criterios.map((c) => ({
          id: c.id,
          descripcion: c.texto,
          respuesta: null as const,
          comentario: "",
          evidencias: [],
        }))
      : [];

    const nueva = addInspeccion({
      proyectoId,
      ubicacion,
      unidadControl,
      protocoloId,
      tipo: protocolo.nombre,
      tipoRegistro: protocolo.tipo,
      inspector,
      items,
      estadoRevision: "Nueva",
      registrosRevision: [{
        id: `rev-${Date.now()}`,
        rol: usuarioActual.rol,
        nombreRevisor: usuarioActual.nombre,
        fechaHora: new Date().toISOString(),
      }],
    });

    toast.success(`${nueva.codigo} creada — Estado: Nueva`);
    router.push("/inspecciones");
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <Link
            href="/inspecciones"
            className={cn(buttonVariants({ variant: "outline", size: "icon" }))}
          >
            <ArrowLeft className="h-4 w-4" />
          </Link>
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Nueva inspección</h1>
            <p className="text-sm text-muted-foreground">
              Crea una inspección vacía que completarás después desde el listado.
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Link href="/inspecciones" className={cn(buttonVariants({ variant: "outline" }))}>
            Cancelar
          </Link>
          <Button onClick={handleSubmit} disabled={!puedeGuardar}>
            Crear inspección
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Datos de la inspección</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label>Etapa constructiva</Label>
              <Select value={etapaId} onValueChange={(v) => setEtapaId(v || "")}>
                <SelectTrigger>
                  <SelectValue placeholder="Selecciona una etapa" />
                </SelectTrigger>
                <SelectContent>
                  {etapasConstructivas.map((etapa) => (
                    <SelectItem key={etapa.id} value={etapa.id}>
                      {etapa.nombre}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label>Protocolo / Partida</Label>
              <Select value={protocoloId} onValueChange={(v) => setProtocoloId(v || "")}>
                <SelectTrigger>
                  <SelectValue placeholder="Selecciona una partida" />
                </SelectTrigger>
                <SelectContent>
                  {protocolosFiltrados.map((p) => (
                    <SelectItem key={p.id} value={p.id}>
                      {p.nombre}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="space-y-1.5">
              <Label>Ubicación</Label>
              <Input
                placeholder="Ej. Piso 4"
                value={ubicacion}
                onChange={(e) => setUbicacion(e.target.value)}
              />
            </div>

            <div className="space-y-1.5">
              <Label>Unidad de control</Label>
              <Input
                placeholder="Ej. Departamento A"
                value={unidadControl}
                onChange={(e) => setUnidadControl(e.target.value)}
              />
            </div>

            <div className="space-y-1.5">
              <Label>Inspector responsable</Label>
              <Input
                placeholder="Ej. Ing. Paola Ríos"
                value={inspector}
                onChange={(e) => setInspector(e.target.value)}
              />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
