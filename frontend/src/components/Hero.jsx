export default function Hero() {
  return (
    <section
      id="inicio"
      style={{
        position: "relative",
        overflow: "hidden",
        borderBottom: "1px solid var(--ceniza-700)",
      }}
    >
      {/* Patrón de fondo: silueta de reja forjada */}
      <svg
        aria-hidden="true"
        style={{ position: "absolute", inset: 0, width: "100%", height: "100%", opacity: 0.16 }}
        preserveAspectRatio="xMidYMid slice"
        viewBox="0 0 1180 640"
      >
        <defs>
          <pattern id="barrotes" width="60" height="640" patternUnits="userSpaceOnUse">
            <rect x="26" width="8" height="640" fill="var(--aluminio-300)" />
            <circle cx="30" cy="90" r="14" fill="none" stroke="var(--aluminio-300)" strokeWidth="6" />
            <circle cx="30" cy="550" r="14" fill="none" stroke="var(--aluminio-300)" strokeWidth="6" />
          </pattern>
        </defs>
        <rect width="1180" height="640" fill="url(#barrotes)" />
        <rect y="150" width="1180" height="10" fill="var(--aluminio-300)" />
        <rect y="470" width="1180" height="10" fill="var(--aluminio-300)" />
      </svg>

      <div
        className="contenedor"
        style={{
          position: "relative",
          paddingTop: 96,
          paddingBottom: 96,
          maxWidth: 760,
        }}
      >
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
        <h1 style={{ fontSize: "clamp(2.6rem, 6vw, 4.4rem)", lineHeight: 0.98 }}>
          Forjamos hierro, aluminio y vidrio para que dure toda la vida.
        </h1>
        <p style={{ marginTop: 24, fontSize: "1.08rem", color: "var(--aluminio-300)", maxWidth: 560 }}>
          Portones, rejas, barandales, cancelería y vidrio templado, diseñados
          y fabricados en taller. Calcula tu precio por metro cuadrado en
          minutos, sin compromiso.
        </p>
        <div style={{ display: "flex", gap: 16, marginTop: 36, flexWrap: "wrap" }}>
          <a href="#catalogo" className="boton boton-ascua">Ver catálogo</a>
          <a href="#cotizador" className="boton boton-borde">Cotizar ahora</a>
        </div>
      </div>
    </section>
  );
}
