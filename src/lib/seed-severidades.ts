import type { SeveridadConfig } from "./types";

export const severidadesSeed: SeveridadConfig[] = [
  { id: "sev-critica", nombre: "Crítica", color: "red", diasSla: 3 },
  { id: "sev-mayor", nombre: "Mayor", color: "amber", diasSla: 7 },
  { id: "sev-menor", nombre: "Menor", color: "slate", diasSla: 14 },
];
