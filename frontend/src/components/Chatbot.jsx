import { useState, useRef, useEffect } from "react";
import { API_BASE } from "../config.js";

export default function Chatbot() {
  const [abierto, setAbierto] = useState(false);
  const [mensajes, setMensajes] = useState([
    { role: "assistant", content: "¡Hola! Soy el asistente de Los Mejía. ¿En qué proyecto de hierro, aluminio o vidrio te puedo ayudar hoy?" },
  ]);
  const [texto, setTexto] = useState("");
  const [enviando, setEnviando] = useState(false);
  const finRef = useRef(null);

  useEffect(() => {
    finRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [mensajes, abierto]);

  const enviar = async (e) => {
    e.preventDefault();
    const contenido = texto.trim();
    if (!contenido || enviando) return;

    const nuevoHistorial = [...mensajes, { role: "user", content: contenido }];
    setMensajes(nuevoHistorial);
    setTexto("");
    setEnviando(true);

    try {
      const r = await fetch(`${API_BASE}/api/chatbot/mensaje`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ historial: nuevoHistorial }),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.error || "No se pudo obtener respuesta.");
      setMensajes([...nuevoHistorial, { role: "assistant", content: data.respuesta }]);
    } catch (err) {
      setMensajes([...nuevoHistorial, { role: "assistant", content: `⚠ ${err.message}` }]);
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div style={{ position: "fixed", right: 24, bottom: 24, zIndex: 50 }}>
      {abierto && (
        <div
          style={{
            width: 320,
            maxHeight: 420,
            display: "flex",
            flexDirection: "column",
            background: "var(--hierro-800)",
            border: "1px solid var(--ceniza-700)",
            borderRadius: "var(--radius-md)",
            marginBottom: 12,
            overflow: "hidden",
            boxShadow: "0 12px 30px rgba(0,0,0,0.4)",
          }}
        >
          <div
            style={{
              padding: "12px 16px",
              borderBottom: "1px solid var(--ceniza-700)",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <span className="display" style={{ fontSize: "1rem" }}>Los Mejía · Chat</span>
            <button
              onClick={() => setAbierto(false)}
              aria-label="Cerrar chat"
              style={{ background: "none", border: "none", color: "var(--aluminio-300)", fontSize: "1.1rem" }}
            >
              ✕
            </button>
          </div>

          <div style={{ flex: 1, overflowY: "auto", padding: 14, display: "flex", flexDirection: "column", gap: 10 }}>
            {mensajes.map((m, i) => (
              <div
                key={i}
                style={{
                  alignSelf: m.role === "user" ? "flex-end" : "flex-start",
                  background: m.role === "user" ? "var(--ascua-500)" : "var(--hierro-950)",
                  border: m.role === "user" ? "none" : "1px solid var(--ceniza-700)",
                  color: "var(--hueso-100)",
                  padding: "8px 12px",
                  borderRadius: "var(--radius-sm)",
                  fontSize: "0.88rem",
                  maxWidth: "85%",
                }}
              >
                {m.content}
              </div>
            ))}
            {enviando && <div style={{ color: "var(--ceniza-500)", fontSize: "0.82rem" }}>escribiendo…</div>}
            <div ref={finRef} />
          </div>

          <form onSubmit={enviar} style={{ display: "flex", borderTop: "1px solid var(--ceniza-700)" }}>
            <input
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
              placeholder="Escribe tu mensaje…"
              style={{
                flex: 1,
                border: "none",
                background: "var(--hierro-950)",
                color: "var(--hueso-100)",
                padding: "12px 14px",
                fontSize: "0.9rem",
              }}
            />
            <button
              type="submit"
              disabled={enviando}
              style={{ background: "var(--ascua-500)", border: "none", color: "var(--hueso-100)", padding: "0 18px", fontWeight: 600 }}
            >
              Enviar
            </button>
          </form>
        </div>
      )}

      <button
        onClick={() => setAbierto(!abierto)}
        aria-label={abierto ? "Cerrar chat" : "Abrir chat con Los Mejía"}
        style={{
          width: 58,
          height: 58,
          borderRadius: "50%",
          background: "var(--ascua-500)",
          border: "3px solid var(--hierro-950)",
          boxShadow: "0 6px 18px rgba(0,0,0,0.45)",
          color: "var(--hueso-100)",
          fontSize: "1.4rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {abierto ? "✕" : "💬"}
      </button>
    </div>
  );
}
