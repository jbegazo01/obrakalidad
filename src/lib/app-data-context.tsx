"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { cargar, guardar } from "./persistencia";
import type {
  ChecklistItem,
  ConfigEstructura,
  ConfiguracionRolesRevision,
  EjeItem,
  Empresa,
  EstadoRevisionInspeccion,
  EtapaConstructiva,
  Evidencia,
  Inspeccion,
  NoConformidad,
  Participante,
  Proyecto,
  ProtocoloInspeccion,
  ProyectoPdfConfig,
  RegistroRevision,
  ResultadoInspeccion,
  RolUsuario,
  SeveridadConfig,
  TipoProtocolo,
  TipoRegistro,
  UnidadPlanificada,
  Usuario,
} from "./types";

type AgregarRegistroRevisionInput = {
  inspeccionId: string;
  rol: string;
  nombreRevisor: string;
  comentario?: string;
};
import { inspecciones as inspeccionesSeed, noConformidades as noConformidadesSeed, proyectos as proyectosMockData, configuracionesRolesRevision as configuracionesRolesRevisionSeed } from "./mock-data";
import { protocolosSeed } from "./seed-protocolos";
import { severidadesSeed } from "./seed-severidades";
import { usuariosSeed } from "./seed-usuarios";
import { etapasSeed } from "./seed-etapas";

function resultadoDeCumplimiento(items: ChecklistItem[]): ResultadoInspeccion {
  if (items.length === 0) return "Nuevo";

  const tieneNoCumple = items.some((i) => i.respuesta === "no_cumple");
  if (tieneNoCumple) return "Falla";

  const todosRespondidos = items.every((i) => i.respuesta !== null);
  if (todosRespondidos) return "Aprobado";

  const algunoRespondido = items.some((i) => i.respuesta !== null);
  if (algunoRespondido) return "En Proceso";

  return "Nuevo";
}

// Los criterios marcados "no_aplica" se excluyen del cálculo: no deben penalizar
// ni favorecer el cumplimiento de un protocolo que no les correspondía.
function calcularCumplimiento(items: ChecklistItem[]) {
  const aplicables = items.filter((i) => i.respuesta !== "no_aplica");
  if (aplicables.length === 0) return 100;
  const cumplen = aplicables.filter((i) => i.respuesta === "cumple").length;
  return Math.round((cumplen / aplicables.length) * 100);
}

type NuevaInspeccionInput = {
  proyectoId: string;
  ubicacion: string;
  unidadControl: string;
  unidadPlanificadaId?: string;
  protocoloId: string;
  tipo: string;
  tipoRegistro: TipoRegistro;
  inspector: string;
  items: ChecklistItem[];
  matrizColumnas?: EjeItem[];
  matrizFilas?: EjeItem[];
  matrizValores?: Record<string, string>;
  comentarioGeneral?: string;
  evidenciasGenerales?: Evidencia[];
  planoReferencia?: string;
  material?: string;
  participantes?: Participante[];
  estadoRevision: EstadoRevisionInspeccion;
  registrosRevision: RegistroRevision[];
};

type NuevaNCInput = {
  proyectoId: string;
  ubicacion: string;
  unidadControl: string;
  descripcion: string;
  severidad: string;
  responsable: string;
  fechaLimite: string;
  inspeccionOriginId?: string;
};

type NuevaEstructuraInput = {
  proyectoId: string;
  labelUbicacion: string;
  labelUnidadControl: string;
};

type NuevaUnidadPlanificadaInput = {
  estructuraId: string;
  ubicacion: string;
  unidadControl: string;
};

type NuevoUsuarioInput = {
  nombre: string;
  email: string;
  rol: RolUsuario;
};

