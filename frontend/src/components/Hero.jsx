export default function Hero() {
  return (
    <section id="inicio" style={{ borderBottom: "1px solid var(--borde)" }}>
      <div
        className="contenedor"
        style={{
          paddingTop: 40,
          paddingBottom: 32,
        }}
      >
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
        <h1 style={{ fontSize: "clamp(1.7rem, 3.2vw, 2.4rem)", lineHeight: 1.05, maxWidth: 760 }}>
          Forjamos hierro, aluminio y vidrio para que dure toda la vida.
        </h1>
        <p style={{ marginTop: 14, fontSize: "1rem", color: "var(--aluminio-300)", maxWidth: 560 }}>
          Portones, rejas, barandales, cancelería y vidrio templado. Explora el
          catálogo y calcula tu precio por metro cuadrado en minutos, sin compromiso.
        </p>
        <div style={{ display: "flex", gap: 14, marginTop: 20, flexWrap: "wrap", alignItems: "center" }}>
          <a href="#catalogo" className="boton boton-ascua">Ver catálogo</a>
          <a href="#cotizador" className="boton boton-borde">Cotizar ahora</a>
          <div style={{ display: "flex", gap: 20, marginLeft: 8, flexWrap: "wrap" }}>
            <Dato numero="3" etiqueta="materiales" />
            <Dato numero="100%" etiqueta="a la medida" />
            <Dato numero="1 día" etiqueta="cotización en línea" />
          </div>
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
