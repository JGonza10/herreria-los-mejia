import { useEffect, useState } from "react";
import { api } from "../../api.js";

export default function AdminRequisicion() {
  const [datos, setDatos] = useState({ total_barras_6m: 0, detalle: [] });

  useEffect(() => {
    api.get("/api/admin/requisicion").then(setDatos).catch(() => {});
  }, []);

  return (
    <div>
      <h2 style={{ fontSize: "1.6rem", marginBottom: 6 }}>Requisición de material</h2>
      <p style={{ fontSize: "0.85rem", color: "var(--texto-tenue)", marginBottom: 20 }}>
        Suma el material de todos los proyectos activos (pendiente/en proceso) — para comprar una vez en vez de ir al proveedor cada vez que se corta un trabajo. Es un total agregado de barras de 6 m; no distingue calibre todavía.
      </p>

      <div style={{ border: "1px solid var(--borde)", borderRadius: "var(--radius-md)", padding: 20, background: "var(--fondo-elevado)", marginBottom: 24 }}>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--texto-tenue)", textTransform: "uppercase" }}>
          Total de barras comerciales (6 m)
        </span>
        <p style={{ fontFamily: "var(--font-mono)", fontSize: "2.2rem", color: "var(--ascua-400)", marginTop: 6 }}>
          {datos.total_barras_6m}
        </p>
      </div>

      <h3 style={{ fontSize: "1.1rem", marginBottom: 10 }}>Detalle por partida</h3>
      <div style={{ display: "grid", gap: 8 }}>
        {datos.detalle.map((d) => (
          <div key={d.partida_id} style={{ display: "flex", justifyContent: "space-between", border: "1px solid var(--borde)", borderRadius: "var(--radius-sm)", padding: "10px 14px", background: "var(--fondo-elevado)", fontSize: "0.85rem" }}>
            <span>{d.proyecto_titulo} — {d.descripcion}</span>
            <span style={{ color: "var(--texto-tenue)" }}>{d.num_barras} barra(s)</span>
          </div>
        ))}
        {datos.detalle.length === 0 && <p style={{ color: "var(--texto-tenue)" }}>Sin proyectos activos con material calculable.</p>}
      </div>
    </div>
  );
}