type AppDataContextValue = {
  inspecciones: Inspeccion[];
  addInspeccion: (input: NuevaInspeccionInput) => Inspeccion;
  marcarCriterioSolucionado: (inspeccionId: string, itemId: string, solucionado: boolean) => void;
  marcarInspeccionSolucionada: (inspeccionId: string) => void;
  actualizarItemCriterio: (
    inspeccionId: string,
    itemId: string,
    patch: Partial<Pick<ChecklistItem, "respuesta" | "comentario" | "evidencias">>
  ) => void;
  actualizarGeneral: (
    inspeccionId: string,
    patch: Partial<Pick<Inspeccion, "comentarioGeneral" | "evidenciasGenerales">>
  ) => void;
  actualizarValorMatriz: (inspeccionId: string, clave: string, valor: string) => void;
  finalizarInspeccion: (inspeccionId: string) => void;
  agregarRegistroRevision: (input: AgregarRegistroRevisionInput) => void;
  obtenerRolesDeRevision: (proyectoId: string) => string[];
  obtenerConfiguracionRoles: (proyectoId: string) => ConfiguracionRolesRevision | undefined;

  noConformidades: NoConformidad[];
  addNoConformidad: (input: NuevaNCInput) => NoConformidad;
  avanzarEstadoNC: (id: string, nuevoEstado: NoConformidad["estado"]) => void;

  usuarios: Usuario[];
  addUsuario: (input: NuevoUsuarioInput) => void;
  toggleEstadoUsuario: (id: string) => void;

  etapasConstructivas: EtapaConstructiva[];
  addEtapa: (nombre: string, descripcion?: string) => void;
  deleteEtapa: (etapaId: string) => void;
  updateEtapa: (etapaId: string, patch: Partial<Pick<EtapaConstructiva, "nombre" | "descripcion">>) => void;

  protocolos: ProtocoloInspeccion[];
  addProtocolo: (nombre: string, tipo: TipoProtocolo) => void;
  removeProtocolo: (id: string) => void;
  addCriterio: (protocoloId: string, texto: string) => void;
  removeCriterio: (protocoloId: string, criterioId: string) => void;
  addColumnaMatriz: (protocoloId: string, texto: string) => void;
  removeColumnaMatriz: (protocoloId: string, columnaId: string) => void;
  addFilaMatriz: (protocoloId: string, texto: string) => void;
  removeFilaMatriz: (protocoloId: string, filaId: string) => void;
  updateProtocoloMeta: (
    protocoloId: string,
    patch: Partial<Pick<ProtocoloInspeccion, "codigoFormato" | "tituloDocumento">>
  ) => void;

  severidades: SeveridadConfig[];
  addSeveridad: (input: Omit<SeveridadConfig, "id">) => void;
  removeSeveridad: (id: string) => void;

  empresa: Empresa;
  updateEmpresa: (patch: Partial<Empresa>) => void;

  proyectoPdfConfig: Record<string, ProyectoPdfConfig>;
  updateProyectoPdfConfig: (proyectoId: string, patch: Partial<ProyectoPdfConfig>) => void;

  estructurasConfig: ConfigEstructura[];
  addEstructura: (input: NuevaEstructuraInput) => ConfigEstructura;
  updateEstructura: (estructuraId: string, patch: Partial<Pick<ConfigEstructura, "labelUbicacion" | "labelUnidadControl">>) => void;
  removeEstructura: (estructuraId: string) => void;

  unidadesPlanificadas: UnidadPlanificada[];
  addUnidadPlanificada: (input: NuevaUnidadPlanificadaInput) => UnidadPlanificada;
  updateUnidadPlanificada: (id: string, patch: Partial<Pick<UnidadPlanificada, "ubicacion" | "unidadControl" | "estado">>) => void;
  removeUnidadPlanificada: (id: string) => void;
  liberarUnidadPlanificada: (unidadId: string, inspeccionId: string) => void;

  proyectos: Proyecto[];
};

const AppDataContext = createContext<AppDataContextValue | null>(null);

// Con datos persistidos entre sesiones, un contador que reinicia en cada carga de página
// podía repetir IDs ya usados anteriormente. Se agrega el timestamp para evitar choques.
let counter = 1000;
const nextId = (prefix: string) => `${prefix}-${Date.now().toString(36)}-${counter++}`;

