"use client";

import { useRef } from "react";
import { FileText, Paperclip, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Evidencia } from "@/lib/types";
import { filesToEvidencias, revocarEvidencia } from "@/lib/evidencia";

export function EvidenceUploader({
  evidencias,
  onAdd,
  onRemove,
  label = "Adjuntar evidencia",
}: {
  evidencias: Evidencia[];
  onAdd: (evidencias: Evidencia[]) => void;
  onRemove: (id: string) => void;
  label?: string;
}) {
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleFiles(e: React.ChangeEvent<HTMLInputElement>) {
    const { files } = e.target;
    if (files && files.length > 0) {
      onAdd(await filesToEvidencias(files));
    }
    e.target.value = "";
  }

  function handleRemove(ev: Evidencia) {
    revocarEvidencia(ev);
    onRemove(ev.id);
  }

  return (
    <div className="space-y-2">
      {evidencias.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {evidencias.map((ev) => (
            <div
              key={ev.id}
              className="group relative h-16 w-16 overflow-hidden rounded-md border bg-muted"
            >
              {ev.tipo === "imagen" ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={ev.url} alt={ev.nombre} className="h-full w-full object-cover" />
              ) : (
                <div className="flex h-full w-full flex-col items-center justify-center gap-1 p-1">
                  <FileText className="h-5 w-5 text-muted-foreground" />
                  <span className="w-full truncate text-center text-[9px] text-muted-foreground">
                    {ev.nombre}
                  </span>
                </div>
              )}
              <button
                type="button"
                onClick={() => handleRemove(ev)}
                className="absolute top-0.5 right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-black/60 text-white opacity-0 transition-opacity group-hover:opacity-100"
                aria-label="Quitar evidencia"
              >
                <X className="h-3 w-3" />
              </button>
            </div>
          ))}
        </div>
      )}
      <input
        ref={inputRef}
        type="file"
        multiple
        accept="image/*,.pdf,.doc,.docx"
        className="hidden"
        onChange={handleFiles}
      />
      <Button
        type="button"
        variant="outline"
        size="sm"
        className="h-7 text-xs"
        onClick={() => inputRef.current?.click()}
      >
        <Paperclip className="h-3.5 w-3.5" />
        {label}
      </Button>
    </div>
  );
}
