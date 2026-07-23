import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

const RUTA_PANEL = {
  administrador: "/admin",
  trabajador: "/trabajador",
  cliente: "/cliente",
};

export default function Login() {
  const { login } = useAuth();
  const navegar = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [enviando, setEnviando] = useState(false);

  const enviar = async (e) => {
    e.preventDefault();
    setEnviando(true);
    setError(null);
    try {
      const usuario = await login(email, password);
      navegar(RUTA_PANEL[usuario.rol] || "/");
    } catch (err) {
      setError(err.message);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div style={{ minHeight: "70vh", display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}>
      <form onSubmit={enviar} style={tarjetaEstilo}>
        <h1 className="display" style={{ fontSize: "1.8rem", marginBottom: 6 }}>Iniciar sesión</h1>
        <p style={{ color: "var(--texto-tenue)", fontSize: "0.9rem", marginBottom: 24 }}>
          Accede a tu panel de Los Mejía.
        </p>

        <label style={etiquetaEstilo}>Email</label>
        <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} style={inputEstilo} />

        <label style={{ ...etiquetaEstilo, marginTop: 14 }}>Contraseña</label>
        <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} style={inputEstilo} />

        {error && <p style={{ color: "var(--ascua-400)", fontSize: "0.88rem", marginTop: 14 }}>{error}</p>}

        <button type="submit" className="boton boton-ascua" disabled={enviando} style={{ marginTop: 22, justifyContent: "center", width: "100%" }}>
          {enviando ? "Entrando…" : "Entrar"}
        </button>

        <p style={{ marginTop: 18, fontSize: "0.88rem", color: "var(--texto-tenue)" }}>
          ¿Eres cliente nuevo?{" "}
          <Link to="/registro" style={{ color: "var(--ascua-400)" }}>Crea tu cuenta</Link>
        </p>
      </form>
    </div>
  );
}

const tarjetaEstilo = {
  width: "100%",
  maxWidth: 380,
  background: "var(--fondo-elevado)",
  border: "1px solid var(--borde)",
  borderRadius: "var(--radius-md)",
  padding: 32,
};

const etiquetaEstilo = {
  display: "block",
  fontSize: "0.78rem",
  color: "var(--texto-tenue)",
  textTransform: "uppercase",
  letterSpacing: "0.06em",
  fontFamily: "var(--font-mono)",
  marginBottom: 6,
};

const inputEstilo = {
  width: "100%",
  padding: "10px 12px",
  borderRadius: "var(--radius-sm)",
  border: "1px solid var(--borde)",
  background: "var(--fondo)",
  color: "var(--texto)",
  fontSize: "0.95rem",
};

export { tarjetaEstilo, etiquetaEstilo, inputEstilo };
