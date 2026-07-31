import { useEffect, useState } from "react";
import { api } from "../../api.js";

const CONCEPTOS = ["material_base", "acabado", "perfil", "cristal", "canteado", "mano_obra"];
const UNIDADES = ["m2", "ml", "pza", "%"];

export default function AdminTarifas() {
  const [tarifas, setTarifas] = useState([]);
  const [seleccionada, setSeleccionada] = useState(null);
  const [precios, setPrecios] = useState([]);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState(null);
  const [mensaje, setMensaje] = useState(null);

  const [nombreNueva, setNombreNueva] = useState("");
  const [vigenteDesde, setVigenteDesde] = useState(() => new Date().toISOString().slice(0, 10));

  const [duplicando, setDuplicando] = useState(false);
  const [nombreDup, setNombreDup] = useState("");
  const [vigenteDup, setVigenteDup] = useState(() => new Date().toISOString().slice(0, 10));
  const [ajustePct, setAjustePct] = useState(0);

  const cargarTarifas = () => api.get("/api/admin/tarifas").then(setTarifas).catch(() => {});

  useEffect(() => { cargarTarifas(); }, []);

  const abrir = async (id) => {
    const data = await api.get(`/api/admin/tarifas/${id}`);
    setSeleccionada(data);
    setPrecios(data.precios.map((p) => ({ ...p })));
    setMensaje(null);
    setError(null);
  };

  const crear = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      const nueva = await api.post("/api/admin/tarifas", { nombre: nombreNueva, vigente_desde: vigenteDesde });
      setNombreNueva("");
      await cargarTarifas();
      abrir(nueva.id);
    } catch (err) {
      setError(err.message);
    }
  };

  const agregarFila = () => {
    setPrecios([...precios, { concepto: "material_base", clave: "", unidad: "m2", precio: 0 }]);
  };

  const cambiarFila = (i, campo, valor) => {
    const copia = [...precios];
    copia[i] = { ...copia[i], [campo]: valor };
    setPrecios(copia);
  };

  const quitarFila = (i) => setPrecios(precios.filter((_, idx) => idx !== i));

  const guardarPrecios = async () => {
    setGuardando(true);
    setError(null);
    setMensaje(null);
    try {
      const limpio = precios.map((p) => ({
        concepto: p.concepto, clave: p.clave, unidad: p.unidad, precio: Number(p.precio),
      }));
      await api.put(`/api/admin/tarifas/${seleccionada.id}/precios`, { precios: limpio });
      setMensaje("Precios guardados.");
      cargarTarifas();
    } catch (err) {
      setError(err.message);
    } finally {
      setGuardando(false);
    }
  };

  const activar = async (id) => {
    await api.post(`/api/admin/tarifas/${id}/activar`, {});
    cargarTarifas();
    if (seleccionada?.id === id) abrir(id);
  };

  const duplicar = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      const nueva = await api.post(`/api/admin/tarifas/${seleccionada.id}/duplicar`, {
        nombre: nombreDup, vigente_desde: vigenteDup, ajuste_pct: Number(ajustePct),
      });
      setDuplicando(false);
      setNombreDup("");
      setAjustePct(0);
      await cargarTarifas();
      abrir(nueva.id);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div>
      <h2 style={{ fontSize: "1.6rem", marginBottom: 6 }}>Tarifas de precios</h2>
      <p style={{ fontSize: "0.85rem", color: "var(--texto-tenue)", marginBottom: 20 }}>
        Un conjunto de precios con fecha de vigencia. Solo una puede estar activa a la vez — las cotizaciones nuevas usan la activa.
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "280px 1fr", gap: 24 }}>
        <div>
          <form onSubmit={crear} style={{ display: "grid", gap: 8, marginBottom: 20 }}>
            <input placeholder="Nombre (ej. Agosto 2026)" required value={nombreNueva} onChange={(e) => setNombreNueva(e.target.value)} style={inputEstilo} />
            <input type="date" required value={vigenteDesde} onChange={(e) => setVigenteDesde(e.target.value)} style={inputEstilo} />
            <button type="submit" className="boton boton-borde" style={{ justifyContent: "center" }}>+ Nueva tarifa vacía</button>
          </form>

          <div style={{ display: "grid", gap: 8 }}>
            {tarifas.map((t) => (
              <button
                key={t.id}
                onClick={() => abrir(t.id)}
                style={{
                  textAlign: "left", padding: "10px 12px", borderRadius: "var(--radius-sm)",
                  border: `1px solid ${seleccionada?.id === t.id ? "var(--ascua-500)" : "var(--borde)"}`,
                  background: "var(--fondo-elevado)", color: "var(--texto)", cursor: "pointer",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ fontWeight: 600 }}>{t.nombre}</span>
                  {t.activa && <span style={{ fontSize: "0.72rem", color: "#4caf6d", fontWeight: 700 }}>ACTIVA</span>}
                </div>
                <span style={{ fontSize: "0.78rem", color: "var(--texto-tenue)" }}>Vigente desde {t.vigente_desde}</span>
              </button>
            ))}
          </div>
        </div>

        <div>
          {!seleccionada && <p style={{ color: "var(--texto-tenue)" }}>Selecciona o crea una tarifa para editar sus precios.</p>}

          {seleccionada && (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                <h3 style={{ fontSize: "1.2rem" }}>{seleccionada.nombre}</h3>
                <div style={{ display: "flex", gap: 8 }}>
                  {!seleccionada.activa && (
                    <button onClick={() => activar(seleccionada.id)} className="boton boton-ascua">Activar</button>
                  )}
                  <button onClick={() => setDuplicando(!duplicando)} className="boton boton-borde">Duplicar…</button>
                </div>
              </div>

              {duplicando && (
                <form onSubmit={duplicar} style={{ display: "flex", gap: 8, marginBottom: 20, flexWrap: "wrap", alignItems: "center", background: "var(--fondo-sutil)", padding: 14, borderRadius: "var(--radius-sm)" }}>
                  <input placeholder="Nombre nueva tarifa" required value={nombreDup} onChange={(e) => setNombreDup(e.target.value)} style={{ ...inputEstilo, width: 180 }} />
                  <input type="date" required value={vigenteDup} onChange={(e) => setVigenteDup(e.target.value)} style={{ ...inputEstilo, width: 150 }} />
                  <label style={{ fontSize: "0.82rem", color: "var(--texto-tenue)" }}>
                    Ajuste %:
                    <input type="number" step="0.1" value={ajustePct} onChange={(e) => setAjustePct(e.target.value)} style={{ ...inputEstilo, width: 70, marginLeft: 6 }} />
                  </label>
                  <button type="submit" className="boton boton-ascua">Copiar precios y crear</button>
                </form>
              )}

              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.88rem" }}>
                <thead>
                  <tr style={{ textAlign: "left", borderBottom: "1px solid var(--borde)" }}>
                    <th style={celdaEncabezado}>Concepto</th>
                    <th style={celdaEncabezado}>Clave</th>
                    <th style={celdaEncabezado}>Unidad</th>
                    <th style={celdaEncabezado}>Precio</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {precios.map((p, i) => (
                    <tr key={i} style={{ borderBottom: "1px solid var(--borde)" }}>
                      <td style={celdaFila}>
                        <select value={p.concepto} onChange={(e) => cambiarFila(i, "concepto", e.target.value)} style={inputTabla}>
                          {CONCEPTOS.map((c) => <option key={c} value={c}>{c}</option>)}
                        </select>
                      </td>
                      <td style={celdaFila}>
                        <input value={p.clave} onChange={(e) => cambiarFila(i, "clave", e.target.value)} placeholder="hierro, aluminio…" style={inputTabla} />
                      </td>
                      <td style={celdaFila}>
                        <select value={p.unidad} onChange={(e) => cambiarFila(i, "unidad", e.target.value)} style={inputTabla}>
                          {UNIDADES.map((u) => <option key={u} value={u}>{u}</option>)}
                        </select>
                      </td>
                      <td style={celdaFila}>
                        <input type="number" step="0.01" value={p.precio} onChange={(e) => cambiarFila(i, "precio", e.target.value)} style={{ ...inputTabla, width: 100 }} />
                      </td>
                      <td style={celdaFila}>
                        <button onClick={() => quitarFila(i)} style={{ background: "none", border: "none", color: "var(--ascua-400)", cursor: "pointer" }}>×</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div style={{ display: "flex", gap: 10, marginTop: 14, alignItems: "center" }}>
                <button onClick={agregarFila} className="boton boton-borde">+ Agregar precio</button>
                <button onClick={guardarPrecios} className="boton boton-ascua" disabled={guardando}>
                  {guardando ? "Guardando…" : "Guardar precios"}
                </button>
                {mensaje && <span style={{ color: "#4caf6d", fontSize: "0.85rem" }}>{mensaje}</span>}
                {error && <span style={{ color: "var(--ascua-400)", fontSize: "0.85rem" }}>{error}</span>}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const inputEstilo = {
  padding: "8px 10px", borderRadius: "var(--radius-sm)", border: "1px solid var(--borde)",
  background: "var(--fondo)", color: "var(--texto)", fontSize: "0.88rem",
};
const inputTabla = { ...inputEstilo, padding: "5px 6px", fontSize: "0.82rem", width: "100%" };
const celdaEncabezado = { padding: "6px 8px", fontSize: "0.78rem", color: "var(--texto-tenue)", textTransform: "uppercase" };
const celdaFila = { padding: "5px 8px" };
