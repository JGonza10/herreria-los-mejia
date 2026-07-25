const BENEFICIOS = [
  {
    titulo: "Diseño a tu medida",
    texto: "Cada pieza se fabrica según las medidas exactas de tu espacio, no sobre catálogo genérico.",
    color: "var(--ascua-500)",
  },
  {
    titulo: "3 materiales, un solo taller",
    texto: "Hierro, aluminio y vidrio trabajados internamente — sin subcontratar tu proyecto.",
    color: "var(--aluminio-300)",
  },
  {
    titulo: "Cotización instantánea",
    texto: "Calcula tu precio por m² en línea, sin esperar una llamada ni una visita.",
    color: "var(--vidrio-400)",
  },
];

export default function Beneficios() {
  return (
    <section style={{ padding: "48px 0", background: "var(--fondo-sutil)", borderBottom: "1px solid var(--borde)" }}>
      <div
        className="contenedor"
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: 28,
        }}
      >
        {BENEFICIOS.map((b) => (
          <div key={b.titulo} style={{ borderLeft: `3px solid ${b.color}`, paddingLeft: 18 }}>
            <p style={{ fontWeight: 700, fontSize: "1.02rem", marginBottom: 6 }}>{b.titulo}</p>
            <p style={{ fontSize: "0.88rem", color: "var(--texto-tenue)" }}>{b.texto}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
