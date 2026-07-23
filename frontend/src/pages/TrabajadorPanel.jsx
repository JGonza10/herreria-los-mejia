import { useEffect, useState } from "react";
import LayoutPanel from "../components/LayoutPanel.jsx";
import { api } from "../api.js";

const ETIQUETA_ESTADO = {
  pendiente: "Pendiente",
  en_proceso: "En proceso",
  terminado: "Terminado",
  entregado: "Entregado",
  cancelado: "Cancelado",
};

export default function TrabajadorPanel() {
  const [asignados, setAsignados] = useState([]);
  const [pendientes, setPendientes] = useState([]);

  const cargar = () => {
    api.get("/api/trabajador/proyectos/asignados").then(setAsignados).catch(() => {});
    api.get("/api/trabajador/proyectos/pendientes").then(setPendientes).catch(() => {});
  };

  useEffect(() => { cargar(); }, []);

  const actualizar = async (id, cambios) => {
    await api.put(`/api/trabajador/proyectos/${id}/avance`, cambios);
    cargar();
  };

  return (
    <LayoutPanel titulo="Panel de trabajador">
      <h2 style={{ fontSize: "1.6rem", marginBottom: 18 }}>Mis proyectos asignados ({asignados.length})</h2>
      <div style={{ display: "grid", gap: 14, marginBottom: 44 }}>
        {asignados.map((p) => (
          <div key={p.id} style={{ border: "1px solid var(--borde)", borderRadius: "var(--radius-md)", padding: 18, background: "var(--fondo-elevado)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 10 }}>
              <div>
                <p style={{ fontWeight: 600 }}>{p.titulo}</p>
                <p style={{ fontSize: "0.85rem", color: "var(--texto-tenue)" }}>Cliente: {p.cliente_nombre} · {p.material}</p>
              </div>
              <span style={{ fontSize: "0.85rem", color: "var(--ascua-400)", fontWeight: 600 }}>{ETIQUETA_ESTADO[p.estado]}</span>
            </div>

            <div style={{ display: "flex", gap: 14, marginTop: 16, alignItems: "center", flexWrap: "wrap" }}>
              <label style={{ fontSize: "0.82rem", color: "var(--texto-tenue)" }}>
                Estado:
                <select
                  value={p.estado}
                  onChange={(e) => actualizar(p.id, { estado: e.target.value })}
                  style={selectEstilo}
                  disabled={p.estado === "entregado" || p.estado === "cancelado"}
                >
                  <option value="pendiente">Pendiente</option>
                  <option value="en_proceso">En proceso</option>
                  <option value="terminado">Terminado</option>
                </select>
              </label>
              <label style={{ fontSize: "0.82rem", color: "var(--texto-tenue)", display: "flex", alignItems: "center", gap: 6 }}>
                Avance:
                <input
                  type="number" min="0" max="100"
                  value={p.avance_porcentaje}
                  onChange={(e) => actualizar(p.id, { avance_porcentaje: Number(e.target.value) })}
                  style={{ ...selectEstilo, width: 64 }}
                />
                %
              </label>
            </div>

            <div style={{ marginTop: 10, height: 6, background: "var(--fondo-sutil)", borderRadius: 999, overflow: "hidden" }}>
              <div style={{ width: `${p.avance_porcentaje}%`, height: "100%", background: "var(--ascua-500)" }} />
            </div>
          </div>
        ))}
        {asignados.length === 0 && <p style={{ color: "var(--texto-tenue)" }}>No tienes proyectos asignados todavía.</p>}
      </div>

      <h2 style={{ fontSize: "1.6rem", marginBottom: 6 }}>Cola general pendiente ({pendientes.length})</h2>
      <p style={{ fontSize: "0.85rem", color: "var(--texto-tenue)", marginBottom: 18 }}>
        Solo consulta — el administrador es quien asigna estos proyectos.
      </p>
      <div style={{ display: "grid", gap: 10 }}>
        {pendientes.map((p) => (
          <div key={p.id} style={{ border: "1px solid var(--borde)", borderRadius: "var(--radius-sm)", padding: "12px 16px", background: "var(--fondo-elevado)", display: "flex", justifyContent: "space-between" }}>
            <span>{p.titulo}</span>
            <span style={{ color: "var(--texto-tenue)", fontSize: "0.85rem" }}>{p.material}</span>
          </div>
        ))}
        {pendientes.length === 0 && <p style={{ color: "var(--texto-tenue)" }}>No hay proyectos pendientes sin asignar.</p>}
      </div>
    </LayoutPanel>
  );
}

const selectEstilo = {
  marginLeft: 6,
  padding: "6px 8px",
  borderRadius: "var(--radius-sm)",
  border: "1px solid var(--borde)",
  background: "var(--fondo)",
  color: "var(--texto)",
  fontSize: "0.82rem",
};
