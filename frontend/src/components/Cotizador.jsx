import { useEffect, useState } from "react";
import { api } from "../api.js";
import { useAuth } from "../context/AuthContext.jsx";
import Pieza3D from "./Pieza3D.jsx";
import Pieza2D from "./Pieza2D.jsx";

const MATERIALES = ["hierro", "aluminio", "vidrio"];

// El cotizador todavía no pregunta el tipo de trabajo (eso es Fase 4.1 de
// frontend, fuera de este alcance) — mientras tanto, el material ya alcanza
// para elegir una representación razonable en la vista previa.
const MODO_DIBUJO_POR_MATERIAL = { hierro: "barrotes", aluminio: "cancel", vidrio: "vidrio" };

export default function Cotizador({ productoPreseleccionado }) {
  const { usuario } = useAuth();
  const [modo, setModo] = useState("personalizada"); // "modelo" | "personalizada"
  const [productos, setProductos] = useState([]);
  const [productoId, setProductoId] = useState("");
  const [material, setMaterial] = useState("hierro");
  const [ancho, setAncho] = useState(2);
  const [alto, setAlto] = useState(1.5);
  const [conAcabado, setConAcabado] = useState(false);
  const [estimado, setEstimado] = useState(null);
  const [calculando, setCalculando] = useState(false);

  const [mostrarFormulario, setMostrarFormulario] = useState(false);
  const [nombre, setNombre] = useState(usuario?.nombre || "");
  const [telefono, setTelefono] = useState(usuario?.telefono || "");
  const [email, setEmail] = useState(usuario?.email || "");
  const [enviando, setEnviando] = useState(false);
  const [enviado, setEnviado] = useState(false);
  const [errorEnvio, setErrorEnvio] = useState(null);

  useEffect(() => {
    api.get("/api/catalogo").then(setProductos).catch(() => setProductos([]));
  }, []);

  useEffect(() => {
    if (productoPreseleccionado) {
      setModo("modelo");
      setProductoId(String(productoPreseleccionado.id));
      setMaterial(productoPreseleccionado.material);
    }
  }, [productoPreseleccionado]);

  useEffect(() => {
    if (modo === "modelo" && productoId) {
      const producto = productos.find((p) => String(p.id) === productoId);
      if (producto) setMaterial(producto.material);
    }
  }, [modo, productoId, productos]);

  useEffect(() => {
    const anchoNum = Number(ancho);
    const altoNum = Number(alto);
    if (!anchoNum || !altoNum || anchoNum <= 0 || altoNum <= 0) {
      setEstimado(null);
      return;
    }
    setCalculando(true);
    const timeout = setTimeout(() => {
      api
        .post("/api/cotizador/calcular", {
          material,
          ancho_m: anchoNum,
          alto_m: altoNum,
          con_acabado: conAcabado,
          producto_id: modo === "modelo" && productoId ? Number(productoId) : null,
        })
        .then(setEstimado)
        .catch(() => setEstimado(null))
        .finally(() => setCalculando(false));
    }, 300);
    return () => clearTimeout(timeout);
  }, [modo, productoId, material, ancho, alto, conAcabado]);

  const enviarSolicitud = async (e) => {
    e.preventDefault();
    setEnviando(true);
    setErrorEnvio(null);
    try {
      await api.post("/api/cotizador/solicitar", {
        nombre_cliente: nombre,
        telefono,
        email,
        material,
        ancho_m: Number(ancho),
        alto_m: Number(alto),
        con_acabado: conAcabado,
        producto_id: modo === "modelo" && productoId ? Number(productoId) : null,
      });
      setEnviado(true);
    } catch (err) {
      setErrorEnvio(err.message);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <section id="cotizador" style={{ padding: "72px 0", background: "var(--fondo-sutil)" }}>
      <div className="contenedor">
        <h2 style={{ fontSize: "2.2rem" }}>Cotizador</h2>
        <p style={{ color: "var(--aluminio-300)", marginTop: 8, maxWidth: 560 }}>
          Elige un modelo de nuestro catálogo o describe tu propia idea. El
          precio se calcula al instante; la cotización final se confirma al
          revisar tu proyecto.
        </p>

        <div style={{ display: "flex", gap: 10, marginTop: 24 }}>
          <button onClick={() => setModo("personalizada")} style={tabEstilo(modo === "personalizada")}>
            Propuesta personalizada
          </button>
          <button onClick={() => setModo("modelo")} style={tabEstilo(modo === "modelo")}>
            Modelo del catálogo
          </button>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1.1fr 0.9fr",
            gap: 32,
            background: "var(--fondo-elevado)",
            border: "1px solid var(--borde)",
            borderRadius: "var(--radius-md)",
            padding: 32,
            marginTop: 20,
          }}
        >
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            {modo === "modelo" ? (
              <div>
                <label style={etiquetaEstilo}>Modelo</label>
                <select
                  value={productoId}
                  onChange={(e) => setProductoId(e.target.value)}
                  style={{ ...inputEstilo, marginTop: 8 }}
                >
                  <option value="">Selecciona un modelo…</option>
                  {productos.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.nombre} ({p.material})
                    </option>
                  ))}
                </select>
              </div>
            ) : (
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
                        border: `1px solid ${material === m ? "var(--ascua-500)" : "var(--borde)"}`,
                        background: material === m ? "var(--ascua-500)" : "transparent",
                        color: material === m ? "#fff" : "var(--texto)",
                        fontWeight: 600,
                      }}
                    >
                      {m}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div style={{ display: "flex", gap: 16 }}>
              <div style={{ flex: 1 }}>
                <label style={etiquetaEstilo}>Ancho (m)</label>
                <input type="number" min="0.1" step="0.1" value={ancho} onChange={(e) => setAncho(e.target.value)} style={inputEstilo} />
              </div>
              <div style={{ flex: 1 }}>
                <label style={etiquetaEstilo}>Alto (m)</label>
                <input type="number" min="0.1" step="0.1" value={alto} onChange={(e) => setAlto(e.target.value)} style={inputEstilo} />
              </div>
            </div>

            <label style={{ display: "flex", alignItems: "center", gap: 10, fontSize: "0.92rem" }}>
              <input type="checkbox" checked={conAcabado} onChange={(e) => setConAcabado(e.target.checked)} />
              Acabado especial (pintura electrostática / esmerilado)
            </label>
          </div>

          <div
            style={{
              borderLeft: "1px dashed var(--borde)",
              paddingLeft: 32,
              display: "flex",
              flexDirection: "column",
              justifyContent: "center",
            }}
          >
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--texto-tenue)", textTransform: "uppercase" }}>
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
            {calculando && <span style={{ fontSize: "0.8rem", color: "var(--texto-tenue)", marginTop: 6 }}>calculando…</span>}

            {!mostrarFormulario && !enviado && (
              <button
                className="boton boton-ascua"
                style={{ marginTop: 20, justifyContent: "center" }}
                onClick={() => setMostrarFormulario(true)}
                disabled={!estimado || (modo === "modelo" && !productoId)}
              >
                Solicitar cotización formal
              </button>
            )}
          </div>
        </div>

        <VistaPrevia material={material} ancho={ancho} alto={alto} />

        {mostrarFormulario && !enviado && (
          <form
            onSubmit={enviarSolicitud}
            style={{
              background: "var(--fondo-elevado)",
              border: "1px solid var(--borde)",
              borderRadius: "var(--radius-md)",
              padding: 28,
              display: "grid",
              gap: 14,
              maxWidth: 480,
              marginTop: 24,
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
          <p style={{ color: "var(--vidrio-400)", fontWeight: 600, marginTop: 24 }}>
            ¡Listo! Recibimos tu solicitud.{" "}
            {usuario ? "Puedes ver su estatus en tu panel." : "El equipo de Los Mejía te contactará pronto."}
          </p>
        )}
      </div>
    </section>
  );
}

