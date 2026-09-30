"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const tabs = [
  { href: "/configuracion/usuarios", label: "Usuarios" },
  { href: "/configuracion/estructura-ubicacion", label: "Estructura & Ubicación" },
  { href: "/configuracion/criterios-inspeccion", label: "Criterios de Inspección" },
  { href: "/configuracion/criterios-no-conformidad", label: "Criterios de No Conformidad" },
  { href: "/configuracion/plantilla-pdf", label: "Plantilla de PDF" },
];

export default function ConfiguracionLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Configuración</h1>
        <p className="text-sm text-muted-foreground">
          Administra usuarios y los estándares de calidad propios de tu empresa.
        </p>
      </div>

      <div className="border-b">
        <nav className="flex gap-6">
          {tabs.map((tab) => {
            const active = pathname === tab.href;
            return (
              <Link
                key={tab.href}
                href={tab.href}
                className={cn(
                  "border-b-2 pb-3 text-sm font-medium transition-colors",
                  active
                    ? "border-primary text-foreground"
                    : "border-transparent text-muted-foreground hover:text-foreground"
                )}
              >
                {tab.label}
              </Link>
            );
          })}
        </nav>
      </div>

      {children}
    </div>
  );
}
