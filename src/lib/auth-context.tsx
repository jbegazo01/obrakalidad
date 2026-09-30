"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { useAppData } from "./app-data-context";
import type { Usuario } from "./types";

type LoginResult = { ok: true } | { ok: false; error: string };

type AuthContextValue = {
  usuarioActual: Usuario | null;
  login: (email: string, password: string) => LoginResult;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { usuarios } = useAppData();
  const [usuarioActual, setUsuarioActual] = useState<Usuario | null>(null);
  const [hidratado, setHidratado] = useState(false);

  // Cargar sesión desde localStorage al montar
  useEffect(() => {
    if (typeof window !== "undefined") {
      try {
        const stored = localStorage.getItem("obracalidad:sesion");
        if (stored) {
          const usuario = JSON.parse(stored) as Usuario;
          // Verificar que el usuario sigue siendo válido
          const existe = usuarios.find((u) => u.id === usuario.id);
          if (existe) {
            setUsuarioActual(existe);
          }
        }
      } catch {
        // Ignorar errores de parsing
      }
      setHidratado(true);
    }
  }, [usuarios]);

  function login(inputEmail: string, password: string): LoginResult {
    if (!password.trim()) {
      return { ok: false, error: "Ingresa tu contraseña." };
    }
    const usuario = usuarios.find(
      (u) => u.email.toLowerCase() === inputEmail.trim().toLowerCase()
    );
    if (!usuario) {
      return { ok: false, error: "No encontramos una cuenta con ese correo." };
    }
    if (usuario.estado !== "Activo") {
      return { ok: false, error: "Este usuario está inactivo. Contacta a tu administrador." };
    }
    setUsuarioActual(usuario);
    // Guardar sesión en localStorage
    if (typeof window !== "undefined") {
      localStorage.setItem("obracalidad:sesion", JSON.stringify(usuario));
    }
    return { ok: true };
  }

  function logout() {
    setUsuarioActual(null);
    if (typeof window !== "undefined") {
      localStorage.removeItem("obracalidad:sesion");
    }
  }

  return (
    <AuthContext.Provider value={{ usuarioActual, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return ctx;
}
