import { useEffect, useState } from "react";
import { api } from "../../api.js";

const ETIQUETA_ESTADO = {
  nueva: "Nueva",
  revisada: "Revisada",
  aprobada: "Aprobada → proyecto creado",
  rechazada: "Rechazada",
};

export default function AdminCotizaciones() {
  const [cotizaciones, setCotizaciones] = useState([]);
  const [trabajadores, setTrabajadores] = useState([]);
  const [seleccion, setSeleccion] = useState({});

  const cargar = () => api.get("/api/admin/cotizaciones").then(setCotizaciones).catch(() => {});

  useEffect(() => {
    cargar();
    api.get("/api/admin/usuarios?rol=trabajador").then(setTrabajadores).catch(() => {});
  }, []);

  const aprobar = async (id) => {
    await api.post(`/api/admin/cotizaciones/${id}/aprobar`, { trabajador_id: seleccion[id] || null });
    cargar();
  };

  const rechazar = async (id) => {
    await api.post(`/api/admin/cotizaciones/${id}/rechazar`, {});
    cargar();
  };

  return (
    <div>
      <h2 style={{ fontSize: "1.6rem", marginBottom: 18 }}>Cotizaciones recibidas ({cotizaciones.length})</h2>
      <div style={{ display: "grid", gap: 14 }}>
        {cotizaciones.map((c) => (
          <div key={c.id} style={{ border: "1px solid var(--borde)", borderRadius: "var(--radius-md)", padding: 18, background: "var(--fondo-elevado)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 10 }}>
              <div>
                <p style={{ fontWeight: 600 }}>{c.nombre_cliente} · {c.telefono}</p>
                <p style={{ fontSize: "0.85rem", color: "var(--texto-tenue)" }}>
                  {c.producto_nombre ? `Modelo: ${c.producto_nombre}` : "Propuesta personalizada"} · {c.material} · {c.metros_cuadrados} m²
                </p>
              </div>
              <div style={{ textAlign: "right" }}>
                <p style={{ fontFamily: "var(--font-mono)", fontSize: "1.2rem" }}>${c.precio_estimado.toLocaleString("es-MX")}</p>
                <p style={{ fontSize: "0.8rem", color: "var(--texto-tenue)" }}>{ETIQUETA_ESTADO[c.estado]}</p>
              </div>
            </div>

            {c.notas && <p style={{ fontSize: "0.85rem", marginTop: 8 }}>Notas: {c.notas}</p>}

            {c.estado === "nueva" && (
              <div style={{ display: "flex", gap: 10, marginTop: 14, flexWrap: "wrap", alignItems: "center" }}>
                <select
                  value={seleccion[c.id] || ""}
                  onChange={(e) => setSeleccion({ ...seleccion, [c.id]: e.target.value })}
                  style={{ padding: "8px 10px", borderRadius: "var(--radius-sm)", border: "1px solid var(--borde)", background: "var(--fondo)", color: "var(--texto)" }}
                >
                  <option value="">Sin asignar todavía</option>
                  {trabajadores.map((t) => (
                    <option key={t.id} value={t.id}>{t.nombre}</option>
                  ))}
                </select>
                <button onClick={() => aprobar(c.id)} className="boton boton-ascua">Aprobar y crear proyecto</button>
                <button onClick={() => rechazar(c.id)} className="boton boton-borde">Rechazar</button>
              </div>
            )}
          </div>
        ))}
        {cotizaciones.length === 0 && <p style={{ color: "var(--texto-tenue)" }}>Todavía no hay cotizaciones.</p>}
      </div>
    </div>
  );
}
