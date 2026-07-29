import { useEffect, useState } from "react";
import { api } from "../../api.js";
import { API_BASE } from "../../config.js";
import Escalera3D from "../../components/Escalera3D.jsx";

const TIPOS = [
  { id: "recta", etiqueta: "Recta" },
  { id: "l", etiqueta: "En L" },
  { id: "u", etiqueta: "En U" },
  { id: "caracol", etiqueta: "Caracol" },
];

const VACIO = {
  altura_total: "2.72",
  ancho: "0.90",
  uso: "vivienda",
  espacio_horizontal: "4.20",
  contrahuella_deseada: "",
  diametro_exterior: "1.40",
  diametro_poste: "0.12",
  angulo_giro_total: "360",
};

export default function AdminEscalera() {
  const [tipo, setTipo] = useState("recta");
  const [form, setForm] = useState(VACIO);
  const [resultado, setResultado] = useState(null);
  const [avisos, setAvisos] = useState([]);
  const [calculando, setCalculando] = useState(false);
  const [error, setError] = useState(null);

  const cambiar = (campo) => (e) => setForm((f) => ({ ...f, [campo]: e.target.value }));

  useEffect(() => {
    setResultado(null);
    setAvisos([]);
    setError(null);
  }, [tipo]);

  useEffect(() => {
    const body = construirCuerpo(tipo, form);
    if (!body) {
      setResultado(null);
      return;
    }
    setCalculando(true);
    setError(null);
    const timeout = setTimeout(() => {
      api
        .post("/api/escalera/calcular", body)
        .then((data) => {
          setResultado(data);
          setAvisos(data.avisos || []);
        })
        .catch((err) => {
          setResultado(null);
          setError(err.message);
        })
        .finally(() => setCalculando(false));
    }, 350);
    return () => clearTimeout(timeout);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tipo, form]);

  return (
    <div>
      <h2 style={{ fontSize: "1.6rem", marginBottom: 6 }}>Calculadora de escaleras</h2>
      <p style={{ fontSize: "0.85rem", color: "var(--texto-tenue)", marginBottom: 20 }}>
        Uso interno del taller — valida contra la Ley de Blondel y el Reglamento de Construcciones (CDMX). No sustituye una revisión estructural certificada.
      </p>

      <div style={{ display: "flex", gap: 10, marginBottom: 20, flexWrap: "wrap" }}>
        {TIPOS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTipo(t.id)}
            style={{
              padding: "8px 18px",
              borderRadius: 999,
              border: `1px solid ${tipo === t.id ? "var(--ascua-500)" : "var(--borde)"}`,
              background: tipo === t.id ? "var(--ascua-500)" : "transparent",
              color: tipo === t.id ? "#fff" : "var(--texto)",
              fontWeight: 600,
              fontSize: "0.85rem",
            }}
          >
            {t.etiqueta}
          </button>
        ))}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 20 }}>
        <FormularioEscalera tipo={tipo} form={form} cambiar={cambiar} />

        <div>
          {error && (
            <div style={avisoEstilo}>{error}</div>
          )}
          {avisos.map((a, i) => (
            <div key={i} style={avisoEstilo}>{a}</div>
          ))}

          {resultado && resultado.tipo === tipo && <TarjetasResultado tipo={tipo} resultado={resultado} />}
          {resultado && resultado.tipo === tipo && (
            <div style={{ border: "1px solid var(--borde)", borderRadius: "var(--radius-md)", padding: 16, background: "var(--fondo-elevado)" }}>
              <Escalera3D tipo={tipo} resultado={resultado} form={form} />
            </div>
          )}

          {resultado && resultado.tipo === tipo && (
            <div style={{ display: "flex", gap: 10, marginTop: 14 }}>
              <BotonDescarga tipo={tipo} form={form} ruta="/api/escalera/pdf" nombreArchivo={`escalera-${tipo}.pdf`} etiqueta="Descargar ficha en PDF" />
              <BotonDescarga tipo={tipo} form={form} ruta="/api/escalera/excel" nombreArchivo={`escalera-${tipo}.xlsx`} etiqueta="Descargar registro en Excel" />
            </div>
          )}

          {!resultado && !error && (
            <p style={{ color: "var(--texto-tenue)" }}>{calculando ? "Calculando…" : "Completa los datos para ver el resultado."}</p>
          )}
        </div>
      </div>
    </div>
  );
}

function construirCuerpo(tipo, form) {
  const alturaTotal = Number(form.altura_total);
  if (!alturaTotal || alturaTotal <= 0) return null;

  const base = {
    tipo,
    altura_total: alturaTotal,
    uso: form.uso,
  };
  if (form.contrahuella_deseada) base.contrahuella_deseada = Number(form.contrahuella_deseada);

  if (tipo === "caracol") {
    const diametroExterior = Number(form.diametro_exterior);
    if (!diametroExterior || diametroExterior <= 0) return null;
    base.diametro_exterior = diametroExterior;
    base.diametro_poste = Number(form.diametro_poste) || 0.10;
    base.angulo_giro_total = Number(form.angulo_giro_total) || 360;
    return base;
  }

  const ancho = Number(form.ancho);
  if (!ancho || ancho <= 0) return null;
  base.ancho = ancho;

  if (tipo === "recta" && form.espacio_horizontal) {
    base.espacio_horizontal = Number(form.espacio_horizontal);
  }
  return base;
}

