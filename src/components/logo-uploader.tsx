"use client";

import { useRef } from "react";
import { ImagePlus, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Evidencia } from "@/lib/types";
import { filesToEvidencias, revocarEvidencia } from "@/lib/evidencia";

export function LogoUploader({
  logo,
  onChange,
  label = "Subir logo",
}: {
  logo?: Evidencia;
  onChange: (logo: Evidencia | undefined) => void;
  label?: string;
}) {
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleFiles(e: React.ChangeEvent<HTMLInputElement>) {
    const { files } = e.target;
    if (files && files.length > 0) {
      const [nuevo] = await filesToEvidencias(files);
      if (logo) revocarEvidencia(logo);
      onChange(nuevo);
    }
    e.target.value = "";
  }

  function quitar() {
    if (logo) revocarEvidencia(logo);
    onChange(undefined);
  }

  if (logo) {
    return (
      <div className="flex items-center gap-3">
        <div className="flex h-16 w-32 items-center justify-center overflow-hidden rounded-md border bg-white p-1">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={logo.url} alt={logo.nombre} className="max-h-full max-w-full object-contain" />
        </div>
        <Button type="button" variant="outline" size="sm" onClick={quitar}>
          <X className="h-3.5 w-3.5" />
          Quitar
        </Button>
      </div>
    );
  }

  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleFiles}
      />
      <Button type="button" variant="outline" size="sm" onClick={() => inputRef.current?.click()}>
        <ImagePlus className="h-3.5 w-3.5" />
        {label}
      </Button>
    </div>
  );
}
