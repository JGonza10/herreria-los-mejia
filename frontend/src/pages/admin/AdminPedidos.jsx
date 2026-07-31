import { useEffect, useState } from "react";
import { api } from "../../api.js";
import { API_BASE, urlImagen } from "../../config.js";

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
  const [expandido, setExpandido] = useState(null);

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
                  {p.saldo > 0 && <span style={{ color: "var(--ascua-400)" }}> · Saldo: ${p.saldo.toLocaleString("es-MX")}</span>}
                  {p.saldo === 0 && <span style={{ color: "#4caf6d" }}> · Pagado completo</span>}
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

              <button onClick={() => setExpandido(expandido === p.id ? null : p.id)} className="boton boton-borde">
                {expandido === p.id ? "Ocultar detalle" : "Ver detalle"}
              </button>
            </div>

            <div style={{ marginTop: 10, height: 6, background: "var(--fondo-sutil)", borderRadius: 999, overflow: "hidden" }}>
              <div style={{ width: `${p.avance_porcentaje}%`, height: "100%", background: "var(--ascua-500)" }} />
            </div>

            {expandido === p.id && <DetalleProyecto proyecto={p} onCambio={cargar} />}
          </div>
        ))}
        {visibles.length === 0 && <p style={{ color: "var(--texto-tenue)" }}>No hay pedidos en este estado.</p>}
      </div>
    </div>
  );
}

