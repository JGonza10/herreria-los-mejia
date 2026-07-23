import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import LayoutPanel from "../components/LayoutPanel.jsx";
import { api } from "../api.js";

const ETIQUETA_COTIZACION = {
  nueva: "En revisión",
  revisada: "Revisada",
  aprobada: "Aprobada",
  rechazada: "No aprobada",
};
const ETIQUETA_PROYECTO = {
  pendiente: "Pendiente de iniciar",
  en_proceso: "En proceso",
  terminado: "Terminado",
  entregado: "Entregado",
  cancelado: "Cancelado",
};

export default function ClientePanel() {
  const [cotizaciones, setCotizaciones] = useState([]);
  const [proyectos, setProyectos] = useState([]);

  useEffect(() => {
    api.get("/api/cliente/cotizaciones").then(setCotizaciones).catch(() => {});
    api.get("/api/cliente/proyectos").then(setProyectos).catch(() => {});
  }, []);

  return (
    <LayoutPanel titulo="Mi panel">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <h2 style={{ fontSize: "1.6rem" }}>Mis proyectos ({proyectos.length})</h2>
        <Link to="/#cotizador" className="boton boton-ascua">Nueva cotización</Link>
      </div>

      <div style={{ display: "grid", gap: 14, marginBottom: 44 }}>
        {proyectos.map((p) => (
          <div key={p.id} style={{ border: "1px solid var(--borde)", borderRadius: "var(--radius-md)", padding: 18, background: "var(--fondo-elevado)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 10 }}>
              <p style={{ fontWeight: 600 }}>{p.titulo}</p>
              <span style={{ fontSize: "0.85rem", color: "var(--ascua-400)", fontWeight: 600 }}>{ETIQUETA_PROYECTO[p.estado]}</span>
            </div>
            <p style={{ fontSize: "0.85rem", color: "var(--texto-tenue)", marginTop: 4 }}>
              {p.material} · ${p.precio_estimado.toLocaleString("es-MX")}
              {p.trabajador_nombre && ` · A cargo de ${p.trabajador_nombre}`}
            </p>
            <div style={{ marginTop: 12, height: 6, background: "var(--fondo-sutil)", borderRadius: 999, overflow: "hidden" }}>
              <div style={{ width: `${p.avance_porcentaje}%`, height: "100%", background: "var(--ascua-500)" }} />
            </div>
            <p style={{ fontSize: "0.78rem", color: "var(--texto-tenue)", marginTop: 4 }}>{p.avance_porcentaje}% completado</p>
          </div>
        ))}
        {proyectos.length === 0 && <p style={{ color: "var(--texto-tenue)" }}>Todavía no tienes proyectos aprobados.</p>}
      </div>

      <h2 style={{ fontSize: "1.6rem", marginBottom: 18 }}>Mis cotizaciones ({cotizaciones.length})</h2>
      <div style={{ display: "grid", gap: 10 }}>
        {cotizaciones.map((c) => (
          <div key={c.id} style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 8, border: "1px solid var(--borde)", borderRadius: "var(--radius-sm)", padding: "12px 16px", background: "var(--fondo-elevado)" }}>
            <div>
              <p>{c.producto_nombre || "Propuesta personalizada"} · {c.material}</p>
              <p style={{ fontSize: "0.78rem", color: "var(--texto-tenue)" }}>{c.metros_cuadrados} m² · ${c.precio_estimado.toLocaleString("es-MX")}</p>
            </div>
            <span style={{ fontSize: "0.82rem", color: "var(--texto-tenue)" }}>{ETIQUETA_COTIZACION[c.estado]}</span>
          </div>
        ))}
        {cotizaciones.length === 0 && <p style={{ color: "var(--texto-tenue)" }}>Todavía no has enviado cotizaciones.</p>}
      </div>
    </LayoutPanel>
  );
}
