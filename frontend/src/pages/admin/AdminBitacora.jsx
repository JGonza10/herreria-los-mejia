import { useEffect, useState } from "react";
import { api } from "../../api.js";

const ETIQUETA_ACCION = {
  cambio_precio: "Cambio de precio",
  activacion: "Activación de tarifa",
  cambio_estado: "Cambio de estado",
  asignacion: "Asignación de trabajador",
};

export default function AdminBitacora() {
  const [registros, setRegistros] = useState([]);
  const [entidad, setEntidad] = useState("");

  useEffect(() => {
    const ruta = entidad ? `/api/admin/bitacora?entidad=${entidad}` : "/api/admin/bitacora";
    api.get(ruta).then(setRegistros).catch(() => {});
  }, [entidad]);

  return (
    <div>
      <h2 style={{ fontSize: "1.6rem", marginBottom: 6 }}>Bitácora de auditoría</h2>
      <p style={{ fontSize: "0.85rem", color: "var(--texto-tenue)", marginBottom: 18 }}>
        Quién cambió qué, y cuándo — últimos 200 registros.
      </p>

      <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
        {["", "tarifa", "proyecto", "cotizacion"].map((e) => (
          <button
            key={e}
            onClick={() => setEntidad(e)}
            style={{
              padding: "7px 14px", borderRadius: 999,
              border: `1px solid ${entidad === e ? "var(--ascua-500)" : "var(--borde)"}`,
              background: entidad === e ? "var(--ascua-500)" : "transparent",
              color: entidad === e ? "#fff" : "var(--texto)", fontSize: "0.82rem", fontWeight: 600,
            }}
          >
            {e || "Todas"}
          </button>
        ))}
      </div>

      <div style={{ display: "grid", gap: 8 }}>
        {registros.map((r) => (
          <div key={r.id} style={{ border: "1px solid var(--borde)", borderRadius: "var(--radius-sm)", padding: "10px 14px", background: "var(--fondo-elevado)", fontSize: "0.85rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
              <span>
                <strong>{r.usuario_nombre || "Sistema"}</strong> — {ETIQUETA_ACCION[r.accion] || r.accion} en {r.entidad} #{r.entidad_id}
              </span>
              <span style={{ color: "var(--texto-tenue)", fontSize: "0.78rem" }}>{new Date(r.creado_en).toLocaleString("es-MX")}</span>
            </div>
            {(r.antes || r.despues) && (
              <details style={{ marginTop: 6 }}>
                <summary style={{ cursor: "pointer", color: "var(--texto-tenue)", fontSize: "0.78rem" }}>Ver detalle</summary>
                <pre style={{ fontSize: "0.72rem", overflowX: "auto", background: "var(--fondo-sutil)", padding: 8, borderRadius: 6, marginTop: 4 }}>
                  {JSON.stringify({ antes: r.antes, despues: r.despues }, null, 2)}
                </pre>
              </details>
            )}
          </div>
        ))}
        {registros.length === 0 && <p style={{ color: "var(--texto-tenue)" }}>Sin registros todavía.</p>}
      </div>
    </div>
  );
}
