import { createContext, useContext, useEffect, useState } from "react";
import { API_BASE } from "../config.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null);
  const [cargando, setCargando] = useState(true);

  const cargarUsuario = async () => {
    try {
      const r = await fetch(`${API_BASE}/api/auth/yo`, { credentials: "include" });
      const data = await r.json();
      setUsuario(data.usuario);
    } catch {
      setUsuario(null);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargarUsuario();
  }, []);

  const login = async (email, password) => {
    const r = await fetch(`${API_BASE}/api/auth/login`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || "No se pudo iniciar sesión.");
    setUsuario(data);
    return data;
  };

  const registro = async ({ nombre, email, telefono, password }) => {
    const r = await fetch(`${API_BASE}/api/auth/registro`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nombre, email, telefono, password }),
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || "No se pudo crear la cuenta.");
    setUsuario(data);
    return data;
  };

  const logout = async () => {
    await fetch(`${API_BASE}/api/auth/logout`, { method: "POST", credentials: "include" });
    setUsuario(null);
  };

  return (
    <AuthContext.Provider value={{ usuario, cargando, login, registro, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
