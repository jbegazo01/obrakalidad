"use client";

import { useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  ClipboardCheck,
  AlertTriangle,
  Building2,
  HardHat,
  LogOut,
  Settings,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useAuth } from "@/lib/auth-context";
import { useAppData } from "@/lib/app-data-context";
import { useProjectSelection } from "@/lib/project-selection-context";

const nav = [
  { href: "/inspecciones", label: "Inspecciones", icon: ClipboardCheck },
  { href: "/no-conformidades", label: "No Conformidades", icon: AlertTriangle },
  { href: "/proyectos", label: "Proyectos", icon: Building2 },
  { href: "/configuracion", label: "Configuración", icon: Settings },
];

function isActive(pathname: string, href: string) {
  return pathname === href || pathname.startsWith(`${href}/`);
}

function iniciales(nombre: string) {
  const partes = nombre.trim().split(/\s+/);
  return ((partes[0]?.[0] ?? "") + (partes[1]?.[0] ?? "")).toUpperCase() || "U";
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { usuarioActual, logout } = useAuth();
  const { proyectos, usuarios } = useAppData();
  const { proyectoSeleccionado, setProyectoSeleccionado } = useProjectSelection();
  const esLogin = pathname === "/login";
  const esImprimir = pathname.endsWith("/imprimir");

  const usuarioActualData = usuarioActual ? usuarios.find((u) => u.id === usuarioActual.id) : null;
  const proyectosAccesibles = usuarioActualData?.proyectoIds
    ? proyectos.filter((p) => usuarioActualData.proyectoIds?.includes(p.id) ?? false)
    : proyectos;

  useEffect(() => {
    if (proyectoSeleccionado === "" && proyectosAccesibles.length > 0) {
      setProyectoSeleccionado(proyectosAccesibles[0].id);
    }
  }, [proyectosAccesibles, proyectoSeleccionado, setProyectoSeleccionado]);

  useEffect(() => {
    if (!esLogin && !usuarioActual) {
      router.replace("/login");
    }
  }, [esLogin, usuarioActual, router]);

  if (esLogin) {
    return <>{children}</>;
  }

  if (!usuarioActual) {
    return null;
  }

  if (esImprimir) {
    return <>{children}</>;
  }

  function handleLogout() {
    logout();
    router.push("/login");
  }

  return (
    <div className="flex min-h-screen w-full bg-slate-50">
      <aside className="hidden w-64 shrink-0 flex-col border-r border-slate-200 bg-slate-900 text-slate-50 md:flex">
        <div className="flex h-16 items-center gap-3 border-b border-slate-800 px-5">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-400 to-blue-600">
            <HardHat className="h-5 w-5" />
          </div>
          <div className="leading-tight">
            <p className="text-sm font-bold tracking-tight">ObraCalidad</p>
            <p className="text-xs text-slate-400">QA/QC Platform</p>
          </div>
          <div className="ml-auto flex items-center gap-1 rounded-full bg-emerald-500/20 px-2.5 py-1 text-xs font-semibold text-emerald-300">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            PRO
          </div>
        </div>

        <div className="px-5 py-3 text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            Sincronizado Local | Online
          </div>
        </div>

        <nav className="flex-1 space-y-1 px-3 py-4">
          {nav.map((item) => {
            const active = isActive(pathname, item.href);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200",
                  active
                    ? "bg-blue-600 text-white shadow-lg"
                    : "text-slate-300 hover:bg-slate-800 hover:text-white"
                )}
              >
                <Icon className="h-5 w-5" />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-slate-800 p-3">
          <div className="flex items-center gap-3 rounded-lg bg-slate-800 px-3 py-3">
            <Avatar className="h-9 w-9 border-2 border-blue-500">
              <AvatarFallback className="bg-gradient-to-br from-blue-400 to-blue-600 text-white font-semibold">
                {iniciales(usuarioActual.nombre)}
              </AvatarFallback>
            </Avatar>
            <div className="min-w-0 flex-1 leading-tight">
              <p className="truncate text-sm font-semibold text-white">{usuarioActual.nombre}</p>
              <p className="truncate text-xs text-slate-400">{usuarioActual.rol}</p>
            </div>
            <button
              type="button"
              onClick={handleLogout}
              title="Cerrar sesión"
              className="shrink-0 rounded-lg p-2 text-slate-400 hover:bg-slate-700 hover:text-slate-200 transition-colors"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </aside>

      <div className="flex min-h-screen flex-1 flex-col">
        <header className="sticky top-0 z-40 border-b border-slate-200 bg-white shadow-sm">
          <div className="flex h-16 items-center justify-between px-4 md:px-6 gap-4">
            <div className="flex items-center gap-2 md:hidden">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600">
                <HardHat className="h-4 w-4 text-white" />
              </div>
              <span className="text-sm font-semibold text-slate-900">ObraCalidad</span>
            </div>

            <div className="flex-1 flex items-center justify-center">
              {proyectosAccesibles.length > 0 && (
                <div className="hidden md:flex items-center gap-3">
                  <Building2 className="h-5 w-5 text-slate-400" />
                  <Select value={proyectoSeleccionado} onValueChange={setProyectoSeleccionado}>
                    <SelectTrigger className="w-80 border-slate-200 bg-white hover:border-blue-400 transition-colors">
                      <SelectValue placeholder="Selecciona un proyecto">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-slate-900">
                            {proyectosAccesibles.find(p => p.id === proyectoSeleccionado)?.nombre}
                          </span>
                          <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-1 text-xs font-semibold text-emerald-700">
                            <span className="h-1 w-1 rounded-full bg-emerald-600" />
                            En Ejecución
                          </span>
                        </div>
                      </SelectValue>
                    </SelectTrigger>
                    <SelectContent>
                      {proyectosAccesibles.map((proyecto) => (
                        <SelectItem key={proyecto.id} value={proyecto.id}>
                          {proyecto.nombre}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
            </div>

            <div className="flex items-center gap-4">
              <span className="hidden text-xs font-medium text-slate-500 md:inline">
                Prototipo v2.4
              </span>
              <button
                type="button"
                onClick={handleLogout}
                className="text-slate-600 hover:text-slate-900 md:hidden transition-colors"
                title="Cerrar sesión"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-auto bg-slate-50 p-4 md:p-6">{children}</main>
      </div>
    </div>
  );
}
