import type { ProtocoloInspeccion } from "./types";

let n = 0;
const id = () => `crit-${++n}`;

export const protocolosSeed: ProtocoloInspeccion[] = [
  // ETAPA 1: ESTRUCTURAS
  {
    id: "proto-concreto",
    etapaId: "etapa-1",
    nombre: "Concreto",
    tipo: "checklist",
    columnas: [],
    filas: [],
    criterios: [
      { id: id(), texto: "Ensayo de slump dentro de rango especificado" },
      { id: id(), texto: "Probetas tomadas y rotuladas" },
      { id: id(), texto: "Encofrado verificado y aprobado previamente" },
      { id: id(), texto: "Acero de refuerzo según plano estructural" },
      { id: id(), texto: "Curado programado y comunicado" },
    ],
  },
  {
    id: "proto-encofrado",
    etapaId: "etapa-1",
    nombre: "Encofrado",
    tipo: "checklist",
    columnas: [],
    filas: [],
    criterios: [
      { id: id(), texto: "Verticalidad y alineamiento (tolerancia ±5mm)" },
      { id: id(), texto: "Limpieza interior del encofrado" },
      { id: id(), texto: "Aplicación de desmoldante" },
      { id: id(), texto: "Arriostres y apuntalamiento adecuados" },
    ],
  },
  {
    id: "proto-acero",
    etapaId: "etapa-1",
    nombre: "Acero",
    tipo: "checklist",
    columnas: [],
    filas: [],
    criterios: [
      { id: id(), texto: "Diámetro y cantidad de varillas según plano" },
      { id: id(), texto: "Recubrimiento mínimo respetado" },
      { id: id(), texto: "Empalmes y longitud de anclaje conformes" },
      { id: id(), texto: "Amarres y separadores colocados" },
    ],
  },
  {
    id: "proto-impermeabilizacion",
    etapaId: "etapa-1",
    nombre: "Impermeabilización",
    tipo: "checklist",
    columnas: [],
    filas: [],
    criterios: [
      { id: id(), texto: "Superficie limpia y seca antes de aplicación" },
      { id: id(), texto: "Espesor de membrana según especificación" },
      { id: id(), texto: "Traslapes y sellado en juntas" },
      { id: id(), texto: "Prueba de inundación sin filtraciones" },
    ],
  },
  // ETAPA 2: ACABADOS
  {
    id: "proto-albanileria",
    etapaId: "etapa-2",
    nombre: "Albañilería",
    tipo: "checklist",
    columnas: [],
    filas: [],
    criterios: [
      { id: id(), texto: "Verticalidad y aplomo de muros" },
      { id: id(), texto: "Espesor de juntas de asentado uniforme" },
      { id: id(), texto: "Escantillón y control de hiladas" },
      { id: id(), texto: "Amarre con elementos estructurales" },
    ],
  },
  // ETAPA 3: INSTALACIONES
  {
    id: "proto-instalaciones",
    etapaId: "etapa-3",
    nombre: "Instalaciones",
    tipo: "checklist",
    columnas: [],
    filas: [],
    criterios: [
      { id: id(), texto: "Identificación y rotulado de circuitos/tuberías" },
      { id: id(), texto: "Puesta a tierra medida y conforme" },
      { id: id(), texto: "Prueba de continuidad / presión" },
      { id: id(), texto: "Fijación y soportería según norma" },
    ],
  },
  {
    id: "proto-niveles",
    etapaId: "etapa-3",
    nombre: "Control de Niveles Topográficos",
    tipo: "matriz",
    criterios: [],
    columnas: [
      { id: id(), texto: "Punto 1" },
      { id: id(), texto: "Punto 2" },
      { id: id(), texto: "Punto 3" },
    ],
    filas: [
      { id: id(), texto: "Cota de diseño (m)" },
      { id: id(), texto: "Cota real medida (m)" },
      { id: id(), texto: "Diferencia (mm)" },
    ],
  },
];
