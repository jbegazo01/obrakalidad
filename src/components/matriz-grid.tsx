"use client";

import { Input } from "@/components/ui/input";
import type { EjeItem } from "@/lib/types";

export function MatrizGrid({
  columnas,
  filas,
  valores,
  editable,
  onChange,
}: {
  columnas: EjeItem[];
  filas: EjeItem[];
  valores: Record<string, string>;
  editable: boolean;
  onChange?: (clave: string, valor: string) => void;
}) {
  if (columnas.length === 0 || filas.length === 0) {
    return (
      <p className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-700">
        Este protocolo aún no tiene filas o columnas configuradas. Agrégalas en Configuración →
        Criterios de Inspección.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto rounded-md border">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr>
            <th className="border-b border-r bg-muted/50 p-2" />
            {columnas.map((c) => (
              <th
                key={c.id}
                className="border-b border-r p-2 text-center text-xs font-medium text-muted-foreground last:border-r-0"
              >
                {c.texto}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {filas.map((f) => (
            <tr key={f.id}>
              <th className="border-r bg-muted/50 p-2 text-left text-xs font-medium text-muted-foreground">
                {f.texto}
              </th>
              {columnas.map((c) => {
                const clave = `${f.id}_${c.id}`;
                return (
                  <td key={c.id} className="border-r p-1 last:border-r-0">
                    {editable ? (
                      <Input
                        value={valores[clave] ?? ""}
                        onChange={(e) => onChange?.(clave, e.target.value)}
                        className="h-8 w-full text-center text-sm"
                      />
                    ) : (
                      <p className="px-2 py-1 text-center text-sm">{valores[clave] || "—"}</p>
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
