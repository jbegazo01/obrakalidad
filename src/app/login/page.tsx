"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Camera,
  ClipboardCheck,
  Eye,
  EyeOff,
  FileCheck2,
  HardHat,
  Users,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/lib/auth-context";
import { useAppData } from "@/lib/app-data-context";
import { toast } from "sonner";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const { usuarios } = useAppData();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mostrarPassword, setMostrarPassword] = useState(false);
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);

  const usuarioDemo = usuarios.find((u) => u.estado === "Activo");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setEnviando(true);
    const resultado = login(email, password);
    if (!resultado.ok) {
      setError(resultado.error);
      setEnviando(false);
      return;
    }
    router.push("/inspecciones");
  }

  function usarCuentaDemo() {
    if (!usuarioDemo) return;
    setEmail(usuarioDemo.email);
    setPassword("demo1234");
    setError("");
  }

  return (
    <div className="flex min-h-screen">
      {/* Panel de acceso */}
      <div className="flex w-full flex-col items-center justify-center px-4 lg:w-[460px] lg:shrink-0 lg:px-12">
        <div className="w-full max-w-sm space-y-6">
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <HardHat className="h-5 w-5" />
            </div>
            <div className="leading-tight">
              <p className="text-base font-semibold">ObraCalidad</p>
              <p className="text-xs text-muted-foreground">Gestión de Calidad</p>
            </div>
          </div>

          <h1 className="text-2xl font-semibold tracking-tight">Inicia sesión</h1>
          <p className="text-sm text-muted-foreground">
            Ingresa con la cuenta de tu empresa en ObraCalidad.
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="email">Correo electrónico</Label>
              <Input
                id="email"
                type="email"
                placeholder="nombre@empresa.pe"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="password">Contraseña</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={mostrarPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="pr-9"
                />
                <button
                  type="button"
                  onClick={() => setMostrarPassword((v) => !v)}
                  className="absolute inset-y-0 right-0 flex w-9 items-center justify-center text-muted-foreground hover:text-foreground"
                  aria-label={mostrarPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                >
                  {mostrarPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}

            <div className="flex items-center justify-end">
              <button
                type="button"
                onClick={() => toast.info("Disponible cuando conectemos el correo de la empresa.")}
                className="text-xs font-medium text-primary hover:underline"
              >
                ¿Olvidaste tu contraseña?
              </button>
            </div>

            <Button type="submit" className="w-full" disabled={enviando}>
              Iniciar sesión
            </Button>
          </form>

          {usuarioDemo && (
            <div className="space-y-2 rounded-md border border-dashed bg-muted/40 p-3 text-xs">
              <p className="font-medium text-foreground">Prototipo de demostración</p>
              <p className="text-muted-foreground">
                Usa cualquier contraseña con un correo activo de Configuración → Usuarios.
              </p>
              <button
                type="button"
                onClick={usarCuentaDemo}
                className="font-medium text-primary hover:underline"
              >
                Usar cuenta de demostración ({usuarioDemo.email})
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Panel decorativo */}
      <div className="relative hidden flex-1 overflow-hidden bg-slate-950 lg:flex lg:flex-col lg:justify-center lg:px-16 lg:py-16">
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.06]"
          style={{
            backgroundImage:
              "linear-gradient(white 1px, transparent 1px), linear-gradient(90deg, white 1px, transparent 1px)",
            backgroundSize: "42px 42px",
          }}
        />
        <div className="relative max-w-md">
          <h2 className="text-3xl font-semibold leading-tight text-white sm:text-4xl">
            El control de calidad de tu obra, sin papeles perdidos.
          </h2>
          <p className="mt-4 text-sm text-slate-300">
            Cada empresa constructora tiene su propio espacio de trabajo: protocolos, no
            conformidades y reportes accesibles para todo tu equipo, desde la obra o la oficina.
          </p>

          <ul className="mt-8 space-y-3 text-sm text-slate-200">
            <li className="flex items-center gap-2.5">
              <ClipboardCheck className="h-4 w-4 shrink-0 text-sky-400" />
              Checklists digitales por protocolo y partida
            </li>
            <li className="flex items-center gap-2.5">
              <Camera className="h-4 w-4 shrink-0 text-sky-400" />
              Evidencia fotográfica vinculada a cada criterio
            </li>
            <li className="flex items-center gap-2.5">
              <FileCheck2 className="h-4 w-4 shrink-0 text-sky-400" />
              Exporta e imprime el protocolo firmado en PDF
            </li>
            <li className="flex items-center gap-2.5">
              <Users className="h-4 w-4 shrink-0 text-sky-400" />
              Un espacio propio por empresa, con sus propios usuarios
            </li>
          </ul>

          {/* Mockup flotante */}
          <div className="mt-10 rounded-xl border border-white/10 bg-white p-4 text-slate-900 shadow-2xl">
            <div className="flex items-center justify-between border-b pb-2">
              <p className="text-xs font-semibold">Checklist — Encofrado</p>
              <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-medium text-amber-700">
                Observado
              </span>
            </div>
            <div className="mt-2 space-y-1.5">
              <div className="flex items-center gap-2 text-xs">
                <span className="flex h-3.5 w-3.5 items-center justify-center rounded-full bg-emerald-100 text-emerald-700">
                  ✓
                </span>
                Verticalidad de encofrado
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span className="flex h-3.5 w-3.5 items-center justify-center rounded-full bg-red-100 text-red-700">
                  ✕
                </span>
                Limpieza interior del encofrado
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span className="flex h-3.5 w-3.5 items-center justify-center rounded-full bg-emerald-100 text-emerald-700">
                  ✓
                </span>
                Aplicación de desmoldante
              </div>
            </div>
            <div className="mt-3 flex items-center gap-2">
              <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-100">
                <div className="h-full w-3/4 rounded-full bg-primary" />
              </div>
              <span className="text-[10px] font-medium text-slate-500">75%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
