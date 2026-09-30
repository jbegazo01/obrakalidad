// Memoria simple en localStorage: lo que el usuario ve como "que la app recuerde mis
// inspecciones" es, técnicamente, esto — el propio navegador guardando los datos en el disco
// de esta computadora. No hay servidor ni base de datos detrás; sigue siendo un prototipo,
// pero ahora sobrevive a recargar la página o cerrar y volver a abrir el navegador.
const PREFIJO = "obracalidad:";

export function cargar<T>(clave: string, valorPorDefecto: T): T {
  if (typeof window === "undefined") return valorPorDefecto;
  try {
    const raw = localStorage.getItem(PREFIJO + clave);
    if (!raw) return valorPorDefecto;
    return JSON.parse(raw) as T;
  } catch {
    return valorPorDefecto;
  }
}

export function guardar<T>(clave: string, valor: T) {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(PREFIJO + clave, JSON.stringify(valor));
  } catch {
    // Cuota de localStorage excedida (muchas fotos en alta resolución) o almacenamiento
    // no disponible (modo privado, etc.). Los datos siguen funcionando en memoria para
    // esta sesión, solo no persisten — no es crítico para un prototipo.
  }
}
