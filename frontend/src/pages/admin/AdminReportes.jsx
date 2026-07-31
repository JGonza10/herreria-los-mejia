import { useEffect, useState } from "react";
import { api } from "../../api.js";
import { API_BASE } from "../../config.js";

export default function AdminReportes() {
  const [costoReal, setCostoReal] = useState([]);
  const [conversion, setConversion] = useState({ por_tipo: [], por_rango_precio: [] });
  const [horas, setHoras] = useState([]);

  useEffect(() => {
    api.get("/api/admin/reportes/costo-real").then(setCostoReal).catch(() => {});
    api.get("/api/admin/reportes/conversion").then(setConversion).catch(() => {});
    api.get("/api/admin/reportes/horas-por-m2").then(setHoras).catch(() => {});
  }, []);

  const descargarExcel = () => {
    const token = localStorage.getItem("token");
    fetch(`${API_BASE}/api/admin/reportes/excel`, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
      .then((r) => r.blob())
      .then((blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "reportes-los-mejia.xlsx";
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
      });
  };

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <h2 style={{ fontSize: "1.6rem" }}>Los números del negocio</h2>
        <button onClick={descargarExcel} className="boton boton-borde">Descargar todo en Excel</button>
      </div>

      <h3 style={estiloSeccion}>Costo real contra cotizado</h3>
      <p style={estiloAyuda}>El costo real depende de que se capture en cada proyecto (pestaña Pedidos). Sin capturar, aparece "—".</p>
      <div style={{ overflowX: "auto", marginBottom: 36 }}>
        <table style={tablaEstilo}>
          <thead>
            <tr>
              <th style={th}>Proyecto</th>
              <th style={th}>Estado</th>
              <th style={th}>Cotizado</th>
              <th style={th}>Costo real</th>
              <th style={th}>Margen real</th>
              <th style={th}>Margen %</th>
            </tr>
          </thead>
          <tbody>
            {costoReal.map((r) => (
              <tr key={r.proyecto_id}>
                <td style={td}>{r.titulo}</td>
                <td style={td}>{r.estado}</td>
                <td style={td}>${r.cotizado.toLocaleString("es-MX")}</td>
                <td style={td}>{r.costo_real_total != null ? `$${r.costo_real_total.toLocaleString("es-MX")}` : "—"}</td>
                <td style={td}>{r.margen_real != null ? `$${r.margen_real.toLocaleString("es-MX")}` : "—"}</td>
                <td style={td}>{r.margen_real_pct != null ? `${r.margen_real_pct}%` : "—"}</td>
              </tr>
            ))}
            {costoReal.length === 0 && <tr><td style={td} colSpan={6}>Sin proyectos todavía.</td></tr>}
          </tbody>
        </table>
      </div>

      <h3 style={estiloSeccion}>Tasa de conversión por tipo de trabajo</h3>
      <div style={{ overflowX: "auto", marginBottom: 24 }}>
        <table style={tablaEstilo}>
          <thead>
            <tr>
              <th style={th}>Tipo</th>
              <th style={th}>Total cotizado</th>
              <th style={th}>Aprobadas</th>
              <th style={th}>Conversión</th>
            </tr>
          </thead>
          <tbody>
            {conversion.por_tipo.map((r) => (
              <tr key={r.tipo}>
                <td style={td}>{r.tipo}</td>
                <td style={td}>{r.total}</td>
                <td style={td}>{r.aprobadas}</td>
                <td style={td}>{r.tasa_conversion_pct}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h3 style={estiloSeccion}>Tasa de conversión por rango de precio</h3>
      <div style={{ overflowX: "auto", marginBottom: 36 }}>
        <table style={tablaEstilo}>
          <thead>
            <tr>
              <th style={th}>Rango</th>
              <th style={th}>Total cotizado</th>
              <th style={th}>Aprobadas</th>
              <th style={th}>Conversión</th>
            </tr>
          </thead>
          <tbody>
            {conversion.por_rango_precio.map((r) => (
              <tr key={r.rango}>
                <td style={td}>${r.rango}</td>
                <td style={td}>{r.total}</td>
                <td style={td}>{r.aprobadas}</td>
                <td style={td}>{r.tasa_conversion_pct}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h3 style={estiloSeccion}>Horas por m²</h3>
      <p style={estiloAyuda}>Solo aparecen proyectos con horas registradas por el trabajador.</p>
      <div style={{ overflowX: "auto" }}>
        <table style={tablaEstilo}>
          <thead>
            <tr>
              <th style={th}>Proyecto</th>
              <th style={th}>Horas</th>
              <th style={th}>m²</th>
              <th style={th}>Horas/m²</th>
            </tr>
          </thead>
          <tbody>
            {horas.map((r) => (
              <tr key={r.proyecto_id}>
                <td style={td}>{r.titulo}</td>
                <td style={td}>{r.horas_totales}</td>
                <td style={td}>{r.m2_totales}</td>
                <td style={td}>{r.horas_por_m2 ?? "—"}</td>
              </tr>
            ))}
            {horas.length === 0 && <tr><td style={td} colSpan={4}>Sin horas registradas todavía.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const estiloSeccion = { fontSize: "1.1rem", marginBottom: 6, marginTop: 8 };
const estiloAyuda = { fontSize: "0.8rem", color: "var(--texto-tenue)", marginBottom: 10 };
const tablaEstilo = { width: "100%", borderCollapse: "collapse", fontSize: "0.85rem", minWidth: 480 };
const th = { textAlign: "left", padding: "8px 10px", borderBottom: "1px solid var(--borde)", color: "var(--texto-tenue)", fontSize: "0.78rem", textTransform: "uppercase" };
const td = { padding: "8px 10px", borderBottom: "1px solid var(--borde)" };
