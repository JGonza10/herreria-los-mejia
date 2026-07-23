import { useEffect, useState } from "react";
import { api } from "../../api.js";

const ESTADOS = ["pendiente", "en_proceso", "terminado", "entregado", "cancelado"];
const ETIQUETA_ESTADO = {
  pendiente: "Pendiente",
  en_proceso: "En proceso",
  terminado: "Terminado",
  entregado: "Entregado",
  cancelado: "Cancelado",
};
const COLOR_ESTADO = {
  pendiente: "var(--texto-tenue)",
  en_proceso: "var(--ascua-400)",
  terminado: "var(--vidrio-400)",
  entregado: "#4caf6d",
  cancelado: "#b23b3b",
};

export default function AdminPedidos() {
  const [proyectos, setProyectos] = useState([]);
  const [trabajadores, setTrabajadores] = useState([]);
  const [filtro, setFiltro] = useState("");

  const cargar = () => api.get("/api/admin/proyectos").then(setProyectos).catch(() => {});

  useEffect(() => {
    cargar();
    api.get("/api/admin/usuarios?rol=trabajador").then(setTrabajadores).catch(() => {});
  }, []);

  const actualizar = async (id, cambios) => {
    await api.put(`/api/admin/proyectos/${id}`, cambios);
    cargar();
  };

  const visibles = filtro ? proyectos.filter((p) => p.estado === filtro) : proyectos;

  return (
    <div>
      <h2 style={{ fontSize: "1.6rem", marginBottom: 6 }}>Pedidos ({proyectos.length})</h2>
      <p style={{ color: "var(--texto-tenue)", fontSize: "0.88rem", marginBottom: 18 }}>
        Se crean automáticamente al aprobar una cotización.
      </p>

      <div style={{ display: "flex", gap: 8, marginBottom: 20, flexWrap: "wrap" }}>
        <button onClick={() => setFiltro("")} style={tabEstilo(filtro === "")}>Todos</button>
        {ESTADOS.map((e) => (
          <button key={e} onClick={() => setFiltro(e)} style={tabEstilo(filtro === e)}>{ETIQUETA_ESTADO[e]}</button>
        ))}
      </div>

      <div style={{ display: "grid", gap: 14 }}>
        {visibles.map((p) => (
          <div key={p.id} style={{ border: "1px solid var(--borde)", borderRadius: "var(--radius-md)", padding: 18, background: "var(--fondo-elevado)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 10 }}>
              <div>
                <p style={{ fontWeight: 600 }}>{p.titulo}</p>
                <p style={{ fontSize: "0.85rem", color: "var(--texto-tenue)" }}>
                  Cliente: {p.cliente_nombre} · {p.material} · ${p.precio_estimado.toLocaleString("es-MX")}
                </p>
              </div>
              <span style={{ color: COLOR_ESTADO[p.estado], fontWeight: 600, fontSize: "0.85rem" }}>
                {ETIQUETA_ESTADO[p.estado]}
              </span>
            </div>

            <div style={{ display: "flex", gap: 14, marginTop: 16, flexWrap: "wrap", alignItems: "center" }}>
              <label style={{ fontSize: "0.82rem", color: "var(--texto-tenue)" }}>
                Trabajador:
                <select
                  value={p.trabajador_id || ""}
                  onChange={(e) => actualizar(p.id, { trabajador_id: e.target.value ? Number(e.target.value) : null })}
                  style={selectEstilo}
                >
                  <option value="">Sin asignar</option>
                  {trabajadores.map((t) => (
                    <option key={t.id} value={t.id}>{t.nombre}</option>
                  ))}
                </select>
              </label>

              <label style={{ fontSize: "0.82rem", color: "var(--texto-tenue)" }}>
                Estado:
                <select value={p.estado} onChange={(e) => actualizar(p.id, { estado: e.target.value })} style={selectEstilo}>
                  {ESTADOS.map((e) => (
                    <option key={e} value={e}>{ETIQUETA_ESTADO[e]}</option>
                  ))}
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
        {visibles.length === 0 && <p style={{ color: "var(--texto-tenue)" }}>No hay pedidos en este estado.</p>}
      </div>
    </div>
  );
}

function tabEstilo(activo) {
  return {
    padding: "7px 14px",
    borderRadius: 999,
    border: `1px solid ${activo ? "var(--ascua-500)" : "var(--borde)"}`,
    background: activo ? "var(--ascua-500)" : "transparent",
    color: activo ? "#fff" : "var(--texto)",
    fontSize: "0.82rem",
    fontWeight: 600,
  };
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
