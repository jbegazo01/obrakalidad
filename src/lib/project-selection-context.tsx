"use client";

import { createContext, useContext, useEffect, useState } from "react";

type ProjectSelectionContextValue = {
  proyectoSeleccionado: string;
  setProyectoSeleccionado: (id: string) => void;
};

const ProjectSelectionContext = createContext<ProjectSelectionContextValue | undefined>(
  undefined
);

export function ProjectSelectionProvider({ children }: { children: React.ReactNode }) {
  const [proyectoSeleccionado, setProyectoSeleccionadoState] = useState<string>("");
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const guardado = localStorage.getItem("obracalidad:proyectoSeleccionado");
    if (guardado) {
      setProyectoSeleccionadoState(guardado);
    }
    setIsHydrated(true);
  }, []);

  const setProyectoSeleccionado = (id: string) => {
    setProyectoSeleccionadoState(id);
    if (typeof window !== "undefined") {
      localStorage.setItem("obracalidad:proyectoSeleccionado", id);
    }
  };

  return (
    <ProjectSelectionContext.Provider
      value={{
        proyectoSeleccionado,
        setProyectoSeleccionado,
      }}
    >
      {children}
    </ProjectSelectionContext.Provider>
  );
}

export function useProjectSelection() {
  const context = useContext(ProjectSelectionContext);
  if (context === undefined) {
    throw new Error("useProjectSelection must be used within ProjectSelectionProvider");
  }
  return context;
}