function DetalleProyecto({ proyecto, onCambio }) {
  const [monto, setMonto] = useState("");
  const [metodo, setMetodo] = useState("transferencia");
  const [costoReal, setCostoReal] = useState(proyecto.costo_material_real ?? "");
  const [despieces, setDespieces] = useState({});
  const [error, setError] = useState(null);

  const registrarPago = async (e) => {
    e.preventDefault();
    if (!monto) return;
    setError(null);
    try {
      await api.post(`/api/admin/proyectos/${proyecto.id}/pagos`, { monto: Number(monto), metodo, fecha: new Date().toISOString().slice(0, 10) });
      setMonto("");
      onCambio();
    } catch (err) {
      setError(err.message);
    }
  };

  const guardarCostoReal = async () => {
    if (costoReal === "") return;
    try {
      await api.put(`/api/admin/proyectos/${proyecto.id}`, { costo_material_real: Number(costoReal) });
      onCambio();
    } catch (err) {
      setError(err.message);
    }
  };

  const verDespiece = async (partidaId) => {
    try {
      const r = await api.post(`/api/admin/partidas/${partidaId}/despiece`, { merma_pct_teorica: 7 });
      setDespieces({ ...despieces, [partidaId]: r });
    } catch (err) {
      setDespieces({ ...despieces, [partidaId]: { error: err.message } });
    }
  };

  const descargarOrden = (partidaId) => {
    const token = localStorage.getItem("token");
    fetch(`${API_BASE}/api/admin/partidas/${partidaId}/orden-trabajo.pdf`, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
      .then((r) => r.blob())
      .then((blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `orden-trabajo-${proyecto.id}-${partidaId}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
      });
  };

  const partidas = proyecto.partidas || [];

  return (
    <div style={{ marginTop: 16, borderTop: "1px dashed var(--borde)", paddingTop: 16, display: "grid", gap: 20 }}>
      {error && <p style={{ color: "var(--ascua-400)" }}>{error}</p>}

      <div>
        <h4 style={estiloSub}>Partidas</h4>
        {partidas.length === 0 && <p style={{ fontSize: "0.82rem", color: "var(--texto-tenue)" }}>Sin partidas registradas (cotización de una sola pieza, sin desglose).</p>}
        <div style={{ display: "grid", gap: 8 }}>
          {partidas.map((partida) => (
            <div key={partida.id} style={{ border: "1px solid var(--borde)", borderRadius: "var(--radius-sm)", padding: 12, fontSize: "0.85rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
                <span>{partida.descripcion} — {partida.cantidad} {partida.desglose?.unidad === "ml" ? "ml" : "m²"}</span>
                <span>${partida.importe.toLocaleString("es-MX")}</span>
              </div>
              <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                <button onClick={() => verDespiece(partida.id)} className="boton boton-borde" style={{ fontSize: "0.78rem", padding: "6px 12px" }}>Ver lista de corte</button>
                <button onClick={() => descargarOrden(partida.id)} className="boton boton-borde" style={{ fontSize: "0.78rem", padding: "6px 12px" }}>Descargar orden de trabajo (PDF)</button>
              </div>
              {despieces[partida.id] && !despieces[partida.id].error && (
                <div style={{ marginTop: 8, fontSize: "0.78rem", color: "var(--texto-tenue)" }}>
                  {despieces[partida.id].num_barras} barra(s) de 6 m · merma real {despieces[partida.id].merma_pct_real}%
                  (teórica {despieces[partida.id].merma_pct_teorica}%)
                </div>
              )}
              {despieces[partida.id]?.error && (
                <p style={{ marginTop: 8, fontSize: "0.78rem", color: "var(--ascua-400)" }}>{despieces[partida.id].error}</p>
              )}
            </div>
          ))}
        </div>
      </div>

      <div>
        <h4 style={estiloSub}>Pagos — saldo ${proyecto.saldo?.toLocaleString("es-MX")}</h4>
        <div style={{ display: "grid", gap: 6, marginBottom: 10 }}>
          {(proyecto.pagos || []).map((pago) => (
            <div key={pago.id} style={{ display: "flex", justifyContent: "space-between", fontSize: "0.82rem" }}>
              <span>{pago.fecha} · {pago.metodo || "sin especificar"}</span>
              <span>${pago.monto.toLocaleString("es-MX")}</span>
            </div>
          ))}
          {(!proyecto.pagos || proyecto.pagos.length === 0) && <p style={{ fontSize: "0.82rem", color: "var(--texto-tenue)" }}>Sin pagos registrados.</p>}
        </div>
        <form onSubmit={registrarPago} style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
          <input type="number" placeholder="Monto" value={monto} onChange={(e) => setMonto(e.target.value)} style={{ ...inputChico, width: 100 }} />
          <select value={metodo} onChange={(e) => setMetodo(e.target.value)} style={inputChico}>
            <option value="transferencia">Transferencia</option>
            <option value="efectivo">Efectivo</option>
          </select>
          <button type="submit" className="boton boton-ascua" style={{ fontSize: "0.82rem", padding: "8px 14px" }}>Registrar pago</button>
        </form>
      </div>

      <div>
        <h4 style={estiloSub}>Costo real y horas</h4>
        <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 8 }}>
          <label style={{ fontSize: "0.82rem", color: "var(--texto-tenue)" }}>Costo real de material:</label>
          <input type="number" value={costoReal} onChange={(e) => setCostoReal(e.target.value)} style={{ ...inputChico, width: 100 }} />
          <button onClick={guardarCostoReal} className="boton boton-borde" style={{ fontSize: "0.78rem", padding: "6px 12px" }}>Guardar</button>
        </div>
        <p style={{ fontSize: "0.82rem", color: "var(--texto-tenue)" }}>
          Horas registradas por el trabajador: {proyecto.total_horas ?? 0}
        </p>
      </div>

      <div>
        <h4 style={estiloSub}>Fotos de avance</h4>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {(proyecto.fotos || []).map((foto) => (
            <a key={foto.id} href={urlImagen(foto.url)} target="_blank" rel="noreferrer">
              <img src={urlImagen(foto.url)} alt={foto.notas || "avance"} style={{ width: 100, height: 100, objectFit: "cover", borderRadius: "var(--radius-sm)", border: "1px solid var(--borde)" }} />
            </a>
          ))}
          {(!proyecto.fotos || proyecto.fotos.length === 0) && <p style={{ fontSize: "0.82rem", color: "var(--texto-tenue)" }}>El trabajador todavía no ha subido fotos.</p>}
        </div>
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

const inputChico = {
  padding: "6px 8px",
  borderRadius: "var(--radius-sm)",
  border: "1px solid var(--borde)",
  background: "var(--fondo)",
  color: "var(--texto)",
  fontSize: "0.82rem",
};

const estiloSub = { fontSize: "0.95rem", marginBottom: 8 };
