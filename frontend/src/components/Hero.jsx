export default function Hero() {
  return (
    <section id="inicio" style={{ borderBottom: "1px solid var(--borde)" }}>
      <div
        className="contenedor"
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 48,
          alignItems: "center",
          paddingTop: 72,
          paddingBottom: 56,
        }}
      >
        {/* Columna izquierda: mensaje */}
        <div>
          <p
            style={{
              fontFamily: "var(--font-mono)",
              color: "var(--ascua-400)",
              fontSize: "0.85rem",
              letterSpacing: "0.12em",
              textTransform: "uppercase",
              marginBottom: 18,
            }}
          >
            Taller familiar · Trabajo a la medida
          </p>
          <h1 style={{ fontSize: "clamp(2.4rem, 5vw, 3.8rem)", lineHeight: 0.98 }}>
            Forjamos hierro, aluminio y vidrio para que dure toda la vida.
          </h1>
          <p style={{ marginTop: 24, fontSize: "1.05rem", color: "var(--aluminio-300)", maxWidth: 480 }}>
            Portones, rejas, barandales, cancelería y vidrio templado, diseñados
            y fabricados en taller. Calcula tu precio por metro cuadrado en
            minutos, sin compromiso.
          </p>
          <div style={{ display: "flex", gap: 16, marginTop: 32, flexWrap: "wrap" }}>
            <a href="#catalogo" className="boton boton-ascua">Ver catálogo</a>
            <a href="#cotizador" className="boton boton-borde">Cotizar ahora</a>
          </div>

          <div style={{ display: "flex", gap: 28, marginTop: 44, flexWrap: "wrap" }}>
            <Dato numero="3" etiqueta="Materiales: hierro, aluminio y vidrio" />
            <Dato numero="100%" etiqueta="Piezas hechas a la medida" />
            <Dato numero="1" etiqueta="Cotización en minutos, en línea" />
          </div>
        </div>

        {/* Columna derecha: mockup del sitio, estilo laptop + teléfono */}
        <div className="ocultar-movil" style={{ position: "relative", height: 380 }}>
          <MockupLaptop />
          <MockupTelefono />
        </div>
      </div>
    </section>
  );
}

function Dato({ numero, etiqueta }) {
  return (
    <div>
      <p className="display" style={{ fontSize: "1.6rem", color: "var(--ascua-500)" }}>{numero}</p>
      <p style={{ fontSize: "0.8rem", color: "var(--texto-tenue)", maxWidth: 140 }}>{etiqueta}</p>
    </div>
  );
}

function MockupLaptop() {
  return (
    <div
      style={{
        position: "absolute",
        top: 10,
        left: "8%",
        width: "84%",
        borderRadius: "10px 10px 0 0",
        border: "1px solid var(--borde)",
        background: "var(--fondo-elevado)",
        boxShadow: "0 24px 50px rgba(0,0,0,0.25)",
        overflow: "hidden",
      }}
    >
      {/* barra del navegador */}
      <div style={{ display: "flex", gap: 6, padding: "10px 14px", borderBottom: "1px solid var(--borde)" }}>
        <span style={puntoEstilo("#e8622c")} />
        <span style={puntoEstilo("#c9cfd3")} />
        <span style={puntoEstilo("#7fb9c2")} />
      </div>
      {/* contenido simulado del sitio */}
      <div style={{ padding: 18 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
          <span className="display" style={{ fontSize: "0.95rem", color: "var(--ascua-500)" }}>LOS MEJÍA</span>
          <div style={{ display: "flex", gap: 8 }}>
            {[1, 2, 3].map((i) => (
              <span key={i} style={{ width: 28, height: 6, borderRadius: 3, background: "var(--borde)" }} />
            ))}
          </div>
        </div>
        <div style={{ width: "70%", height: 10, borderRadius: 3, background: "var(--ascua-500)", opacity: 0.8, marginBottom: 8 }} />
        <div style={{ width: "50%", height: 10, borderRadius: 3, background: "var(--borde)", marginBottom: 18 }} />
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10 }}>
          {["var(--ascua-500)", "var(--aluminio-300)", "var(--vidrio-400)"].map((c, i) => (
            <div key={i} style={{ border: "1px solid var(--borde)", borderRadius: 6, overflow: "hidden" }}>
              <div style={{ height: 42, background: c, opacity: 0.35 }} />
              <div style={{ padding: 8 }}>
                <div style={{ width: "80%", height: 6, borderRadius: 3, background: "var(--borde)", marginBottom: 5 }} />
                <div style={{ width: "50%", height: 6, borderRadius: 3, background: "var(--borde)" }} />
              </div>
            </div>
          ))}
        </div>
      </div>
      {/* base de la laptop */}
      <div style={{ height: 12, background: "var(--borde)", margin: "0 -6%", borderRadius: "0 0 6px 6px" }} />
    </div>
  );
}

function MockupTelefono() {
  return (
    <div
      style={{
        position: "absolute",
        bottom: -6,
        right: "4%",
        width: 108,
        height: 210,
        borderRadius: 18,
        border: "6px solid var(--fondo-elevado)",
        outline: "1px solid var(--borde)",
        background: "var(--fondo)",
        boxShadow: "0 20px 40px rgba(0,0,0,0.3)",
        overflow: "hidden",
        padding: 10,
      }}
    >
      <div style={{ width: "60%", height: 8, borderRadius: 3, background: "var(--ascua-500)", opacity: 0.8, marginBottom: 10 }} />
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 60, borderRadius: 6, border: "1px dashed var(--borde)", marginBottom: 10 }}>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: "1.1rem", color: "var(--ascua-400)" }}>$</span>
      </div>
      {[1, 2, 3].map((i) => (
        <div key={i} style={{ width: `${90 - i * 10}%`, height: 6, borderRadius: 3, background: "var(--borde)", marginBottom: 7 }} />
      ))}
    </div>
  );
}

function puntoEstilo(color) {
  return { width: 8, height: 8, borderRadius: "50%", background: color, display: "inline-block" };
}
