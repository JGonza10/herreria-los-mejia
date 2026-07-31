import { useEffect, useState } from "react";
import { api } from "../../api.js";

const ETIQUETA_ESTADO = {
  nueva: "Nueva",
  revisada: "Revisada",
  aprobada: "Aprobada → proyecto creado",
  rechazada: "Rechazada",
  vencida: "Vencida",
};

export default function AdminCotizaciones() {
  const [cotizaciones, setCotizaciones] = useState([]);
  const [trabajadores, setTrabajadores] = useState([]);
  const [seleccion, setSeleccion] = useState({});
  const [seguimiento, setSeguimiento] = useState(null);
  const [mostrarSeguimiento, setMostrarSeguimiento] = useState(false);
  const [simulando, setSimulando] = useState(null);

  const cargar = () => api.get("/api/admin/cotizaciones").then(setCotizaciones).catch(() => {});
  const cargarSeguimiento = () => api.get("/api/admin/cotizaciones/seguimiento").then(setSeguimiento).catch(() => {});

  useEffect(() => {
    cargar();
    cargarSeguimiento();
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

  const revivir = async (id) => {
    await api.post(`/api/admin/cotizaciones/${id}/revivir`, {});
    cargar();
    cargarSeguimiento();
  };

  const totalSeguimiento = seguimiento
    ? seguimiento["3_dias"].length + seguimiento["7_dias"].length + seguimiento["15_dias_o_mas"].length
    : 0;

  return (
    <div>
      <h2 style={{ fontSize: "1.6rem", marginBottom: 18 }}>Cotizaciones recibidas ({cotizaciones.length})</h2>

      {seguimiento && totalSeguimiento > 0 && (
        <div style={{ border: "1px solid var(--ascua-500)", borderRadius: "var(--radius-md)", padding: 16, marginBottom: 20, background: "var(--fondo-elevado)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontWeight: 600 }}>
              {totalSeguimiento} cotización(es) sin respuesta — la mayoría no se pierden por precio, se pierden por falta de seguimiento
            </span>
            <button onClick={() => setMostrarSeguimiento(!mostrarSeguimiento)} className="boton boton-borde">
              {mostrarSeguimiento ? "Ocultar" : "Ver detalle"}
            </button>
          </div>
          {mostrarSeguimiento && (
            <div style={{ marginTop: 14, display: "grid", gap: 10 }}>
              {[["3_dias", "3+ días"], ["7_dias", "7+ días"], ["15_dias_o_mas", "15+ días"]].map(([clave, etiqueta]) => (
                seguimiento[clave].length > 0 && (
                  <div key={clave}>
                    <p style={{ fontSize: "0.8rem", color: "var(--texto-tenue)", marginBottom: 4 }}>{etiqueta}</p>
                    {seguimiento[clave].map((c) => (
                      <div key={c.id} style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", padding: "6px 0" }}>
                        <span>{c.nombre_cliente} · {c.folio || `#${c.id}`}</span>
                        {c.link_whatsapp && (
                          <a href={c.link_whatsapp} target="_blank" rel="noreferrer" style={{ color: "#4caf6d" }}>
                            Escribir por WhatsApp
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                )
              ))}
            </div>
          )}
        </div>
      )}

      <div style={{ display: "grid", gap: 14 }}>
        {cotizaciones.map((c) => (
          <div key={c.id} style={{ border: "1px solid var(--borde)", borderRadius: "var(--radius-md)", padding: 18, background: "var(--fondo-elevado)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 10 }}>
              <div>
                <p style={{ fontWeight: 600 }}>
                  {c.nombre_cliente} · {c.telefono} {c.folio && <span style={{ color: "var(--texto-tenue)", fontWeight: 400 }}>· {c.folio}</span>}
                </p>
                <p style={{ fontSize: "0.85rem", color: "var(--texto-tenue)" }}>
                  {c.producto_nombre ? `Modelo: ${c.producto_nombre}` : "Propuesta personalizada"} · {c.material} · {c.metros_cuadrados} m²
                  {c.partidas?.length > 1 && ` · ${c.partidas.length} partidas`}
                </p>
              </div>
              <div style={{ textAlign: "right" }}>
                <p style={{ fontFamily: "var(--font-mono)", fontSize: "1.2rem" }}>${(c.total ?? c.precio_estimado).toLocaleString("es-MX")}</p>
                <p style={{ fontSize: "0.8rem", color: c.estado === "vencida" ? "var(--ascua-400)" : "var(--texto-tenue)" }}>{ETIQUETA_ESTADO[c.estado]}</p>
              </div>
            </div>

            {c.notas && <p style={{ fontSize: "0.85rem", marginTop: 8 }}>Notas: {c.notas}</p>}

            <div style={{ display: "flex", gap: 10, marginTop: 14, flexWrap: "wrap", alignItems: "center" }}>
              {c.estado === "nueva" && (
                <>
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
                </>
              )}
              {c.estado === "vencida" && (
                <button onClick={() => revivir(c.id)} className="boton boton-ascua">Revivir con precios actuales</button>
              )}
              {c.link_whatsapp && (
                <a href={c.link_whatsapp} target="_blank" rel="noreferrer" className="boton boton-borde">WhatsApp</a>
              )}
              {c.token_publico && (
                <button
                  onClick={() => navigator.clipboard.writeText(`${window.location.origin}/cotizacion/${c.token_publico}`)}
                  className="boton boton-borde"
                >
                  Copiar link de aceptación
                </button>
              )}
              <button onClick={() => setSimulando(simulando === c.id ? null : c.id)} className="boton boton-borde">
                {simulando === c.id ? "Cerrar simulación" : "Simular"}
              </button>
            </div>

            {simulando === c.id && <PanelSimulacion cotizacionId={c.id} />}
          </div>
        ))}
        {cotizaciones.length === 0 && <p style={{ color: "var(--texto-tenue)" }}>Todavía no hay cotizaciones.</p>}
      </div>
    </div>
  );
}

function PanelSimulacion({ cotizacionId }) {
  const [params, setParams] = useState({
    mano_obra: 0, flete_km: 0, flete_precio_km: 0, merma_pct: 7, utilidad_pct: 25, descuento: 0, aplica_iva: false,
  });
  const [resultado, setResultado] = useState(null);
  const [calculando, setCalculando] = useState(false);
  const [error, setError] = useState(null);

  const simular = async () => {
    setCalculando(true);
    setError(null);
    try {
      const r = await api.post(`/api/admin/cotizaciones/${cotizacionId}/simular`, params);
      setResultado(r);
    } catch (err) {
      setError(err.message);
    } finally {
      setCalculando(false);
    }
  };

  useEffect(() => { simular(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, []);

  const campo = (clave, etiqueta, esCheckbox = false) => (
    <label style={{ fontSize: "0.8rem", color: "var(--texto-tenue)", display: "flex", flexDirection: "column", gap: 4 }}>
      {etiqueta}
      {esCheckbox ? (
        <input type="checkbox" checked={params[clave]} onChange={(e) => setParams({ ...params, [clave]: e.target.checked })} />
      ) : (
        <input
          type="number" value={params[clave]}
          onChange={(e) => setParams({ ...params, [clave]: Number(e.target.value) })}
          style={{ padding: "6px 8px", borderRadius: "var(--radius-sm)", border: "1px solid var(--borde)", background: "var(--fondo)", color: "var(--texto)", width: 100 }}
        />
      )}
    </label>
  );

  return (
    <div style={{ marginTop: 16, padding: 16, background: "var(--fondo-sutil)", borderRadius: "var(--radius-sm)" }}>
      <p style={{ fontSize: "0.8rem", color: "var(--texto-tenue)", marginBottom: 10 }}>
        No se guarda nada — solo para que el dueño vea el margen antes de confirmar.
      </p>
      <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 14 }}>
        {campo("mano_obra", "Mano de obra ($)")}
        {campo("flete_km", "Flete (km)")}
        {campo("flete_precio_km", "Flete ($/km)")}
        {campo("merma_pct", "Merma (%)")}
        {campo("utilidad_pct", "Utilidad (%)")}
        {campo("descuento", "Descuento ($)")}
        {campo("aplica_iva", "Aplica IVA", true)}
      </div>
      <button onClick={simular} className="boton boton-ascua" disabled={calculando}>
        {calculando ? "Calculando…" : "Recalcular"}
      </button>

      {error && <p style={{ color: "var(--ascua-400)", marginTop: 10 }}>{error}</p>}

      {resultado && (
        <div style={{ marginTop: 16, display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 10 }}>
          <Dato etiqueta="Costo directo" valor={`$${resultado.costo_directo.toLocaleString("es-MX")}`} />
          <Dato etiqueta="Utilidad" valor={`$${resultado.utilidad.toLocaleString("es-MX")}`} />
          <Dato etiqueta="Margen sobre venta" valor={`${resultado.margen_sobre_venta_pct}%`} destacado />
          <Dato etiqueta="Subtotal" valor={`$${resultado.subtotal.toLocaleString("es-MX")}`} />
          <Dato etiqueta="IVA" valor={`$${resultado.iva.toLocaleString("es-MX")}`} />
          <Dato etiqueta="Total" valor={`$${resultado.total.toLocaleString("es-MX")}`} destacado />
          <Dato
            etiqueta="Estimado al cliente"
            valor={`$${resultado.estimado_cliente_min.toLocaleString("es-MX")} – $${resultado.estimado_cliente_max.toLocaleString("es-MX")}`}
          />
        </div>
      )}
    </div>
  );
}

function Dato({ etiqueta, valor, destacado }) {
  return (
    <div>
      <span style={{ fontSize: "0.72rem", color: "var(--texto-tenue)", textTransform: "uppercase", display: "block" }}>{etiqueta}</span>
      <span style={{ fontFamily: "var(--font-mono)", fontSize: destacado ? "1.1rem" : "0.95rem", color: destacado ? "var(--ascua-400)" : "var(--texto)" }}>
        {valor}
      </span>
    </div>
  );
}
