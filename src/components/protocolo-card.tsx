"use client";

import { useState } from "react";
import { Plus, Table2, Trash2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAppData } from "@/lib/app-data-context";
import type { EjeItem, ProtocoloInspeccion } from "@/lib/types";

function EjeList({
  titulo,
  placeholder,
  items,
  onAdd,
  onRemove,
}: {
  titulo: string;
  placeholder: string;
  items: EjeItem[];
  onAdd: (texto: string) => void;
  onRemove: (id: string) => void;
}) {
  const [nuevo, setNuevo] = useState("");

  function handleAdd() {
    const texto = nuevo.trim();
    if (!texto) return;
    onAdd(texto);
    setNuevo("");
  }

  return (
    <div className="space-y-1.5">
      <p className="text-xs font-medium text-muted-foreground">{titulo}</p>
      {items.length === 0 && (
        <p className="text-xs text-muted-foreground">Sin elementos todavía.</p>
      )}
      {items.map((it) => (
        <div
          key={it.id}
          className="flex items-center justify-between gap-2 rounded-md bg-muted/50 px-2.5 py-1 text-sm"
        >
          <span>{it.texto}</span>
          <button
            type="button"
            onClick={() => onRemove(it.id)}
            className="shrink-0 text-muted-foreground hover:text-destructive"
            aria-label="Eliminar"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      ))}
      <div className="flex items-center gap-2">
        <Input
          placeholder={placeholder}
          value={nuevo}
          onChange={(e) => setNuevo(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              handleAdd();
            }
          }}
          className="h-8 text-sm"
        />
        <Button variant="outline" size="icon-sm" onClick={handleAdd}>
          <Plus className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

export function ProtocoloCard({ protocolo }: { protocolo: ProtocoloInspeccion }) {
  const {
    addCriterio,
    removeCriterio,
    removeProtocolo,
    updateProtocoloMeta,
    addColumnaMatriz,
    removeColumnaMatriz,
    addFilaMatriz,
    removeFilaMatriz,
  } = useAppData();
  const [nuevoCriterio, setNuevoCriterio] = useState("");

  function handleAddCriterio() {
    const texto = nuevoCriterio.trim();
    if (!texto) return;
    addCriterio(protocolo.id, texto);
    setNuevoCriterio("");
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div className="flex items-center gap-2">
          <CardTitle className="text-base">{protocolo.nombre}</CardTitle>
          {protocolo.tipo === "matriz" && (
            <Badge className="gap-1 bg-violet-100 text-violet-700 hover:bg-violet-100">
              <Table2 className="h-3 w-3" />
              Matriz
            </Badge>
          )}
        </div>
        <Button
          variant="ghost"
          size="icon-sm"
          className="text-muted-foreground hover:text-destructive"
          onClick={() => removeProtocolo(protocolo.id)}
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid grid-cols-1 gap-2 rounded-md bg-muted/40 p-2.5 sm:grid-cols-2">
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Título en el PDF (opcional)</label>
            <Input
              placeholder={`Ej. PROTOCOLO DE ${protocolo.nombre.toUpperCase()}`}
              defaultValue={protocolo.tituloDocumento ?? ""}
              onBlur={(e) => updateProtocoloMeta(protocolo.id, { tituloDocumento: e.target.value })}
              className="h-7 text-xs"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Código de formato (opcional)</label>
            <Input
              placeholder="Ej. REG-SIG-40"
              defaultValue={protocolo.codigoFormato ?? ""}
              onBlur={(e) => updateProtocoloMeta(protocolo.id, { codigoFormato: e.target.value })}
              className="h-7 text-xs"
            />
          </div>
        </div>

        {protocolo.tipo === "matriz" ? (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <EjeList
              titulo="Columnas (eje X)"
              placeholder="Ej. Punto 1"
              items={protocolo.columnas}
              onAdd={(texto) => addColumnaMatriz(protocolo.id, texto)}
              onRemove={(id) => removeColumnaMatriz(protocolo.id, id)}
            />
            <EjeList
              titulo="Filas (eje Y)"
              placeholder="Ej. Cota real"
              items={protocolo.filas}
              onAdd={(texto) => addFilaMatriz(protocolo.id, texto)}
              onRemove={(id) => removeFilaMatriz(protocolo.id, id)}
            />
          </div>
        ) : (
          <>
            {protocolo.criterios.length === 0 && (
              <p className="text-xs text-muted-foreground">Sin criterios configurados todavía.</p>
            )}
            {protocolo.criterios.map((c) => (
              <div
                key={c.id}
                className="flex items-center justify-between gap-2 rounded-md bg-muted/50 px-3 py-1.5 text-sm"
              >
                <span>{c.texto}</span>
                <button
                  type="button"
                  onClick={() => removeCriterio(protocolo.id, c.id)}
                  className="shrink-0 text-muted-foreground hover:text-destructive"
                  aria-label="Eliminar criterio"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            ))}
            <div className="flex items-center gap-2 pt-1">
              <Input
                placeholder="Nuevo criterio de revisión..."
                value={nuevoCriterio}
                onChange={(e) => setNuevoCriterio(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    handleAddCriterio();
                  }
                }}
                className="h-8 text-sm"
              />
              <Button variant="outline" size="icon-sm" onClick={handleAddCriterio}>
                <Plus className="h-4 w-4" />
              </Button>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
