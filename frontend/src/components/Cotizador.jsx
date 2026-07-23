import { useEffect, useState } from "react";
import { API_BASE } from "../config.js";

const MATERIALES = ["hierro", "aluminio", "vidrio"];

export default function Cotizador() {
  const [material, setMaterial] = useState("hierro");
  const [ancho, setAncho] = useState(2);
  const [alto, setAlto] = useState(1.5);
  const [conAcabado, setConAcabado] = useState(false);
  const [estimado, setEstimado] = useState(null);
  const [calculando, setCalculando] = useState(false);

  const [mostrarFormulario, setMostrarFormulario] = useState(false);
  const [nombre, setNombre] = useState("");
  const [telefono, setTelefono] = useState("");
  const [email, setEmail] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [enviado, setEnviado] = useState(false);
  const [errorEnvio, setErrorEnvio] = useState(null);

  useEffect(() => {
    const anchoNum = Number(ancho);
    const altoNum = Number(alto);
    if (!anchoNum || !altoNum || anchoNum <= 0 || altoNum <= 0) {
      setEstimado(null);
      return;
    }
    setCalculando(true);
    const timeout = setTimeout(() => {
      fetch(`${API_BASE}/api/cotizador/calcular`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ material, ancho_m: anchoNum, alto_m: altoNum, con_acabado: conAcabado }),
      })
        .then((r) => r.json())
        .then((data) => setEstimado(data.error ? null : data))
        .catch(() => setEstimado(null))
        .finally(() => setCalculando(false));
    }, 300);
    return () => clearTimeout(timeout);
  }, [material, ancho, alto, conAcabado]);

  const enviarSolicitud = async (e) => {
    e.preventDefault();
    setEnviando(true);
    setErrorEnvio(null);
    try {
      const r = await fetch(`${API_BASE}/api/cotizador/solicitar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          nombre_cliente: nombre,
          telefono,
          email,
          material,
          ancho_m: Number(ancho),
          alto_m: Number(alto),
          con_acabado: conAcabado,
        }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.error || "Error al enviar la solicitud");
      setEnviado(true);
    } catch (err) {
      setErrorEnvio(err.message);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <section id="cotizador" style={{ padding: "72px 0", background: "var(--hierro-900)" }}>
      <div className="contenedor" style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr)", gap: 40 }}>
        <div>
          <h2 style={{ fontSize: "2.2rem" }}>Cotizador</h2>
          <p style={{ color: "var(--aluminio-300)", marginTop: 8, maxWidth: 560 }}>
            Dinos el material y las medidas de tu proyecto. El precio se
            calcula al instante; es una referencia, la cotización final se
            confirma al revisar el sitio.
          </p>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1.1fr 0.9fr",
            gap: 32,
            background: "var(--hierro-800)",
            border: "1px solid var(--ceniza-700)",
            borderRadius: "var(--radius-md)",
            padding: 32,
          }}
        >
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            <div>
              <label style={etiquetaEstilo}>Material</label>
              <div style={{ display: "flex", gap: 10, marginTop: 8 }}>
                {MATERIALES.map((m) => (
                  <button
                    key={m}
                    onClick={() => setMaterial(m)}
                    style={{
                      flex: 1,
                      padding: "10px 0",
                      textTransform: "capitalize",
                      borderRadius: "var(--radius-sm)",
                      border: `1px solid ${material === m ? "var(--ascua-500)" : "var(--ceniza-700)"}`,
                      background: material === m ? "var(--ascua-500)" : "transparent",
                      color: "var(--hueso-100)",
                      fontWeight: 600,
                    }}
                  >
                    {m}
                  </button>
                ))}
              </div>
            </div>

            <div style={{ display: "flex", gap: 16 }}>
              <div style={{ flex: 1 }}>
                <label style={etiquetaEstilo}>Ancho (m)</label>
                <input
                  type="number"
                  min="0.1"
                  step="0.1"
                  value={ancho}
                  onChange={(e) => setAncho(e.target.value)}
                  style={inputEstilo}
                />
              </div>
              <div style={{ flex: 1 }}>
                <label style={etiquetaEstilo}>Alto (m)</label>
                <input
                  type="number"
                  min="0.1"
                  step="0.1"
                  value={alto}
                  onChange={(e) => setAlto(e.target.value)}
                  style={inputEstilo}
                />
              </div>
            </div>

            <label style={{ display: "flex", alignItems: "center", gap: 10, fontSize: "0.92rem" }}>
              <input type="checkbox" checked={conAcabado} onChange={(e) => setConAcabado(e.target.checked)} />
              Acabado especial (pintura electrostática / esmerilado)
            </label>
          </div>

          <div
            style={{
              borderLeft: "1px dashed var(--ceniza-700)",
              paddingLeft: 32,
              display: "flex",
              flexDirection: "column",
              justifyContent: "center",
            }}
          >
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--ceniza-500)", textTransform: "uppercase" }}>
              Precio estimado
            </span>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "2.4rem", color: "var(--ascua-400)", marginTop: 6 }}>
              {estimado ? `$${estimado.precio_estimado.toLocaleString("es-MX")}` : "—"}
            </span>
            {estimado && (
              <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.85rem", color: "var(--aluminio-300)" }}>
                {estimado.metros_cuadrados} m²
              </span>
            )}
            {calculando && <span style={{ fontSize: "0.8rem", color: "var(--ceniza-500)", marginTop: 6 }}>calculando…</span>}

            {!mostrarFormulario && !enviado && (
              <button
                className="boton boton-ascua"
                style={{ marginTop: 20, justifyContent: "center" }}
                onClick={() => setMostrarFormulario(true)}
                disabled={!estimado}
              >
                Solicitar cotización formal
              </button>
            )}
          </div>
        </div>

        {mostrarFormulario && !enviado && (
          <form
            onSubmit={enviarSolicitud}
            style={{
              background: "var(--hierro-800)",
              border: "1px solid var(--ceniza-700)",
              borderRadius: "var(--radius-md)",
              padding: 28,
              display: "grid",
              gap: 14,
              maxWidth: 480,
            }}
          >
            <label style={etiquetaEstilo}>Nombre</label>
            <input required value={nombre} onChange={(e) => setNombre(e.target.value)} style={inputEstilo} />
            <label style={etiquetaEstilo}>Teléfono</label>
            <input required value={telefono} onChange={(e) => setTelefono(e.target.value)} style={inputEstilo} />
            <label style={etiquetaEstilo}>Email (opcional)</label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} style={inputEstilo} />
            {errorEnvio && <p style={{ color: "var(--ascua-400)", fontSize: "0.88rem" }}>{errorEnvio}</p>}
            <button type="submit" className="boton boton-ascua" disabled={enviando} style={{ justifyContent: "center" }}>
              {enviando ? "Enviando…" : "Enviar solicitud"}
            </button>
          </form>
        )}

        {enviado && (
          <p style={{ color: "var(--vidrio-400)", fontWeight: 600 }}>
            ¡Listo! Recibimos tu solicitud. El equipo de Los Mejía te contactará pronto.
          </p>
        )}
      </div>
    </section>
  );
}

const etiquetaEstilo = {
  fontSize: "0.78rem",
  color: "var(--ceniza-500)",
  textTransform: "uppercase",
  letterSpacing: "0.06em",
  fontFamily: "var(--font-mono)",
};

const inputEstilo = {
  width: "100%",
  padding: "10px 12px",
  borderRadius: "var(--radius-sm)",
  border: "1px solid var(--ceniza-700)",
  background: "var(--hierro-950)",
  color: "var(--hueso-100)",
  fontSize: "0.95rem",
};