function VistaPrevia({ material, ancho, alto }) {
  const anchoNum = Number(ancho);
  const altoNum = Number(alto);
  if (!anchoNum || !altoNum || anchoNum <= 0 || altoNum <= 0) return null;

  const modoDibujo = MODO_DIBUJO_POR_MATERIAL[material] || "barrotes";
  const spec = { medidas: { ancho_m: anchoNum, alto_m: altoNum }, estructura: {} };

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        gap: 24,
        background: "var(--fondo-elevado)",
        border: "1px solid var(--borde)",
        borderRadius: "var(--radius-md)",
        padding: 24,
        marginTop: 20,
      }}
    >
      <div>
        <span style={etiquetaEstilo}>Vista 3D</span>
        <div style={{ marginTop: 10 }}>
          <Pieza3D spec={spec} modoDibujo={modoDibujo} />
        </div>
      </div>
      <div>
        <span style={etiquetaEstilo}>Alzado</span>
        <div style={{ marginTop: 10 }}>
          <Pieza2D spec={spec} modoDibujo={modoDibujo} />
        </div>
      </div>
    </div>
  );
}

function tabEstilo(activo) {
  return {
    padding: "9px 18px",
    borderRadius: 999,
    border: `1px solid ${activo ? "var(--ascua-500)" : "var(--borde)"}`,
    background: activo ? "var(--ascua-500)" : "transparent",
    color: activo ? "#fff" : "var(--texto)",
    fontSize: "0.88rem",
    fontWeight: 600,
  };
}

const etiquetaEstilo = {
  fontSize: "0.78rem",
  color: "var(--texto-tenue)",
  textTransform: "uppercase",
  letterSpacing: "0.06em",
  fontFamily: "var(--font-mono)",
};

const inputEstilo = {
  width: "100%",
  padding: "10px 12px",
  borderRadius: "var(--radius-sm)",
  border: "1px solid var(--borde)",
  background: "var(--fondo)",
  color: "var(--texto)",
  fontSize: "0.95rem",
};
