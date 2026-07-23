import { useEffect, useState } from "react";
import { api } from "../../api.js";

const VACIO = { nombre: "", email: "", telefono: "", password: "", rol: "trabajador" };

export default function AdminUsuarios() {
  const [usuarios, setUsuarios] = useState([]);
  const [form, setForm] = useState(VACIO);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState(null);

  const cargar = () => api.get("/api/admin/usuarios").then(setUsuarios).catch(() => {});

  useEffect(() => { cargar(); }, []);

  const crear = async (e) => {
    e.preventDefault();
    setGuardando(true);
    setError(null);
    try {
      await api.post("/api/admin/usuarios", form);
      setForm(VACIO);
      cargar();
    } catch (err) {
      setError(err.message);
    } finally {
      setGuardando(false);
    }
  };

  return (
    <div>
      <h2 style={{ fontSize: "1.6rem", marginBottom: 18 }}>Nueva cuenta de equipo</h2>
      <form onSubmit={crear} style={{ display: "grid", gap: 14, maxWidth: 420, marginBottom: 40 }}>
        <input placeholder="Nombre" required value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} style={inputEstilo} />
        <input type="email" placeholder="Email" required value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} style={inputEstilo} />
        <input placeholder="Teléfono" value={form.telefono} onChange={(e) => setForm({ ...form, telefono: e.target.value })} style={inputEstilo} />
        <input type="password" placeholder="Contraseña" required minLength={6} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} style={inputEstilo} />
        <select value={form.rol} onChange={(e) => setForm({ ...form, rol: e.target.value })} style={inputEstilo}>
          <option value="trabajador">Trabajador</option>
          <option value="administrador">Administrador</option>
        </select>
        {error && <p style={{ color: "var(--ascua-400)" }}>{error}</p>}
        <button type="submit" className="boton boton-ascua" disabled={guardando}>
          {guardando ? "Creando…" : "Crear cuenta"}
        </button>
      </form>

      <h2 style={{ fontSize: "1.6rem", marginBottom: 18 }}>Equipo ({usuarios.length})</h2>
      <div style={{ display: "grid", gap: 10 }}>
        {usuarios.map((u) => (
          <div key={u.id} style={{ display: "flex", justifyContent: "space-between", border: "1px solid var(--borde)", borderRadius: "var(--radius-sm)", padding: "12px 16px", background: "var(--fondo-elevado)" }}>
            <div>
              <p style={{ fontWeight: 600 }}>{u.nombre}</p>
              <p style={{ fontSize: "0.82rem", color: "var(--texto-tenue)" }}>{u.email}</p>
            </div>
            <span style={{ fontSize: "0.8rem", color: "var(--texto-tenue)", textTransform: "capitalize" }}>{u.rol}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

const inputEstilo = {
  width: "100%",
  padding: "10px 12px",
  borderRadius: "var(--radius-sm)",
  border: "1px solid var(--borde)",
  background: "var(--fondo)",
  color: "var(--texto)",
  fontSize: "0.95rem",
};
