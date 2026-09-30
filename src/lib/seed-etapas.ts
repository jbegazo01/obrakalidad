import type { EtapaConstructiva } from "./types";

export const etapasSeed: EtapaConstructiva[] = [
  {
    id: "etapa-1",
    nombre: "ESTRUCTURAS",
    descripcion: "Concreto, encofrado, acero y trabajos estructurales",
    orden: 1,
  },
  {
    id: "etapa-2",
    nombre: "ACABADOS",
    descripcion: "Pintura, revestimientos, pisos y acabados finales",
    orden: 2,
  },
  {
    id: "etapa-3",
    nombre: "INSTALACIONES",
    descripcion: "Instalaciones eléctricas, sanitarias y HVAC",
    orden: 3,
  },
];
