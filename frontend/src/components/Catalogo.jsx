import { useEffect, useState } from "react";
import { api } from "../api.js";

const MATERIALES = [
  { valor: "", etiqueta: "Todos" },
  { valor: "hierro", etiqueta: "Hierro" },
  { valor: "aluminio", etiqueta: "Aluminio" },
  { valor: "vidrio", etiqueta: "Vidrio" },
];

const COLOR_MATERIAL = {
  hierro: "var(--ascua-500)",
  aluminio: "var(--aluminio-300)",
  vidrio: "var(--vidrio-400)",
};

export default function Catalogo({ onCotizarProducto }) {
  const [material, setMaterial] = useState("");
  const [productos, setProductos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setCargando(true);
    setError(null);
    const query = material ? `?material=${material}` : "";
    api
      .get(`/api/catalogo${query}`)
      .then(setProductos)
      .catch(() => setError("No se pudo cargar el catálogo. Intenta de nuevo más tarde."))
      .finally(() => setCargando(false));
  }, [material]);

  return (
    <section id="catalogo" style={{ padding: "72px 0" }}>
      <div className="contenedor">
        <h2 style={{ fontSize: "2.2rem" }}>Catálogo</h2>
        <p style={{ color: "var(--aluminio-300)", marginTop: 8, maxWidth: 560 }}>
          Piezas de referencia. Cada trabajo se fabrica a la medida exacta de
          tu espacio.
        </p>

        <div style={{ display: "flex", gap: 10, marginTop: 28, flexWrap: "wrap" }}>
          {MATERIALES.map((m) => (
            <button
              key={m.valor}
              onClick={() => setMaterial(m.valor)}
              style={{
                padding: "9px 18px",
                borderRadius: 999,
                border: `1px solid ${material === m.valor ? "var(--ascua-500)" : "var(--borde)"}`,
                background: material === m.valor ? "var(--ascua-500)" : "transparent",
                color: material === m.valor ? "#fff" : "var(--texto)",
                fontSize: "0.88rem",
                fontWeight: 600,
              }}
            >
              {m.etiqueta}
            </button>
          ))}
        </div>

        {error && <p style={{ color: "var(--ascua-400)", marginTop: 24 }}>{error}</p>}
        {cargando && <p style={{ color: "var(--texto-tenue)", marginTop: 24 }}>Cargando catálogo…</p>}

        {!cargando && !error && (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
              gap: 22,
              marginTop: 32,
            }}
          >
            {productos.map((p) => (
              <article
                key={p.id}
                style={{
                  background: "var(--fondo-elevado)",
                  border: "1px solid var(--borde)",
                  borderRadius: "var(--radius-md)",
                  overflow: "hidden",
                  borderTop: `3px solid ${COLOR_MATERIAL[p.material] || "var(--borde)"}`,
                  display: "flex",
                  flexDirection: "column",
                }}
              >
                {p.imagen_url ? (
                  <img
                    src={p.imagen_url}
                    alt={p.nombre}
                    style={{ width: "100%", height: 160, objectFit: "cover" }}
                  />
                ) : (
                  <div
                    style={{
                      width: "100%",
                      height: 160,
                      background: "var(--fondo-sutil)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      color: "var(--texto-tenue)",
                      fontSize: "0.8rem",
                    }}
                  >
                    Sin imagen todavía
                  </div>
                )}
                <div style={{ padding: 22, flex: 1, display: "flex", flexDirection: "column" }}>
                  <span
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: "0.7rem",
                      letterSpacing: "0.1em",
                      textTransform: "uppercase",
                      color: COLOR_MATERIAL[p.material],
                    }}
                  >
                    {p.material}
                  </span>
                  <h3 style={{ fontSize: "1.3rem", marginTop: 10 }}>{p.nombre}</h3>
                  <p style={{ color: "var(--aluminio-300)", fontSize: "0.92rem", marginTop: 8, flex: 1 }}>
                    {p.descripcion}
                  </p>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: 16 }}>
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: "1rem" }}>
                      Desde ${p.precio_referencia_m2.toLocaleString("es-MX")} / m²
                    </span>
                    <button
                      onClick={() => onCotizarProducto?.(p)}
                      style={{
                        background: "none",
                        border: "1px solid var(--ascua-500)",
                        color: "var(--ascua-400)",
                        borderRadius: "var(--radius-sm)",
                        padding: "6px 12px",
                        fontSize: "0.82rem",
                        fontWeight: 600,
                      }}
                    >
                      Cotizar
                    </button>
                  </div>
                </div>
              </article>
            ))}
            {productos.length === 0 && (
              <p style={{ color: "var(--texto-tenue)" }}>No hay productos para este material todavía.</p>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
