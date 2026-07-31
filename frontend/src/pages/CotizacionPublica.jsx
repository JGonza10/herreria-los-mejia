import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import Header from "../components/Header.jsx";
import { API_BASE } from "../config.js";
import { tarjetaEstilo } from "./Login.jsx";

// Página pública de aceptación de cotización (Fase 7.1) — sin login, el
// token firmado es lo que da acceso. No es un contrato ante notario, pero
// es infinitamente mejor que "usted me dijo que sí por teléfono".
export default function CotizacionPublica() {
  const { token } = useParams();
  const [cotizacion, setCotizacion] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);
  const [aceptando, setAceptando] = useState(false);

  const cargar = () => {
    setCargando(true);
    fetch(`${API_BASE}/api/cotizador/publica/${token}`)
      .then(async (r) => {
        const data = await r.json();
        if (!r.ok) throw new Error(data.error || "No se pudo cargar la cotización.");
        return data;
      })
      .then((data) => { setCotizacion(data); setError(null); })
      .catch((err) => setError(err.message))
      .finally(() => setCargando(false));
  };

  useEffect(() => { cargar(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [token]);

  const aceptar = async () => {
    setAceptando(true);
    try {
      const r = await fetch(`${API_BASE}/api/cotizador/publica/${token}/aceptar`, { method: "POST" });
      const data = await r.json();
      if (!r.ok) throw new Error(data.error || "No se pudo aceptar la cotización.");
      setCotizacion(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setAceptando(false);
    }
  };

  return (
    <>
      <Header />
      <div style={{ minHeight: "70vh", display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}>
        <div style={{ ...tarjetaEstilo, maxWidth: 520 }}>
          {cargando && <p style={{ color: "var(--texto-tenue)" }}>Cargando…</p>}

          {!cargando && error && (
            <>
              <h1 className="display" style={{ fontSize: "1.6rem", marginBottom: 10 }}>Enlace no válido</h1>
              <p style={{ color: "var(--ascua-400)" }}>{error}</p>
            </>
          )}

          {!cargando && cotizacion && (
            <>
              <h1 className="display" style={{ fontSize: "1.6rem", marginBottom: 4 }}>
                Cotización {cotizacion.folio || `#${cotizacion.id}`}
              </h1>
              <p style={{ color: "var(--texto-tenue)", fontSize: "0.9rem", marginBottom: 20 }}>
                Para {cotizacion.nombre_cliente}
              </p>

              {(cotizacion.partidas && cotizacion.partidas.length > 0 ? cotizacion.partidas : [{
                id: "unica", descripcion: cotizacion.material, cantidad: cotizacion.metros_cuadrados, importe: cotizacion.precio_estimado,
              }]).map((partida) => (
                <div key={partida.id} style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderBottom: "1px solid var(--borde)", fontSize: "0.9rem" }}>
                  <span>{partida.descripcion}</span>
                  <span>${partida.importe.toLocaleString("es-MX")}</span>
                </div>
              ))}

              <div style={{ display: "flex", justifyContent: "space-between", padding: "14px 0", fontSize: "1.3rem", fontFamily: "var(--font-mono)" }}>
                <span>Total</span>
                <span style={{ color: "var(--ascua-400)" }}>
                  ${(cotizacion.total ?? cotizacion.precio_estimado).toLocaleString("es-MX")}
                </span>
              </div>

              <p style={{ fontSize: "0.78rem", color: "var(--texto-tenue)", marginBottom: 20 }}>
                Estimado sujeto a medición en sitio. No incluye obra civil, resane, pintura de muro ni instalaciones eléctricas, salvo que se indique.
                {cotizacion.vigencia_hasta && ` Vigente hasta ${cotizacion.vigencia_hasta}.`}
              </p>

              {cotizacion.vencida && (
                <p style={{ color: "var(--ascua-400)", fontWeight: 600 }}>
                  Esta cotización ya venció. Contacta al taller para que te la actualicen con los precios vigentes.
                </p>
              )}

              {!cotizacion.vencida && cotizacion.aceptada_en && (
                <p style={{ color: "#4caf6d", fontWeight: 600 }}>
                  ¡Aceptada el {new Date(cotizacion.aceptada_en).toLocaleString("es-MX")}! El taller se pondrá en contacto contigo.
                </p>
              )}

              {!cotizacion.vencida && !cotizacion.aceptada_en && (
                <button onClick={aceptar} disabled={aceptando} className="boton boton-ascua" style={{ width: "100%", justifyContent: "center" }}>
                  {aceptando ? "Enviando…" : "Acepto esta cotización"}
                </button>
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
}
