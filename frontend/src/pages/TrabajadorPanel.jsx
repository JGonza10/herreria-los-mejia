import { useEffect, useRef, useState } from "react";
import LayoutPanel from "../components/LayoutPanel.jsx";
import { api } from "../api.js";
import { urlImagen } from "../config.js";

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
  const [expandido, setExpandido] = useState(null);

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
              <button onClick={() => setExpandido(expandido === p.id ? null : p.id)} className="boton boton-borde">
                {expandido === p.id ? "Ocultar" : "Registrar horas / subir foto"}
              </button>
            </div>

            <div style={{ marginTop: 10, height: 6, background: "var(--fondo-sutil)", borderRadius: 999, overflow: "hidden" }}>
              <div style={{ width: `${p.avance_porcentaje}%`, height: "100%", background: "var(--ascua-500)" }} />
            </div>

            {expandido === p.id && <PanelHorasYFotos proyecto={p} onCambio={cargar} />}
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

function PanelHorasYFotos({ proyecto, onCambio }) {
  const [horas, setHoras] = useState("");
  const [notasHoras, setNotasHoras] = useState("");
  const [subiendo, setSubiendo] = useState(false);
  const [error, setError] = useState(null);
  const [mensaje, setMensaje] = useState(null);
  const inputArchivo = useRef(null);

  const registrarHoras = async (e) => {
    e.preventDefault();
    if (!horas) return;
    setError(null);
    try {
      await api.post(`/api/trabajador/proyectos/${proyecto.id}/horas`, { horas: Number(horas), notas: notasHoras || undefined });
      setHoras("");
      setNotasHoras("");
      setMensaje("Horas registradas.");
      onCambio();
    } catch (err) {
      setError(err.message);
    }
  };

  const subirFoto = async (e) => {
    const archivo = e.target.files?.[0];
    if (!archivo) return;
    setSubiendo(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("imagen", archivo);
      await api.postForm(`/api/trabajador/proyectos/${proyecto.id}/fotos`, formData);
      setMensaje("Foto subida.");
      onCambio();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubiendo(false);
      if (inputArchivo.current) inputArchivo.current.value = "";
    }
  };

  return (
    <div style={{ marginTop: 16, borderTop: "1px dashed var(--borde)", paddingTop: 16, display: "grid", gap: 18 }}>
      {error && <p style={{ color: "var(--ascua-400)" }}>{error}</p>}
      {mensaje && <p style={{ color: "#4caf6d", fontSize: "0.85rem" }}>{mensaje}</p>}

      <div>
        <h4 style={{ fontSize: "0.95rem", marginBottom: 8 }}>Registrar horas (total hoy: {proyecto.total_horas ?? 0})</h4>
        <form onSubmit={registrarHoras} style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
          <input type="number" step="0.5" min="0.1" max="24" placeholder="Horas" required value={horas} onChange={(e) => setHoras(e.target.value)} style={{ ...inputChico, width: 80 }} />
          <input placeholder="Notas (opcional)" value={notasHoras} onChange={(e) => setNotasHoras(e.target.value)} style={{ ...inputChico, width: 200 }} />
          <button type="submit" className="boton boton-ascua" style={{ fontSize: "0.82rem", padding: "8px 14px" }}>Registrar</button>
        </form>
      </div>

      <div>
        <h4 style={{ fontSize: "0.95rem", marginBottom: 8 }}>Fotos de avance</h4>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 10 }}>
          {(proyecto.fotos || []).map((foto) => (
            <img key={foto.id} src={urlImagen(foto.url)} alt="avance" style={{ width: 90, height: 90, objectFit: "cover", borderRadius: "var(--radius-sm)", border: "1px solid var(--borde)" }} />
          ))}
        </div>
        <input ref={inputArchivo} type="file" accept="image/png,image/jpeg,image/webp" onChange={subirFoto} disabled={subiendo} />
        {subiendo && <span style={{ fontSize: "0.8rem", color: "var(--texto-tenue)", marginLeft: 8 }}>Subiendo…</span>}
      </div>
    </div>
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

const inputChico = {
  padding: "6px 8px",
  borderRadius: "var(--radius-sm)",
  border: "1px solid var(--borde)",
  background: "var(--fondo)",
  color: "var(--texto)",
  fontSize: "0.82rem",
};
