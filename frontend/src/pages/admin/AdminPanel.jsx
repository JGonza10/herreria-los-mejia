import { Suspense, lazy, useState } from "react";
import LayoutPanel from "../../components/LayoutPanel.jsx";
import AdminCatalogo from "./AdminCatalogo.jsx";
import AdminCotizaciones from "./AdminCotizaciones.jsx";
import AdminPedidos from "./AdminPedidos.jsx";
import AdminUsuarios from "./AdminUsuarios.jsx";

// Carga perezosa: AdminEscalera trae Three.js (~600 KB). Si fuera un import
// normal, ese peso se sumaría al bundle principal del sitio público entero.
// Con lazy() solo se descarga cuando un admin realmente abre esta pestaña.
const AdminEscalera = lazy(() => import("./AdminEscalera.jsx"));

const TABS = [
  { id: "pedidos", etiqueta: "Pedidos", Componente: AdminPedidos },
  { id: "cotizaciones", etiqueta: "Cotizaciones", Componente: AdminCotizaciones },
  { id: "catalogo", etiqueta: "Catálogo", Componente: AdminCatalogo },
  { id: "equipo", etiqueta: "Equipo", Componente: AdminUsuarios },
  { id: "escalera", etiqueta: "Escalera", Componente: AdminEscalera },
];

export default function AdminPanel() {
  const [tab, setTab] = useState("pedidos");
  const Activo = TABS.find((t) => t.id === tab).Componente;

  return (
    <LayoutPanel titulo="Panel de administrador">
      <div style={{ display: "flex", gap: 8, marginBottom: 32, flexWrap: "wrap" }}>
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            style={{
              padding: "9px 18px",
              borderRadius: 999,
              border: `1px solid ${tab === t.id ? "var(--ascua-500)" : "var(--borde)"}`,
              background: tab === t.id ? "var(--ascua-500)" : "transparent",
              color: tab === t.id ? "#fff" : "var(--texto)",
              fontWeight: 600,
              fontSize: "0.9rem",
            }}
          >
            {t.etiqueta}
          </button>
        ))}
      </div>
      <Suspense fallback={<p style={{ color: "var(--texto-tenue)" }}>Cargando…</p>}>
        <Activo />
      </Suspense>
    </LayoutPanel>
  );
}
