import type { Inspeccion, ResultadoInspeccion } from "./types";

export type EstadoVisibleInspeccion = ResultadoInspeccion | "Solucionado";

export function esMatriz(insp: Inspeccion) {
  return insp.tipoRegistro === "matriz";
}

export function estadoVisible(insp: Inspeccion): EstadoVisibleInspeccion {
  return insp.estado === "Solucionado" ? "Solucionado" : insp.resultado;
}

export function progresoSolucion(insp: Inspeccion) {
  const pendientes = insp.items.filter((i) => i.respuesta === "no_cumple");
  const solucionados = pendientes.filter((i) => i.solucionado).length;
  return { total: pendientes.length, solucionados };
}

export function puedeMarcarComoSolucionada(insp: Inspeccion) {
  if (insp.resultado === "Aprobado" || insp.estado === "Solucionado") return false;
  const { total, solucionados } = progresoSolucion(insp);
  return total > 0 && solucionados === total;
}
