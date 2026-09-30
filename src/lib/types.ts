export type EstadoNC = "Abierta" | "En proceso" | "Cerrada";
export type ResultadoInspeccion = "Nuevo" | "En Proceso" | "Aprobado" | "Falla";

export type EstadoRevisionInspeccion =
  | "Nueva"
  | "En Revisión"
  | "Revisiones Completadas"
  | "Finalizada";

export type RegistroRevision = {
  id: string;
  rol: string;
  nombreRevisor: string;
  comentario?: string;
  fechaHora: string;
};

export type ConfiguracionRolesRevision = {
  id: string;
  proyectoId: string;
  rolesRevision: string[];
  requiereTodasLasRevisiones: boolean;
};

export type Proyecto = {
  id: string;
  nombre: string;
  ubicacion: string;
  cliente: string;
  residente: string;
  estructuraConfigId?: string;
};

// Configuración de estructura: qué nombres/etiquetas se usan para ubicación y unidad de control
export type ConfigEstructura = {
  id: string;
  proyectoId: string;
  labelUbicacion: string;
  labelUnidadControl: string;
};

// Unidades planificadas para controlar cobertura de inspecciones (KPI)
export type UnidadPlanificada = {
  id: string;
  estructuraId: string;
  ubicacion: string;
  unidadControl: string;
  estado: "pendiente" | "liberada";
  inspeccionOriginId?: string;
};

// Datos adicionales del proyecto usados solo para armar el encabezado del PDF/impresión.
// Separados de Proyecto para no tocar los datos operativos ya existentes.
export type ProyectoPdfConfig = {
  nombreOficial?: string;
  cui?: string;
  supervision?: string;
  logoCliente?: Evidencia;
};

export type Empresa = {
  nombre: string;
  logo?: Evidencia;
};

export type RespuestaCriterio = "cumple" | "no_cumple" | "no_aplica";

export type TipoEvidencia = "imagen" | "archivo";

export type Evidencia = {
  id: string;
  nombre: string;
  url: string;
  tipo: TipoEvidencia;
};

export type ChecklistItem = {
  id: string;
  descripcion: string;
  respuesta: RespuestaCriterio | null;
  comentario?: string;
  evidencias: Evidencia[];
  solucionado?: boolean;
  fechaSolucion?: string;
};

export type Participante = {
  id: string;
  nombre: string;
  rol: string;
  firmaUrl: string;
  fechaHora: string;
};

// Estado de trazabilidad de la inspección: si tuvo hallazgos (Observado/Rechazado),
// "Pendiente" hasta que se resuelvan todos los criterios en "no cumple" y se confirme
// explícitamente con el botón de cierre. Las inspecciones "Aprobado" no usan este campo.
export type EstadoInspeccion = "Pendiente" | "Solucionado";

// "checklist" = protocolo de conformidad (cumple/no cumple, con cumplimiento y trazabilidad).
// "matriz" = tabla de datos libre (eje X / eje Y), puramente informativa, sin cumplimiento
// ni resultado — para controles de toma de información (ej. niveles, mediciones, matrices).
export type TipoRegistro = "checklist" | "matriz";

export type EjeItem = {
  id: string;
  texto: string;
};

export type Inspeccion = {
  id: string;
  codigo: string;
  proyectoId: string;
  ubicacion: string;
  unidadControl: string;
  unidadPlanificadaId?: string;
  protocoloId: string;
  tipo: string;
  tipoRegistro: TipoRegistro;
  fecha: string;
  inspector: string;
  resultado: ResultadoInspeccion;
  cumplimiento: number;
  items: ChecklistItem[];
  // Solo cuando tipoRegistro === "matriz": copia de las columnas/filas del protocolo al
  // momento de crear el registro (no cambia si luego se edita la plantilla), y los valores
  // ingresados en cada celda, con clave `${filaId}_${columnaId}`.
  matrizColumnas?: EjeItem[];
  matrizFilas?: EjeItem[];
  matrizValores?: Record<string, string>;
  comentarioGeneral?: string;
  evidenciasGenerales: Evidencia[];
  planoReferencia?: string;
  material?: string;
  participantes: Participante[];
  estado: EstadoInspeccion;
  fechaSolucionInspeccion?: string;
  // Flujo de revisión: estado actual del proceso de revisión
  estadoRevision: EstadoRevisionInspeccion;
  registrosRevision: RegistroRevision[];
  // Mientras no esté finalizada, los criterios (o celdas de la matriz) pueden corregirse
  // (ej. algo dado por conforme que luego resultó con un error). Al finalizar queda
  // archivada y de solo lectura.
  finalizada: boolean;
  fechaFinalizacion?: string;
};

export type NoConformidad = {
  id: string;
  codigo: string;
  proyectoId: string;
  ubicacion: string;
  unidadControl: string;
  descripcion: string;
  severidad: string;
  estado: EstadoNC;
  responsable: string;
  fechaApertura: string;
  fechaLimite: string;
  inspeccionOriginId?: string;
};

export type RolUsuario =
  | "Calidad"
  | "Producción"
  | "Residente"
  | "Supervisor"
  | "Subcontratista"
  | "Visualizador";

export type EstadoUsuario = "Activo" | "Inactivo";

export type Usuario = {
  id: string;
  nombre: string;
  email: string;
  rol: RolUsuario;
  estado: EstadoUsuario;
  fechaCreacion: string;
  proyectoIds: string[];
};

export type CriterioInspeccion = {
  id: string;
  texto: string;
};

export type TipoProtocolo = "checklist" | "matriz";

export type ProtocoloInspeccion = {
  id: string;
  etapaId: string;
  nombre: string;
  tipo: TipoProtocolo;
  criterios: CriterioInspeccion[];
  // Solo relevante cuando tipo === "matriz": encabezados configurables de columnas (eje X)
  // y filas (eje Y) de la tabla libre.
  columnas: EjeItem[];
  filas: EjeItem[];
  codigoFormato?: string;
  tituloDocumento?: string;
};

export type EtapaConstructiva = {
  id: string;
  nombre: string;
  descripcion?: string;
  orden?: number;
};

export type ColorEtiqueta =
  | "red"
  | "amber"
  | "slate"
  | "orange"
  | "violet"
  | "teal"
  | "emerald"
  | "blue";

export type SeveridadConfig = {
  id: string;
  nombre: string;
  color: ColorEtiqueta;
  diasSla: number;
};
