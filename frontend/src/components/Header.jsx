export default function Header() {
  return (
    <header
      style={{
        position: "sticky",
        top: 0,
        zIndex: 40,
        background: "rgba(23, 20, 15, 0.92)",
        backdropFilter: "blur(6px)",
        borderBottom: "1px solid var(--ceniza-700)",
      }}
    >
      <div
        className="contenedor"
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          height: 72,
        }}
      >
        <a href="#inicio" style={{ textDecoration: "none" }}>
          <span className="display" style={{ fontSize: "1.5rem", letterSpacing: "0.04em" }}>
            LOS MEJÍA
          </span>
          <span
            style={{
              display: "block",
              fontSize: "0.62rem",
              color: "var(--ceniza-500)",
              fontFamily: "var(--font-mono)",
              textTransform: "uppercase",
              letterSpacing: "0.15em",
              marginTop: -2,
            }}
          >
            Hierro · Aluminio · Vidrio
          </span>
        </a>
        <nav style={{ display: "flex", gap: 28, fontSize: "0.92rem" }}>
          <a href="#catalogo" style={{ textDecoration: "none" }}>Catálogo</a>
          <a href="#cotizador" style={{ textDecoration: "none" }}>Cotizador</a>
          <a href="#contacto" style={{ textDecoration: "none" }}>Contacto</a>
        </nav>
      </div>
    </header>
  );
}
