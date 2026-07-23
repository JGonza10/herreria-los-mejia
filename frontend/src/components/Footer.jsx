export default function Footer() {
  return (
    <footer id="contacto" style={{ padding: "56px 0 40px", borderTop: "1px solid var(--ceniza-700)" }}>
      <div
        className="contenedor"
        style={{
          display: "flex",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: 32,
        }}
      >
        <div>
          <span className="display" style={{ fontSize: "1.3rem" }}>LOS MEJÍA</span>
          <p style={{ color: "var(--ceniza-500)", marginTop: 8, maxWidth: 320, fontSize: "0.9rem" }}>
            Herrería de hierro, aluminio y vidrio. Trabajo a la medida, hecho en taller.
          </p>
        </div>

        <div>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--ceniza-500)", textTransform: "uppercase" }}>
            Síguenos
          </span>
          <div style={{ display: "flex", gap: 16, marginTop: 10 }}>
            <a href="https://facebook.com" target="_blank" rel="noreferrer" aria-label="Facebook" style={enlaceRedStyle}>Facebook</a>
            <a href="https://instagram.com" target="_blank" rel="noreferrer" aria-label="Instagram" style={enlaceRedStyle}>Instagram</a>
            <a href="https://wa.me/520000000000" target="_blank" rel="noreferrer" aria-label="WhatsApp" style={enlaceRedStyle}>WhatsApp</a>
          </div>
        </div>

        <div>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem", color: "var(--ceniza-500)", textTransform: "uppercase" }}>
            Contacto
          </span>
          <p style={{ marginTop: 10, fontSize: "0.9rem" }}>contacto@losmejia.com</p>
          <p style={{ fontSize: "0.9rem" }}>Tel. (000) 000-0000</p>
        </div>
      </div>

      <p style={{ textAlign: "center", color: "var(--ceniza-700)", fontSize: "0.78rem", marginTop: 40 }}>
        © {new Date().getFullYear()} Herrería Los Mejía. Todos los derechos reservados.
      </p>
    </footer>
  );
}

const enlaceRedStyle = {
  textDecoration: "none",
  fontSize: "0.9rem",
  color: "var(--aluminio-300)",
  borderBottom: "1px solid transparent",
};
