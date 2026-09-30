"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Printer } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAppData } from "@/lib/app-data-context";
import { proyectos } from "@/lib/mock-data";
import { esMatriz as esRegistroMatriz, estadoVisible } from "@/lib/inspeccion-utils";
import type { ChecklistItem, Evidencia, Participante } from "@/lib/types";

function celda(v?: string) {
  return v && v.trim() ? v : "—";
}

function formatearFechaHora(iso: string) {
  const d = new Date(iso);
  return `${d.toLocaleDateString("es-PE")} ${d.toLocaleTimeString("es-PE", {
    hour: "2-digit",
    minute: "2-digit",
  })}`;
}

function formatearFecha(iso?: string) {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("es-PE");
}

function RespuestaMarca({ activo }: { activo: boolean }) {
  return (
    <span className="inline-flex h-4 w-4 items-center justify-center border border-black text-[11px] font-bold leading-none">
      {activo ? "✓" : ""}
    </span>
  );
}

type Foto = { id: string; url: string; nombre: string; caption: string };

export default function ImprimirInspeccionPage() {
  const { id } = useParams<{ id: string }>();
  const { inspecciones, protocolos, empresa, proyectoPdfConfig } = useAppData();

  const inspeccion = inspecciones.find((i) => i.id === id);
  const proyecto = inspeccion ? proyectos.find((p) => p.id === inspeccion.proyectoId) : undefined;
  const protocolo = inspeccion ? protocolos.find((p) => p.nombre === inspeccion.tipo) : undefined;
  const config = proyecto ? proyectoPdfConfig[proyecto.id] ?? {} : {};

  if (!inspeccion || !proyecto) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-white p-6 text-center">
        <p className="text-sm text-muted-foreground">
          No se encontró la inspección. Es posible que la página se haya recargado y se perdieran
          los datos de esta sesión de demostración.
        </p>
        <Link href="/inspecciones" className="text-sm font-medium text-primary hover:underline">
          Volver a Inspecciones
        </Link>
      </div>
    );
  }

  const esMatriz = esRegistroMatriz(inspeccion);
  const nombreOficial = celda(config.nombreOficial) !== "—" ? config.nombreOficial! : proyecto.nombre;
  const tituloDocumento =
    protocolo?.tituloDocumento?.trim() || `PROTOCOLO DE ${inspeccion.tipo}`.toUpperCase();
  const codigoFormato = protocolo?.codigoFormato?.trim() || "";

  const firmantes: Participante[] =
    inspeccion.participantes.length > 0
      ? inspeccion.participantes
      : [
          {
            id: "fallback-inspector",
            nombre: inspeccion.inspector,
            rol: "Inspector",
            firmaUrl: "",
            fechaHora: `${inspeccion.fecha}T00:00:00`,
          },
        ];

  const fotos: Foto[] = [
    ...inspeccion.items.flatMap((item: ChecklistItem) =>
      item.evidencias.map((ev: Evidencia) => ({
        id: ev.id,
        url: ev.url,
        nombre: ev.nombre,
        caption: item.descripcion,
      }))
    ),
    ...inspeccion.evidenciasGenerales.map((ev: Evidencia) => ({
      id: ev.id,
      url: ev.url,
      nombre: ev.nombre,
      caption: "Observación general",
    })),
  ];

  return (
    <div className="min-h-screen bg-neutral-200">
      <style>{`
        @page { size: A4; margin: 12mm; }
        @media print {
          .no-print { display: none !important; }
          .page-break { break-before: page; }
          html, body { background: white !important; }
        }
        * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
      `}</style>

      <div className="no-print sticky top-0 z-10 flex items-center justify-between border-b bg-white px-4 py-3 shadow-sm">
        <Link
          href="/inspecciones"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Volver
        </Link>
        <p className="text-sm font-medium">{inspeccion.codigo}</p>
        <Button size="sm" onClick={() => window.print()}>
          <Printer className="h-4 w-4" />
          Imprimir / Guardar PDF
        </Button>
      </div>

      <div className="mx-auto max-w-[210mm] bg-white p-[12mm] text-black shadow-md print:m-0 print:p-0 print:shadow-none">
        {/* Encabezado */}
        <table className="w-full border-collapse border border-black text-[11px]">
          <tbody>
            <tr>
              <td className="w-28 border border-black p-1 text-center align-middle">
                {empresa.logo && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={empresa.logo.url}
                    alt={empresa.nombre || "Logo contratista"}
                    className="mx-auto max-h-14 max-w-full object-contain"
                  />
                )}
              </td>
              <td className="border border-black p-2 text-center align-middle">
                <p className="text-[12px] font-bold leading-snug">
                  &quot;{nombreOficial.toUpperCase()}&quot;
                  {config.cui && ` - CUI ${config.cui}`}
                </p>
              </td>
              <td className="w-28 border border-black p-1 text-center align-middle">
                {config.logoCliente && (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img
                    src={config.logoCliente.url}
                    alt="Logo cliente"
                    className="mx-auto max-h-14 max-w-full object-contain"
                  />
                )}
              </td>
            </tr>
            <tr>
              <td className="border border-black p-1.5 text-center font-semibold">REV.00</td>
              <td className="border border-black p-1.5 text-center font-bold">{tituloDocumento}</td>
              <td className="border border-black p-1.5 text-center font-semibold">
                {celda(codigoFormato)}
              </td>
            </tr>
          </tbody>
        </table>
        <table className="w-full border-collapse border border-t-0 border-black text-[11px]">
          <tbody>
            <tr>
              <td className="w-1/2 border border-black p-1.5">
                <b>CLIENTE:</b> {celda(proyecto.cliente)}
              </td>
              <td className="w-1/2 border border-black p-1.5">
                <b>SUPERVISIÓN:</b> {celda(config.supervision)}
              </td>
            </tr>
            <tr>
              <td className="border border-black p-1.5">
                <b>UBICACIÓN:</b> {celda(proyecto.ubicacion)}
              </td>
              <td className="border border-black p-1.5">
                <b>N° REGISTRO:</b> {inspeccion.codigo}
              </td>
            </tr>
            <tr>
              <td className="border border-black p-1.5">
                <b>UBICACIÓN / UNIDAD:</b> {celda(`${inspeccion.ubicacion} / ${inspeccion.unidadControl}`)}
              </td>
              <td className="border border-black p-1.5">
                <b>FECHA:</b> {inspeccion.fecha}
              </td>
            </tr>
            <tr>
              <td className="border border-black p-1.5">
                <b>PLANO DE REFERENCIA:</b> {celda(inspeccion.planoReferencia)}
              </td>
              <td className="border border-black p-1.5">
                <b>MATERIAL:</b> {celda(inspeccion.material)}
              </td>
            </tr>
          </tbody>
        </table>

        {esMatriz ? (
          <>
            {/* Matriz de datos */}
            <table className="mt-4 w-full border-collapse border border-black text-[11px]">
              <thead>
                <tr className="bg-neutral-100">
                  <th className="border border-black p-1.5" />
                  {(inspeccion.matrizColumnas ?? []).map((c) => (
                    <th key={c.id} className="border border-black p-1.5 text-center">
                      {c.texto}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(inspeccion.matrizFilas ?? []).map((f) => (
                  <tr key={f.id}>
                    <th className="border border-black bg-neutral-100 p-1.5 text-left">{f.texto}</th>
                    {(inspeccion.matrizColumnas ?? []).map((c) => (
                      <td key={c.id} className="border border-black p-1.5 text-center">
                        {inspeccion.matrizValores?.[`${f.id}_${c.id}`] || "—"}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="mt-2 border border-black p-2 text-[11px]">
              <b>Registro:</b> Matriz de datos informativa (sin cumplimiento asociado)
              {inspeccion.finalizada && " · Finalizada"}
            </div>
          </>
        ) : (
          <>
            {/* Checklist */}
            <table className="mt-4 w-full border-collapse border border-black text-[11px]">
              <thead>
                <tr className="bg-neutral-100">
                  <th className="border border-black p-1 w-7">N°</th>
                  <th className="border border-black p-1 text-left">Criterio de revisión</th>
                  <th className="border border-black p-1 w-14">Cumple</th>
                  <th className="border border-black p-1 w-16">No cumple</th>
                  <th className="border border-black p-1 w-14">No aplica</th>
                  <th className="border border-black p-1 text-left w-[26%]">Observaciones</th>
                </tr>
              </thead>
              <tbody>
                {inspeccion.items.map((item, idx) => (
                  <tr key={item.id}>
                    <td className="border border-black p-1 text-center">{idx + 1}</td>
                    <td className="border border-black p-1">{item.descripcion}</td>
                    <td className="border border-black p-1 text-center">
                      <RespuestaMarca activo={item.respuesta === "cumple"} />
                    </td>
                    <td className="border border-black p-1 text-center">
                      <RespuestaMarca activo={item.respuesta === "no_cumple"} />
                    </td>
                    <td className="border border-black p-1 text-center">
                      <RespuestaMarca activo={item.respuesta === "no_aplica"} />
                    </td>
                    <td className="border border-black p-1">
                      {item.comentario || ""}
                      {item.respuesta === "no_cumple" && (
                        <span
                          className={
                            item.solucionado
                              ? "ml-1 font-semibold text-emerald-700"
                              : "ml-1 font-semibold text-red-700"
                          }
                        >
                          {item.solucionado
                            ? `(Solucionado ${formatearFecha(item.fechaSolucion)})`
                            : "(Pendiente de solución)"}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className="mt-2 flex items-center justify-between border border-black p-2 text-[11px]">
              <span>
                <b>Cumplimiento:</b> {inspeccion.cumplimiento}%
              </span>
              <span>
                <b>Resultado:</b> {estadoVisible(inspeccion)}
                {inspeccion.estado === "Solucionado" && ` (hallazgo original: ${inspeccion.resultado})`}
                {inspeccion.finalizada && " · Finalizada"}
              </span>
            </div>
          </>
        )}

        {inspeccion.comentarioGeneral && (
          <div className="mt-2 border border-black p-2 text-[11px]">
            <b>Observaciones generales:</b> {inspeccion.comentarioGeneral}
          </div>
        )}

        {/* Firmas */}
        <div className="mt-6">
          <p className="mb-2 text-[11px] font-bold uppercase">Firmas de participantes</p>
          <div className="grid grid-cols-3 gap-x-4 gap-y-6">
            {firmantes.map((f) => (
              <div key={f.id} className="text-center">
                <div className="flex h-16 items-end justify-center border-b border-black">
                  {f.firmaUrl && (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={f.firmaUrl} alt={`Firma de ${f.nombre}`} className="max-h-16 object-contain" />
                  )}
                </div>
                <p className="mt-1 text-[11px] font-medium">{f.nombre}</p>
                <p className="text-[10px] text-neutral-600">{f.rol}</p>
                <p className="text-[10px] text-neutral-600">{formatearFechaHora(f.fechaHora)}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Panel fotográfico */}
        <div className="page-break pt-4">
          <h2 className="mb-1 text-center text-[13px] font-bold uppercase">
            Panel fotográfico — Evidencias
          </h2>
          <p className="mb-4 text-center text-[11px] text-neutral-600">
            {inspeccion.codigo} — {inspeccion.ubicacion} / {inspeccion.unidadControl}
          </p>
          {fotos.length === 0 ? (
            <p className="text-center text-[11px] text-neutral-500">
              No se adjuntaron evidencias fotográficas.
            </p>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              {fotos.map((f) => (
                <div key={f.id} className="border border-black p-1">
                  <div className="flex aspect-[4/3] w-full items-center justify-center overflow-hidden bg-neutral-100">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img src={f.url} alt={f.nombre} className="h-full w-full object-cover" />
                  </div>
                  <p className="mt-1 text-center text-[10px]">{f.caption}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
