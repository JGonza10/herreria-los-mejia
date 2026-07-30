// Alzado acotado en SVG (Fase 6) — sirve para confirmar medidas antes de
// fabricar. Comparte la misma convención geométrica que Pieza3D.jsx y que
// backend/dominio/despiece.py (separación de barrotes por defecto, marco
// perimetral): si el dibujo de pantalla y el de Pieza3D no coincidieran, se
// pierde la confianza en los dos.
const SEPARACION_BARROTES_DEFAULT_CM = 12;
const LIENZO_W = 520;
const LIENZO_H = 320;
const MARGEN = 44;

export default function Pieza2D({ spec, modoDibujo = "barrotes" }) {
  const { ancho_m: ancho, alto_m: alto } = spec.medidas;
  if (!ancho || !alto) return null;

  const escala = Math.min((LIENZO_W - MARGEN * 2) / ancho, (LIENZO_H - MARGEN * 2) / alto);
  const w = ancho * escala;
  const h = alto * escala;
  const x0 = (LIENZO_W - w) / 2;
  const y0 = MARGEN;

  return (
    <svg viewBox={`0 0 ${LIENZO_W} ${LIENZO_H + 30}`} style={{ width: "100%", height: "auto" }}>
      <ContenidoPieza modoDibujo={modoDibujo} spec={spec} x0={x0} y0={y0} w={w} h={h} />

      {/* cota de ancho */}
      <line x1={x0} y1={y0 + h + 18} x2={x0 + w} y2={y0 + h + 18} stroke="var(--texto-tenue)" strokeWidth="1" />
      <line x1={x0} y1={y0 + h + 14} x2={x0} y2={y0 + h + 22} stroke="var(--texto-tenue)" strokeWidth="1" />
      <line x1={x0 + w} y1={y0 + h + 14} x2={x0 + w} y2={y0 + h + 22} stroke="var(--texto-tenue)" strokeWidth="1" />
      <text x={x0 + w / 2} y={y0 + h + 34} textAnchor="middle" fontSize="11" fill="var(--texto-tenue)">
        {ancho.toFixed(2)} m
      </text>

      {/* cota de alto */}
      <line x1={x0 - 18} y1={y0} x2={x0 - 18} y2={y0 + h} stroke="var(--texto-tenue)" strokeWidth="1" />
      <line x1={x0 - 22} y1={y0} x2={x0 - 14} y2={y0} stroke="var(--texto-tenue)" strokeWidth="1" />
      <line x1={x0 - 22} y1={y0 + h} x2={x0 - 14} y2={y0 + h} stroke="var(--texto-tenue)" strokeWidth="1" />
      <text
        x={x0 - 26} y={y0 + h / 2}
        textAnchor="middle" fontSize="11" fill="var(--texto-tenue)"
        transform={`rotate(-90, ${x0 - 26}, ${y0 + h / 2})`}
      >
        {alto.toFixed(2)} m
      </text>
    </svg>
  );
}

function ContenidoPieza({ modoDibujo, spec, x0, y0, w, h }) {
  if (modoDibujo === "cancel") {
    const divisiones = spec.estructura?.divisiones_verticales || 0;
    const numPaneles = divisiones + 1;
    return (
      <>
        <rect x={x0} y={y0} width={w} height={h} fill="var(--vidrio-400)" opacity="0.25" stroke="var(--aluminio-400)" strokeWidth="2.5" />
        {Array.from({ length: divisiones }, (_, i) => {
          const x = x0 + (w / numPaneles) * (i + 1);
          return <line key={i} x1={x} y1={y0} x2={x} y2={y0 + h} stroke="var(--aluminio-400)" strokeWidth="2" />;
        })}
      </>
    );
  }

  if (modoDibujo === "vidrio") {
    return <rect x={x0} y={y0} width={w} height={h} fill="var(--vidrio-400)" opacity="0.3" stroke="var(--aluminio-400)" strokeWidth="2.5" />;
  }

  if (modoDibujo === "estructura") {
    // Barandal: pasamanos superior + postes, no un marco cerrado.
    const numPostes = Math.max(2, Math.round((spec.medidas.ancho_m || 1) / 1.0) + 1);
    return (
      <>
        <line x1={x0} y1={y0} x2={x0 + w} y2={y0} stroke="var(--texto)" strokeWidth="3" />
        {Array.from({ length: numPostes }, (_, i) => {
          const x = x0 + (w / (numPostes - 1)) * i;
          return <line key={i} x1={x} y1={y0} x2={x} y2={y0 + h} stroke="var(--texto)" strokeWidth="2.5" />;
        })}
      </>
    );
  }

  // "barrotes" (default): marco cerrado + barrotes verticales.
  const separacionCm = spec.estructura?.separacion_barrotes_cm || SEPARACION_BARROTES_DEFAULT_CM;
  const separacionM = separacionCm / 100;
  const numBarrotes = Math.max(0, Math.round((spec.medidas.ancho_m || 1) / separacionM) - 1);
  return (
    <>
      <rect x={x0} y={y0} width={w} height={h} fill="none" stroke="var(--texto)" strokeWidth="2.5" />
      {Array.from({ length: numBarrotes }, (_, i) => {
        const x = x0 + (w / (numBarrotes + 1)) * (i + 1);
        return <line key={i} x1={x} y1={y0} x2={x} y2={y0 + h} stroke="var(--ascua-500)" strokeWidth="1.5" />;
      })}
    </>
  );
}
