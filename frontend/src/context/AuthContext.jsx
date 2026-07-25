import { createContext, useContext, useEffect, useState } from "react";
import { API_BASE } from "../config.js";

const AuthContext = createContext(null);
const CLAVE_TOKEN = "token";

export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null);
  const [cargando, setCargando] = useState(true);

  const cargarUsuario = async () => {
    const token = localStorage.getItem(CLAVE_TOKEN);
    if (!token) {
      setUsuario(null);
      setCargando(false);
      return;
    }
    try {
      const r = await fetch(`${API_BASE}/api/auth/yo`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await r.json();
      setUsuario(data.usuario);
      if (!data.usuario) localStorage.removeItem(CLAVE_TOKEN);
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
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || "No se pudo iniciar sesión.");
    localStorage.setItem(CLAVE_TOKEN, data.token);
    setUsuario(data);
    return data;
  };

  const registro = async ({ nombre, email, telefono, password }) => {
    const r = await fetch(`${API_BASE}/api/auth/registro`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nombre, email, telefono, password }),
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || "No se pudo crear la cuenta.");
    localStorage.setItem(CLAVE_TOKEN, data.token);
    setUsuario(data);
    return data;
  };

  const logout = async () => {
    localStorage.removeItem(CLAVE_TOKEN);
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
