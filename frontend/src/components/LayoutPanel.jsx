import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import ThemeToggle from "./ThemeToggle.jsx";

export default function LayoutPanel({ titulo, children }) {
  const { usuario, logout } = useAuth();

  return (
    <div style={{ minHeight: "100vh" }}>
      <header
        style={{
          borderBottom: "1px solid var(--borde)",
          background: "var(--fondo-sutil)",
        }}
      >
        <div
          className="contenedor"
          style={{ display: "flex", justifyContent: "space-between", alignItems: "center", height: 64 }}
        >
          <div>
            <Link to="/" style={{ textDecoration: "none", color: "var(--ascua-500)" }} className="display">
              LOS MEJÍA
            </Link>
            <span style={{ marginLeft: 12, fontSize: "0.85rem", color: "var(--texto-tenue)" }}>{titulo}</span>
          </div>
          <div style={{ display: "flex", gap: 16, alignItems: "center", fontSize: "0.88rem" }}>
            <span style={{ color: "var(--texto-tenue)" }}>{usuario?.nombre}</span>
            <ThemeToggle />
            <button onClick={logout} style={{ background: "none", border: "1px solid var(--borde)", borderRadius: "var(--radius-sm)", padding: "6px 12px", color: "var(--texto)" }}>
              Salir
            </button>
          </div>
        </div>
      </header>
      <div className="contenedor" style={{ padding: "32px 24px" }}>
        {children}
      </div>
    </div>
  );
}
