import type { Evidencia } from "./types";

let contador = 0;

function leerComoDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

// Se guarda como data URL (base64) en vez de un blob URL temporal: así la evidencia
// sobrevive al guardarse en localStorage y a recargar la página. Tiene un límite real de
// tamaño (localStorage ronda los 5-10MB por sitio) — suficiente para probar, no para producción.
export async function filesToEvidencias(files: FileList): Promise<Evidencia[]> {
  const archivos = Array.from(files);
  const urls = await Promise.all(archivos.map(leerComoDataUrl));
  return archivos.map((file, i) => ({
    id: `ev-${Date.now()}-${contador++}`,
    nombre: file.name,
    url: urls[i],
    tipo: file.type.startsWith("image/") ? "imagen" : "archivo",
  }));
}

export function revocarEvidencia(evidencia: Evidencia) {
  // Los data URL no requieren liberarse; se deja como no-op seguro para no romper
  // el resto de las llamadas existentes (URL.revokeObjectURL en un data: URL no hace nada).
  if (evidencia.url.startsWith("blob:")) {
    URL.revokeObjectURL(evidencia.url);
  }
}
