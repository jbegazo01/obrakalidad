import type { ColorEtiqueta } from "./types";

export const colorEtiquetaClasses: Record<ColorEtiqueta, string> = {
  red: "bg-red-100 text-red-700 hover:bg-red-100",
  amber: "bg-amber-100 text-amber-700 hover:bg-amber-100",
  slate: "bg-slate-100 text-slate-700 hover:bg-slate-100",
  orange: "bg-orange-100 text-orange-700 hover:bg-orange-100",
  violet: "bg-violet-100 text-violet-700 hover:bg-violet-100",
  teal: "bg-teal-100 text-teal-700 hover:bg-teal-100",
  emerald: "bg-emerald-100 text-emerald-700 hover:bg-emerald-100",
  blue: "bg-blue-100 text-blue-700 hover:bg-blue-100",
};

export const colorEtiquetaDot: Record<ColorEtiqueta, string> = {
  red: "bg-red-500",
  amber: "bg-amber-500",
  slate: "bg-slate-500",
  orange: "bg-orange-500",
  violet: "bg-violet-500",
  teal: "bg-teal-500",
  emerald: "bg-emerald-500",
  blue: "bg-blue-500",
};

export const coloresDisponibles: { value: ColorEtiqueta; label: string }[] = [
  { value: "red", label: "Rojo" },
  { value: "amber", label: "Ámbar" },
  { value: "orange", label: "Naranja" },
  { value: "violet", label: "Violeta" },
  { value: "teal", label: "Verde azulado" },
  { value: "emerald", label: "Verde" },
  { value: "blue", label: "Azul" },
  { value: "slate", label: "Gris" },
];