export function AppDataProvider({ children }: { children: React.ReactNode }) {
  const [inspecciones, setInspecciones] = useState<Inspeccion[]>(() =>
    cargar("inspecciones", inspeccionesSeed)
  );
  const [noConformidades, setNoConformidades] = useState<NoConformidad[]>(() =>
    cargar("noConformidades", noConformidadesSeed)
  );
  const [usuarios, setUsuarios] = useState<Usuario[]>(() => cargar("usuarios", usuariosSeed));
  const [etapasConstructivas, setEtapasConstructivas] = useState<EtapaConstructiva[]>(() =>
    cargar("etapasConstructivas", etapasSeed)
  );
  const [protocolos, setProtocolos] = useState<ProtocoloInspeccion[]>(() =>
    cargar("protocolos", protocolosSeed)
  );
  const [severidades, setSeveridades] = useState<SeveridadConfig[]>(() =>
    cargar("severidades", severidadesSeed)
  );
  const [empresa, setEmpresa] = useState<Empresa>(() => cargar("empresa", { nombre: "" }));
  const [proyectoPdfConfig, setProyectoPdfConfig] = useState<Record<string, ProyectoPdfConfig>>(
    () => cargar("proyectoPdfConfig", {})
  );
  const [estructurasConfig, setEstructurasConfig] = useState<ConfigEstructura[]>(() =>
    cargar("estructurasConfig", [])
  );
  const [unidadesPlanificadas, setUnidadesPlanificadas] = useState<UnidadPlanificada[]>(() =>
    cargar("unidadesPlanificadas", [])
  );
  const [proyectos, setProyectos] = useState<Proyecto[]>(() =>
    cargar("proyectos", proyectosMockData)
  );
  const [configuracionesRolesRevision, setConfiguracionesRolesRevision] = useState<ConfiguracionRolesRevision[]>(() =>
    cargar("configuracionesRolesRevision", configuracionesRolesRevisionSeed)
  );

  // Cada vez que algo cambia, se refleja en localStorage — así "recuerda" entre recargas
  // y entre sesiones de distintos usuarios en el mismo navegador.
  useEffect(() => guardar("inspecciones", inspecciones), [inspecciones]);
  useEffect(() => guardar("noConformidades", noConformidades), [noConformidades]);
  useEffect(() => guardar("usuarios", usuarios), [usuarios]);
  useEffect(() => guardar("etapasConstructivas", etapasConstructivas), [etapasConstructivas]);
  useEffect(() => guardar("protocolos", protocolos), [protocolos]);
  useEffect(() => guardar("severidades", severidades), [severidades]);
  useEffect(() => guardar("empresa", empresa), [empresa]);
  useEffect(() => guardar("proyectoPdfConfig", proyectoPdfConfig), [proyectoPdfConfig]);
  useEffect(() => guardar("estructurasConfig", estructurasConfig), [estructurasConfig]);
  useEffect(() => guardar("unidadesPlanificadas", unidadesPlanificadas), [unidadesPlanificadas]);
  useEffect(() => guardar("proyectos", proyectos), [proyectos]);
  useEffect(() => guardar("configuracionesRolesRevision", configuracionesRolesRevision), [configuracionesRolesRevision]);

  function addInspeccion(input: NuevaInspeccionInput) {
    // Las matrices de datos son puramente informativas: no calculan cumplimiento ni
    // resultado, se guardan en "Aprobado"/100% como valores neutros para que no aparezcan
    // en los filtros ni estadísticas de conformidad (ver esMatriz() en inspeccion-utils).
    const esMatriz = input.tipoRegistro === "matriz";
    const cumplimiento = esMatriz ? 100 : calcularCumplimiento(input.items);
    const nueva: Inspeccion = {
      id: nextId("insp"),
      codigo: `INS-2026-${Math.floor(100 + Math.random() * 900)}`,
      proyectoId: input.proyectoId,
      ubicacion: input.ubicacion,
      unidadControl: input.unidadControl,
      unidadPlanificadaId: input.unidadPlanificadaId,
      protocoloId: input.protocoloId,
      tipo: input.tipo,
      tipoRegistro: input.tipoRegistro,
      fecha: new Date().toISOString().slice(0, 10),
      inspector: input.inspector,
      resultado: esMatriz ? "Aprobado" : resultadoDeCumplimiento(input.items),
      cumplimiento,
      items: input.items,
      matrizColumnas: input.matrizColumnas,
      matrizFilas: input.matrizFilas,
      matrizValores: input.matrizValores,
      comentarioGeneral: input.comentarioGeneral,
      evidenciasGenerales: input.evidenciasGenerales ?? [],
      planoReferencia: input.planoReferencia,
      material: input.material,
      participantes: input.participantes ?? [],
      estado: "Pendiente",
      estadoRevision: input.estadoRevision,
      registrosRevision: input.registrosRevision,
      finalizada: false,
    };
    setInspecciones((prev) => [nueva, ...prev]);

    if (input.unidadPlanificadaId) {
      liberarUnidadPlanificada(input.unidadPlanificadaId, nueva.id);
    }

    return nueva;
  }

  function actualizarValorMatriz(inspeccionId: string, clave: string, valor: string) {
    setInspecciones((prev) =>
      prev.map((insp) =>
        insp.id === inspeccionId && !insp.finalizada
          ? { ...insp, matrizValores: { ...insp.matrizValores, [clave]: valor } }
          : insp
      )
    );
  }

  // Mientras la inspección no esté finalizada, se puede corregir cualquier criterio: su
  // respuesta (ej. algo dado por conforme que luego resultó con un error), su comentario o
  // su evidencia. Si cambia la respuesta, recalcula cumplimiento/resultado y, si ya no
  // aplica, retrocede el estado "Solucionado".
  function actualizarItemCriterio(
    inspeccionId: string,
    itemId: string,
    patch: Partial<Pick<ChecklistItem, "respuesta" | "comentario" | "evidencias">>
  ) {
    setInspecciones((prev) =>
      prev.map((insp) => {
        if (insp.id !== inspeccionId || insp.finalizada) return insp;

        const items = insp.items.map((item) => {
          if (item.id !== itemId) return item;
          const actualizado = { ...item, ...patch };
          if (patch.respuesta !== undefined && patch.respuesta !== "no_cumple") {
            actualizado.solucionado = false;
            actualizado.fechaSolucion = undefined;
          }
          return actualizado;
        });

        if (patch.respuesta === undefined) {
          return { ...insp, items };
        }

        const cumplimiento = calcularCumplimiento(items);
        const resultado = resultadoDeCumplimiento(items);

        let estado = insp.estado;
        let fechaSolucionInspeccion = insp.fechaSolucionInspeccion;
        if (resultado === "Aprobado") {
          estado = "Pendiente";
          fechaSolucionInspeccion = undefined;
        } else if (insp.estado === "Solucionado") {
          const todosSolucionados = items
            .filter((i) => i.respuesta === "no_cumple")
            .every((i) => i.solucionado);
          if (!todosSolucionados) {
            estado = "Pendiente";
            fechaSolucionInspeccion = undefined;
          }
        }

        return { ...insp, items, cumplimiento, resultado, estado, fechaSolucionInspeccion };
      })
    );
  }

  function actualizarGeneral(
    inspeccionId: string,
    patch: Partial<Pick<Inspeccion, "comentarioGeneral" | "evidenciasGenerales">>
  ) {
    setInspecciones((prev) =>
      prev.map((insp) => (insp.id === inspeccionId && !insp.finalizada ? { ...insp, ...patch } : insp))
    );
  }

  function finalizarInspeccion(inspeccionId: string) {
    setInspecciones((prev) =>
      prev.map((insp) =>
        insp.id === inspeccionId
          ? { ...insp, finalizada: true, fechaFinalizacion: new Date().toISOString() }
          : insp
      )
    );
  }

  function marcarCriterioSolucionado(inspeccionId: string, itemId: string, solucionado: boolean) {
    setInspecciones((prev) =>
      prev.map((insp) =>
        insp.id === inspeccionId && !insp.finalizada
          ? {
              ...insp,
              items: insp.items.map((item) =>
                item.id === itemId
                  ? {
                      ...item,
                      solucionado,
                      fechaSolucion: solucionado ? new Date().toISOString() : undefined,
                    }
                  : item
              ),
            }
          : insp
      )
    );
  }

  function marcarInspeccionSolucionada(inspeccionId: string) {
    setInspecciones((prev) =>
      prev.map((insp) =>
        insp.id === inspeccionId && !insp.finalizada
          ? { ...insp, estado: "Solucionado", fechaSolucionInspeccion: new Date().toISOString() }
          : insp
      )
    );
  }

  function agregarRegistroRevision(input: AgregarRegistroRevisionInput) {
    setInspecciones((prev) =>
      prev.map((insp) => {
        if (insp.id !== input.inspeccionId) return insp;

        const nuevosRegistros = [
          ...insp.registrosRevision,
          {
            id: `rev-${Date.now()}`,
            rol: input.rol,
            nombreRevisor: input.nombreRevisor,
            comentario: input.comentario,
            fechaHora: new Date().toISOString(),
          },
        ];

        // Determinar nuevo estado basándose en revisiones completadas
        const config = configuracionesRolesRevision.find((c) => c.proyectoId === insp.proyectoId);
        const rolesConfigurados = config?.rolesRevision ?? [];
        const rolesQueRevisaron = new Set(nuevosRegistros.map((r) => r.rol));
        const todasLasRevisionesCompletas = rolesConfigurados.every((rol) => rolesQueRevisaron.has(rol));

        const nuevoEstado: EstadoRevisionInspeccion = todasLasRevisionesCompletas
          ? "Revisiones Completadas"
          : "En Revisión";

        return {
          ...insp,
          estadoRevision: nuevoEstado,
          registrosRevision: nuevosRegistros,
        };
      })
    );
  }

  function addNoConformidad(input: NuevaNCInput) {
    const nueva: NoConformidad = {
      id: nextId("nc"),
      codigo: `NC-2026-${Math.floor(100 + Math.random() * 900)}`,
      proyectoId: input.proyectoId,
      ubicacion: input.ubicacion,
      unidadControl: input.unidadControl,
      descripcion: input.descripcion,
      severidad: input.severidad,
      estado: "Abierta",
      responsable: input.responsable,
      fechaApertura: new Date().toISOString().slice(0, 10),
      fechaLimite: input.fechaLimite,
      inspeccionOriginId: input.inspeccionOriginId,
    };
    setNoConformidades((prev) => [nueva, ...prev]);
    return nueva;
  }

  function avanzarEstadoNC(id: string, nuevoEstado: NoConformidad["estado"]) {
    setNoConformidades((prev) =>
      prev.map((n) => (n.id === id ? { ...n, estado: nuevoEstado } : n))
    );
  }

  function addUsuario(input: NuevoUsuarioInput) {
    const nuevo: Usuario = {
      id: nextId("user"),
      nombre: input.nombre,
      email: input.email,
      rol: input.rol,
      estado: "Activo",
      fechaCreacion: new Date().toISOString().slice(0, 10),
      proyectoIds: [],
    };
    setUsuarios((prev) => [nuevo, ...prev]);
    return nuevo;
  }

  function toggleEstadoUsuario(id: string) {
    setUsuarios((prev) =>
      prev.map((u) =>
        u.id === id ? { ...u, estado: u.estado === "Activo" ? "Inactivo" : "Activo" } : u
      )
    );
  }

  function addEtapa(nombre: string, descripcion?: string) {
    setEtapasConstructivas((prev) => [
      ...prev,
      { id: nextId("etapa"), nombre, descripcion, orden: prev.length + 1 },
    ]);
  }

  function deleteEtapa(etapaId: string) {
    setEtapasConstructivas((prev) => prev.filter((e) => e.id !== etapaId));
  }

  function updateEtapa(etapaId: string, patch: Partial<Pick<EtapaConstructiva, "nombre" | "descripcion">>) {
    setEtapasConstructivas((prev) =>
      prev.map((e) => (e.id === etapaId ? { ...e, ...patch } : e))
    );
  }

  function addProtocolo(nombre: string, tipo: TipoProtocolo, etapaId: string = "etapa-1") {
    setProtocolos((prev) => [
      ...prev,
      { id: nextId("proto"), etapaId, nombre, tipo, criterios: [], columnas: [], filas: [] },
    ]);
  }

  function addColumnaMatriz(protocoloId: string, texto: string) {
    setProtocolos((prev) =>
      prev.map((p) =>
        p.id === protocoloId
          ? { ...p, columnas: [...p.columnas, { id: nextId("col"), texto }] }
          : p
      )
    );
  }

  function removeColumnaMatriz(protocoloId: string, columnaId: string) {
    setProtocolos((prev) =>
      prev.map((p) =>
        p.id === protocoloId
          ? { ...p, columnas: p.columnas.filter((c) => c.id !== columnaId) }
          : p
      )
    );
  }

  function addFilaMatriz(protocoloId: string, texto: string) {
    setProtocolos((prev) =>
      prev.map((p) =>
        p.id === protocoloId ? { ...p, filas: [...p.filas, { id: nextId("fila"), texto }] } : p
      )
    );
  }

  function removeFilaMatriz(protocoloId: string, filaId: string) {
    setProtocolos((prev) =>
      prev.map((p) =>
        p.id === protocoloId ? { ...p, filas: p.filas.filter((f) => f.id !== filaId) } : p
      )
    );
  }

  function removeProtocolo(id: string) {
    setProtocolos((prev) => prev.filter((p) => p.id !== id));
  }

  function addCriterio(protocoloId: string, texto: string) {
    setProtocolos((prev) =>
      prev.map((p) =>
        p.id === protocoloId
          ? { ...p, criterios: [...p.criterios, { id: nextId("crit"), texto }] }
          : p
      )
    );
  }

  function removeCriterio(protocoloId: string, criterioId: string) {
    setProtocolos((prev) =>
      prev.map((p) =>
        p.id === protocoloId
          ? { ...p, criterios: p.criterios.filter((c) => c.id !== criterioId) }
          : p
      )
    );
  }

  function addSeveridad(input: Omit<SeveridadConfig, "id">) {
    setSeveridades((prev) => [...prev, { ...input, id: nextId("sev") }]);
  }

  function removeSeveridad(id: string) {
    setSeveridades((prev) => prev.filter((s) => s.id !== id));
  }

  function updateProtocoloMeta(
    protocoloId: string,
    patch: Partial<Pick<ProtocoloInspeccion, "codigoFormato" | "tituloDocumento">>
  ) {
    setProtocolos((prev) =>
      prev.map((p) => (p.id === protocoloId ? { ...p, ...patch } : p))
    );
  }

  function updateEmpresa(patch: Partial<Empresa>) {
    setEmpresa((prev) => ({ ...prev, ...patch }));
  }

  function updateProyectoPdfConfig(proyectoId: string, patch: Partial<ProyectoPdfConfig>) {
    setProyectoPdfConfig((prev) => ({
      ...prev,
      [proyectoId]: { ...prev[proyectoId], ...patch },
    }));
  }

  function addEstructura(input: NuevaEstructuraInput) {
    const nueva: ConfigEstructura = {
      id: nextId("est"),
      proyectoId: input.proyectoId,
      labelUbicacion: input.labelUbicacion,
      labelUnidadControl: input.labelUnidadControl,
    };
    setEstructurasConfig((prev) => [...prev, nueva]);
    return nueva;
  }

  function updateEstructura(estructuraId: string, patch: Partial<Pick<ConfigEstructura, "labelUbicacion" | "labelUnidadControl">>) {
    setEstructurasConfig((prev) =>
      prev.map((e) => (e.id === estructuraId ? { ...e, ...patch } : e))
    );
  }

  function removeEstructura(estructuraId: string) {
    setEstructurasConfig((prev) => prev.filter((e) => e.id !== estructuraId));
    setUnidadesPlanificadas((prev) => prev.filter((u) => u.estructuraId !== estructuraId));
  }

  function addUnidadPlanificada(input: NuevaUnidadPlanificadaInput) {
    const nueva: UnidadPlanificada = {
      id: nextId("unplani"),
      estructuraId: input.estructuraId,
      ubicacion: input.ubicacion,
      unidadControl: input.unidadControl,
      estado: "pendiente",
    };
    setUnidadesPlanificadas((prev) => [...prev, nueva]);
    return nueva;
  }

  function updateUnidadPlanificada(id: string, patch: Partial<Pick<UnidadPlanificada, "ubicacion" | "unidadControl" | "estado">>) {
    setUnidadesPlanificadas((prev) =>
      prev.map((u) => (u.id === id ? { ...u, ...patch } : u))
    );
  }

  function removeUnidadPlanificada(id: string) {
    setUnidadesPlanificadas((prev) => prev.filter((u) => u.id !== id));
  }

  function liberarUnidadPlanificada(unidadId: string, inspeccionId: string) {
    setUnidadesPlanificadas((prev) =>
      prev.map((u) =>
        u.id === unidadId ? { ...u, estado: "liberada", inspeccionOriginId: inspeccionId } : u
      )
    );
  }

  function obtenerRolesDeRevision(proyectoId: string): string[] {
    const config = configuracionesRolesRevision.find((c) => c.proyectoId === proyectoId);
    return config?.rolesRevision ?? [];
  }

  function obtenerConfiguracionRoles(proyectoId: string): ConfiguracionRolesRevision | undefined {
    return configuracionesRolesRevision.find((c) => c.proyectoId === proyectoId);
  }

  const value = useMemo<AppDataContextValue>(
    () => ({
      inspecciones,
      addInspeccion,
      marcarCriterioSolucionado,
      marcarInspeccionSolucionada,
      actualizarItemCriterio,
      actualizarGeneral,
      actualizarValorMatriz,
      finalizarInspeccion,
      agregarRegistroRevision,
      obtenerRolesDeRevision,
      obtenerConfiguracionRoles,
      noConformidades,
      addNoConformidad,
      avanzarEstadoNC,
      usuarios,
      addUsuario,
      toggleEstadoUsuario,
      etapasConstructivas,
      addEtapa,
      deleteEtapa,
      updateEtapa,
      protocolos,
      addProtocolo,
      removeProtocolo,
      addCriterio,
      removeCriterio,
      addColumnaMatriz,
      removeColumnaMatriz,
      addFilaMatriz,
      removeFilaMatriz,
      updateProtocoloMeta,
      severidades,
      addSeveridad,
      removeSeveridad,
      empresa,
      updateEmpresa,
      proyectoPdfConfig,
      updateProyectoPdfConfig,
      estructurasConfig,
      addEstructura,
      updateEstructura,
      removeEstructura,
      unidadesPlanificadas,
      addUnidadPlanificada,
      updateUnidadPlanificada,
      removeUnidadPlanificada,
      liberarUnidadPlanificada,
      proyectos,
    }),
    [inspecciones, noConformidades, usuarios, etapasConstructivas, protocolos, severidades, empresa, proyectoPdfConfig, estructurasConfig, unidadesPlanificadas, proyectos, configuracionesRolesRevision]
  );

  return <AppDataContext.Provider value={value}>{children}</AppDataContext.Provider>;
}

export function useAppData() {
  const ctx = useContext(AppDataContext);
  if (!ctx) throw new Error("useAppData debe usarse dentro de AppDataProvider");
  return ctx;
}