function FormularioEscalera({ tipo, form, cambiar }) {
  return (
    <div style={{ border: "1px solid var(--borde)", borderRadius: "var(--radius-md)", padding: 18, background: "var(--fondo-elevado)", alignSelf: "start" }}>
      <Campo etiqueta="Altura total (m)" valor={form.altura_total} onChange={cambiar("altura_total")} />

      {tipo !== "caracol" && (
        <Campo etiqueta="Ancho de la escalera (m)" valor={form.ancho} onChange={cambiar("ancho")} />
      )}

      {tipo === "recta" && (
        <Campo etiqueta="Espacio horizontal disponible (m)" valor={form.espacio_horizontal} onChange={cambiar("espacio_horizontal")} />
      )}

      {tipo === "caracol" && (
        <>
          <Campo etiqueta="Diámetro exterior (m)" valor={form.diametro_exterior} onChange={cambiar("diametro_exterior")} />
          <Campo etiqueta="Diámetro del poste central (m)" valor={form.diametro_poste} onChange={cambiar("diametro_poste")} />
          <Campo etiqueta="Ángulo de giro total (°)" valor={form.angulo_giro_total} onChange={cambiar("angulo_giro_total")} />
        </>
      )}

      <Campo etiqueta="Contrahuella deseada (m, opcional)" valor={form.contrahuella_deseada} onChange={cambiar("contrahuella_deseada")} />

      {tipo !== "caracol" && (
        <label style={{ fontSize: "0.8rem", color: "var(--texto-tenue)", display: "block", marginBottom: 4 }}>
          Uso
          <select
            value={form.uso}
            onChange={cambiar("uso")}
            style={{ display: "block", width: "100%", marginTop: 4, padding: "8px 10px", borderRadius: 6, border: "1px solid var(--borde)", background: "var(--fondo)", color: "var(--texto)" }}
          >
            <option value="vivienda">Vivienda</option>
            <option value="servicio">Servicio</option>
          </select>
        </label>
      )}
    </div>
  );
}

function Campo({ etiqueta, valor, onChange }) {
  return (
    <label style={{ fontSize: "0.8rem", color: "var(--texto-tenue)", display: "block", marginBottom: 12 }}>
      {etiqueta}
      <input
        type="number"
        step="0.01"
        value={valor}
        onChange={onChange}
        style={{ display: "block", width: "100%", marginTop: 4, padding: "8px 10px", borderRadius: 6, border: "1px solid var(--borde)", background: "var(--fondo)", color: "var(--texto)" }}
      />
    </label>
  );
}

function TarjetasResultado({ tipo, resultado }) {
  const tarjetas = [];
  tarjetas.push({ valor: resultado.num_escalones, etiqueta: "escalones" });
  tarjetas.push({ valor: `${(resultado.contrahuella * 100).toFixed(1)} cm`, etiqueta: "contrahuella" });

  if (tipo === "caracol") {
    tarjetas.push({ valor: `${(resultado.huella_linea_paso * 100).toFixed(1)} cm`, etiqueta: "huella (línea de paso)" });
    tarjetas.push({ valor: `${resultado.angulo_por_escalon}°`, etiqueta: "ángulo / escalón" });
  } else {
    tarjetas.push({ valor: `${(resultado.huella * 100).toFixed(1)} cm`, etiqueta: "huella" });
    tarjetas.push({ valor: `${resultado.inclinacion_grados}°`, etiqueta: "inclinación" });
  }

  if (tipo === "l" || tipo === "u") {
    tarjetas.push({ valor: `${resultado.escalones_tramo1} / ${resultado.escalones_tramo2}`, etiqueta: "escalones tramo 1 / 2" });
    tarjetas.push({ valor: `${resultado.espacio_requerido_x} × ${resultado.espacio_requerido_y} m`, etiqueta: "espacio requerido" });
  }
  if (tipo === "recta") {
    tarjetas.push({ valor: `${resultado.longitud_horizontal} m`, etiqueta: "longitud horizontal" });
  }

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(110px, 1fr))", gap: 10, marginBottom: 16 }}>
      {tarjetas.map((t, i) => (
        <div key={i} style={{ border: "1px solid var(--borde)", borderRadius: "var(--radius-sm)", padding: 12, textAlign: "center", background: "var(--fondo-elevado)" }}>
          <p className="display" style={{ fontSize: "1.15rem", color: "var(--ascua-500)", margin: 0 }}>{t.valor}</p>
          <p style={{ fontSize: "0.72rem", color: "var(--texto-tenue)", margin: "4px 0 0" }}>{t.etiqueta}</p>
        </div>
      ))}
    </div>
  );
}

const avisoEstilo = {
  background: "var(--ascua-500)",
  opacity: 0.9,
  color: "#fff",
  padding: "10px 14px",
  borderRadius: 8,
  fontSize: "0.8rem",
  marginBottom: 10,
};

function BotonDescarga({ tipo, form, ruta, nombreArchivo, etiqueta }) {
  const [descargando, setDescargando] = useState(false);
  const [error, setError] = useState(null);

  const descargar = async () => {
    const body = construirCuerpo(tipo, form);
    if (!body) return;
    setDescargando(true);
    setError(null);
    try {
      const token = localStorage.getItem("token");
      const r = await fetch(`${API_BASE}${ruta}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(body),
      });
      if (!r.ok) {
        const data = await r.json().catch(() => null);
        throw new Error((data && data.error) || "No se pudo generar el archivo.");
      }
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = nombreArchivo;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message);
    } finally {
      setDescargando(false);
    }
  };

  return (
    <div>
      {error && <div style={avisoEstilo}>{error}</div>}
      <button
        onClick={descargar}
        disabled={descargando}
        style={{
          padding: "10px 20px",
          borderRadius: 6,
          border: "1px solid var(--borde)",
          background: "var(--fondo-elevado)",
          color: "var(--texto)",
          fontWeight: 600,
          fontSize: "0.85rem",
          cursor: descargando ? "default" : "pointer",
          opacity: descargando ? 0.6 : 1,
        }}
      >
        {descargando ? "Generando…" : etiqueta}
      </button>
    </div>
  );
}
