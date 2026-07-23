import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import ThemeToggle from "./ThemeToggle.jsx";

const RUTA_PANEL = {
  administrador: "/admin",
  trabajador: "/trabajador",
  cliente: "/cliente",
};

export default function Header() {
  const { usuario, logout } = useAuth();

  return (
    <header style={{ position: "sticky", top: 0, zIndex: 40 }}>
      {/* Barra superior de contacto */}
      <div
        style={{
          background: "var(--fondo-sutil)",
          borderBottom: "1px solid var(--borde)",
          fontSize: "0.8rem",
          color: "var(--texto-tenue)",
        }}
      >
        <div
          className="contenedor"
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            height: 36,
            flexWrap: "wrap",
            gap: 8,
          }}
        >
          <div style={{ display: "flex", gap: 18 }}>
            <span>📞 (000) 000-0000</span>
            <span className="ocultar-movil">✉ contacto@losmejia.com</span>
          </div>
          <div style={{ display: "flex", gap: 14, alignItems: "center" }}>
            {usuario ? (
              <>
                <Link to={RUTA_PANEL[usuario.rol] || "/"} style={{ textDecoration: "none" }}>
                  Mi panel ({usuario.nombre.split(" ")[0]})
                </Link>
                <button
                  onClick={logout}
                  style={{ background: "none", border: "none", color: "inherit", cursor: "pointer", fontSize: "0.8rem" }}
                >
                  Salir
                </button>
              </>
            ) : (
              <>
                <Link to="/login" style={{ textDecoration: "none" }}>Iniciar sesión</Link>
                <Link to="/registro" style={{ textDecoration: "none" }}>Crear cuenta</Link>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Navegación principal */}
      <div
        style={{
          backdropFilter: "blur(6px)",
          borderBottom: "1px solid var(--borde)",
          background: "var(--fondo)",
        }}
      >
        <div
          className="contenedor"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            height: 76,
          }}
        >
          <Link to="/" style={{ textDecoration: "none" }}>
            <span className="display" style={{ fontSize: "1.6rem", letterSpacing: "0.04em", color: "var(--ascua-500)" }}>
              LOS MEJÍA
            </span>
            <span
              style={{
                display: "block",
                fontSize: "0.62rem",
                color: "var(--texto-tenue)",
                fontFamily: "var(--font-mono)",
                textTransform: "uppercase",
                letterSpacing: "0.15em",
                marginTop: -2,
              }}
            >
              Hierro · Aluminio · Vidrio
            </span>
          </Link>
          <nav style={{ display: "flex", gap: 26, fontSize: "0.92rem", alignItems: "center" }}>
            <a href="/#catalogo" style={{ textDecoration: "none" }}>Catálogo</a>
            <a href="/#cotizador" className="ocultar-movil" style={{ textDecoration: "none" }}>Cotizador</a>
            <a href="/#contacto" className="ocultar-movil" style={{ textDecoration: "none" }}>Contacto</a>
            <ThemeToggle />
            <a href="/#cotizador" className="boton boton-ascua">Cotizar ahora</a>
          </nav>
        </div>
      </div>
    </header>
  );
}
