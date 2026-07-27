export default function Hero() {
  return (
    <section id="inicio" style={{ borderBottom: "1px solid var(--borde)" }}>
      <div
        className="contenedor"
        style={{
          display: "grid",
          gridTemplateColumns: "1.05fr 0.95fr",
          gap: 40,
          alignItems: "center",
          paddingTop: 48,
          paddingBottom: 40,
        }}
      >
        {/* Columna izquierda: mensaje */}
        <div>
          <p
            style={{
              fontFamily: "var(--font-mono)",
              color: "var(--ascua-400)",
              fontSize: "0.8rem",
              letterSpacing: "0.12em",
              textTransform: "uppercase",
              marginBottom: 10,
            }}
          >
            Taller familiar · Trabajo a la medida
          </p>
          <h1 style={{ fontSize: "clamp(1.8rem, 3.4vw, 2.6rem)", lineHeight: 1.05 }}>
            Forjamos hierro, aluminio y vidrio para que dure toda la vida.
          </h1>
          <p style={{ marginTop: 14, fontSize: "1rem", color: "var(--aluminio-300)", maxWidth: 480 }}>
            Portones, rejas, barandales, cancelería y vidrio templado. Explora
            el catálogo y calcula tu precio por metro cuadrado en minutos, sin
            compromiso.
          </p>
          <div style={{ display: "flex", gap: 14, marginTop: 22, flexWrap: "wrap", alignItems: "center" }}>
            <a href="#catalogo" className="boton boton-ascua">Ver catálogo</a>
            <a href="#cotizador" className="boton boton-borde">Cotizar ahora</a>
          </div>

          <div style={{ display: "flex", gap: 24, marginTop: 30, flexWrap: "wrap" }}>
            <Dato numero="3" etiqueta="materiales" />
            <Dato numero="100%" etiqueta="a la medida" />
            <Dato numero="1 día" etiqueta="cotización en línea" />
          </div>
        </div>

        {/* Columna derecha: mockup del sitio, estilo laptop + teléfono */}
        <div className="ocultar-movil" style={{ position: "relative", height: 340 }}>
          <MockupLaptop />
          <MockupTelefono />
        </div>
      </div>
    </section>
  );
}

function Dato({ numero, etiqueta }) {
  return (
    <div style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
      <span className="display" style={{ fontSize: "1.15rem", color: "var(--ascua-500)" }}>{numero}</span>
      <span style={{ fontSize: "0.78rem", color: "var(--texto-tenue)" }}>{etiqueta}</span>
    </div>
  );
}

function MockupLaptop() {
  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: "6%",
        width: "88%",
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
      <div style={{ padding: 16 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <span className="display" style={{ fontSize: "0.95rem", color: "var(--ascua-500)" }}>LOS MEJÍA</span>
          <div style={{ display: "flex", gap: 8 }}>
            {[1, 2, 3].map((i) => (
              <span key={i} style={{ width: 24, height: 6, borderRadius: 3, background: "var(--borde)" }} />
            ))}
          </div>
        </div>
        <div style={{ width: "70%", height: 9, borderRadius: 3, background: "var(--ascua-500)", opacity: 0.8, marginBottom: 6 }} />
        <div style={{ width: "50%", height: 9, borderRadius: 3, background: "var(--borde)", marginBottom: 14 }} />
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
          <TarjetaMaterial franja="#f0997b" icono={<IconoPorton />} />
          <TarjetaMaterial franja="#c9cfd3" icono={<IconoVentana />} />
          <TarjetaMaterial franja="#7fb9c2" icono={<IconoVidrio />} />
        </div>
      </div>
      {/* base de la laptop */}
      <div style={{ height: 10, background: "var(--borde)", margin: "0 -6%", borderRadius: "0 0 6px 6px" }} />
    </div>
  );
}

function TarjetaMaterial({ franja, icono }) {
  return (
    <div style={{ border: "1px solid var(--borde)", borderRadius: 6, overflow: "hidden", background: "#fff" }}>
      <div style={{ height: 24, background: franja, opacity: 0.55 }} />
      <div style={{ padding: 8, display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
        {icono}
        <div style={{ width: "80%", height: 5, borderRadius: 3, background: "var(--borde)" }} />
        <div style={{ width: "55%", height: 5, borderRadius: 3, background: "var(--borde)" }} />
      </div>
    </div>
  );
}

function IconoPorton() {
  return (
    <svg width="34" height="30" viewBox="0 0 88 76" fill="none">
      <g stroke="#c2532a" strokeWidth="6" strokeLinecap="round">
        <line x1="18" y1="76" x2="18" y2="30" />
        <line x1="70" y1="76" x2="70" y2="30" />
        <path d="M18 30 L44 14 L44 76" />
        <path d="M44 76 L44 14 L70 30" />
        <line x1="44" y1="52" x2="70" y2="52" />
        <line x1="18" y1="52" x2="44" y2="52" />
        <line x1="18" y1="76" x2="70" y2="76" />
      </g>
    </svg>
  );
}

function IconoVentana() {
  return (
    <svg width="34" height="30" viewBox="0 0 88 76" fill="none">
      <rect x="12" y="12" width="64" height="52" rx="3" stroke="#888780" strokeWidth="6" />
      <line x1="44" y1="12" x2="44" y2="64" stroke="#888780" strokeWidth="6" />
      <line x1="12" y1="38" x2="76" y2="38" stroke="#888780" strokeWidth="6" />
    </svg>
  );
}

function IconoVidrio() {
  return (
    <svg width="34" height="30" viewBox="0 0 88 76" fill="none">
      <path d="M22 12 L76 12 L64 64 L34 64 Z" fill="#cbe8ec" stroke="#1f6d78" strokeWidth="5" />
      <line x1="30" y1="24" x2="70" y2="24" stroke="#1f6d78" strokeWidth="4" />
      <line x1="33" y1="38" x2="67" y2="38" stroke="#1f6d78" strokeWidth="4" />
      <line x1="20" y1="18" x2="30" y2="58" stroke="#ffffff" strokeWidth="5" strokeLinecap="round" opacity="0.9" />
    </svg>
  );
}

function MockupTelefono() {
  return (
    <div
      style={{
        position: "absolute",
        bottom: -6,
        right: "2%",
        width: 100,
        height: 190,
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
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 52, borderRadius: 6, border: "1px dashed var(--borde)", marginBottom: 10 }}>
        <span style={{ fontFamily: "var(--font-mono)", fontSize: "1.05rem", color: "var(--ascua-400)" }}>$</span>
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
