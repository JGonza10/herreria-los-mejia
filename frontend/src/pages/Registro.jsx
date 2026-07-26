import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";
import { tarjetaEstilo, etiquetaEstilo, inputEstilo } from "./Login.jsx";

export default function Registro() {
  const { registro } = useAuth();
  const navegar = useNavigate();
  const [form, setForm] = useState({ nombre: "", email: "", telefono: "", password: "" });
  const [error, setError] = useState(null);
  const [enviando, setEnviando] = useState(false);

  const actualizar = (campo) => (e) => setForm({ ...form, [campo]: e.target.value });

  const enviar = async (e) => {
    e.preventDefault();
    setEnviando(true);
    setError(null);
    try {
      await registro(form);
      // Igual que en login: siempre a la portada.
      navegar("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div style={{ minHeight: "70vh", display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}>
      <form onSubmit={enviar} style={tarjetaEstilo}>
        <h1 className="display" style={{ fontSize: "1.8rem", marginBottom: 6 }}>Crear cuenta</h1>
        <p style={{ color: "var(--texto-tenue)", fontSize: "0.9rem", marginBottom: 24 }}>
          Regístrate para cotizar en línea y dar seguimiento a tus proyectos.
        </p>

        <label style={etiquetaEstilo}>Nombre completo</label>
        <input required value={form.nombre} onChange={actualizar("nombre")} style={inputEstilo} />

        <label style={{ ...etiquetaEstilo, marginTop: 14 }}>Email</label>
        <input type="email" required value={form.email} onChange={actualizar("email")} style={inputEstilo} />

        <label style={{ ...etiquetaEstilo, marginTop: 14 }}>Teléfono</label>
        <input value={form.telefono} onChange={actualizar("telefono")} style={inputEstilo} />

        <label style={{ ...etiquetaEstilo, marginTop: 14 }}>Contraseña</label>
        <input type="password" required minLength={6} value={form.password} onChange={actualizar("password")} style={inputEstilo} />

        {error && <p style={{ color: "var(--ascua-400)", fontSize: "0.88rem", marginTop: 14 }}>{error}</p>}

        <button type="submit" className="boton boton-ascua" disabled={enviando} style={{ marginTop: 22, justifyContent: "center", width: "100%" }}>
          {enviando ? "Creando cuenta…" : "Crear cuenta"}
        </button>

        <p style={{ marginTop: 18, fontSize: "0.88rem", color: "var(--texto-tenue)" }}>
          ¿Ya tienes cuenta?{" "}
          <Link to="/login" style={{ color: "var(--ascua-400)" }}>Inicia sesión</Link>
        </p>
      </form>
    </div>
  );
}
