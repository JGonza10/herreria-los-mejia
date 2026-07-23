import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function RutaProtegida({ rolesPermitidos, children }) {
  const { usuario, cargando } = useAuth();

  if (cargando) {
    return <p style={{ padding: 40, color: "var(--texto-tenue)" }}>Cargando…</p>;
  }
  if (!usuario) {
    return <Navigate to="/login" replace />;
  }
  if (rolesPermitidos && !rolesPermitidos.includes(usuario.rol)) {
    return <Navigate to="/" replace />;
  }
  return children;
}
