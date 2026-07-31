import { useEffect, useState } from "react";
import { api } from "../../api.js";

export default function AdminAgenda() {
  const [semanas, setSemanas] = useState([]);

  useEffect(() => {
    api.get("/api/admin/agenda").then(setSemanas).catch(() => {});
  }, []);

  return (
    <div>
      <h2 style={{ fontSize: "1.6rem", marginBottom: 6 }}>Agenda y capacidad</h2>
      <p style={{ fontSize: "0.85rem", color: "var(--texto-tenue)", marginBottom: 20 }}>
        Carga de trabajo por semana de entrega estimada, contra la capacidad del taller.
      </p>

      <div style={{ display: "grid", gap: 12 }}>
        {semanas.map((s) => (
          <div
            key={s.semana_inicio}
            style={{
              border: `1px solid ${s.sobrecargada ? "var(--ascua-500)" : "var(--borde)"}`,
              borderRadius: "var(--radius-md)", padding: 16,
              background: s.sobrecargada ? "var(--ascua-500)10" : "var(--fondo-elevado)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
              <span style={{ fontWeight: 600 }}>Semana del {s.semana_inicio}</span>
              <span style={{ color: s.sobrecargada ? "var(--ascua-400)" : "var(--texto-tenue)", fontWeight: 600, fontSize: "0.85rem" }}>
                {s.carga} / {s.capacidad} {s.sobrecargada ? "· SOBRECARGADA" : ""}
              </span>
            </div>
            <div style={{ marginTop: 8, height: 6, background: "var(--fondo-sutil)", borderRadius: 999, overflow: "hidden" }}>
              <div
                style={{
                  width: `${Math.min(100, (s.carga / s.capacidad) * 100)}%`, height: "100%",
                  background: s.sobrecargada ? "var(--ascua-500)" : "var(--vidrio-400)",
                }}
              />
            </div>
            <p style={{ fontSize: "0.8rem", color: "var(--texto-tenue)", marginTop: 8 }}>
              {s.proyectos.map((p) => p.titulo).join(", ")}
            </p>
          </div>
        ))}
        {semanas.length === 0 && <p style={{ color: "var(--texto-tenue)" }}>Sin proyectos activos con fecha estimada.</p>}
      </div>
    </div>
  );
}
