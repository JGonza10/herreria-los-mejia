import { useEffect, useState } from "react";
import { api } from "../../api.js";

const VACIO = { id: null, nombre: "", material: "hierro", descripcion: "", precio_referencia_m2: "", destacado: false };

export default function AdminCatalogo() {
  const [productos, setProductos] = useState([]);
  const [form, setForm] = useState(VACIO);
  const [archivo, setArchivo] = useState(null);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState(null);
  const [errorCarga, setErrorCarga] = useState(null);

  const cargar = () =>
    api.get("/api/admin/productos")
      .then((data) => { setProductos(data); setErrorCarga(null); })
      .catch((err) => setErrorCarga(err.message));

  useEffect(() => { cargar(); }, []);

  const editar = (producto) => {
    setForm(producto);
    setArchivo(null);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const limpiar = () => {
    setForm(VACIO);
    setArchivo(null);
  };

  const guardar = async (e) => {
    e.preventDefault();
    setGuardando(true);
    setError(null);
    try {
      const datos = new FormData();
      datos.append("nombre", form.nombre);
      datos.append("material", form.material);
      datos.append("descripcion", form.descripcion || "");
      datos.append("precio_referencia_m2", form.precio_referencia_m2);
      datos.append("destacado", String(!!form.destacado));
      if (archivo) datos.append("imagen", archivo);

      if (form.id) {
        await api.putForm(`/api/admin/productos/${form.id}`, datos);
      } else {
        await api.postForm("/api/admin/productos", datos);
      }
      limpiar();
      cargar();
    } catch (err) {
      setError(err.message);
    } finally {
      setGuardando(false);
    }
  };

  const eliminar = async (id) => {
    if (!confirm("¿Eliminar este producto del catálogo?")) return;
    await api.del(`/api/admin/productos/${id}`);
    cargar();
  };

  return (
    <div>
      <h2 style={{ fontSize: "1.6rem", marginBottom: 18 }}>{form.id ? "Editar producto" : "Nuevo producto"}</h2>

      <form onSubmit={guardar} style={{ display: "grid", gap: 14, maxWidth: 480, marginBottom: 40 }}>
        <input placeholder="Nombre" required value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} style={inputEstilo} />

        <select value={form.material} onChange={(e) => setForm({ ...form, material: e.target.value })} style={inputEstilo}>
          <option value="hierro">Hierro</option>
          <option value="aluminio">Aluminio</option>
          <option value="vidrio">Vidrio</option>
        </select>

        <textarea placeholder="Descripción" rows={3} value={form.descripcion || ""} onChange={(e) => setForm({ ...form, descripcion: e.target.value })} style={inputEstilo} />

        <input type="number" step="0.01" placeholder="Precio referencia por m²" required value={form.precio_referencia_m2} onChange={(e) => setForm({ ...form, precio_referencia_m2: e.target.value })} style={inputEstilo} />

        <label style={{ fontSize: "0.85rem", color: "var(--texto-tenue)" }}>
          Imagen {form.imagen_url && "(sube una nueva para reemplazarla)"}
        </label>
        <input type="file" accept="image/png,image/jpeg,image/webp" onChange={(e) => setArchivo(e.target.files[0])} />

        <label style={{ display: "flex", gap: 8, alignItems: "center", fontSize: "0.9rem" }}>
          <input type="checkbox" checked={!!form.destacado} onChange={(e) => setForm({ ...form, destacado: e.target.checked })} />
          Destacado en el catálogo
        </label>

        {error && <p style={{ color: "var(--ascua-400)" }}>{error}</p>}

        <div style={{ display: "flex", gap: 12 }}>
          <button type="submit" className="boton boton-ascua" disabled={guardando}>
            {guardando ? "Guardando…" : form.id ? "Guardar cambios" : "Agregar producto"}
          </button>
          {form.id && <button type="button" onClick={limpiar} className="boton boton-borde">Cancelar</button>}
        </div>
      </form>

      <h2 style={{ fontSize: "1.6rem", marginBottom: 18 }}>Productos ({productos.length})</h2>
      {errorCarga && <p style={{ color: "var(--ascua-400)", marginBottom: 14 }}>{errorCarga}</p>}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: 16 }}>
        {productos.map((p) => (
          <div key={p.id} style={{ border: "1px solid var(--borde)", borderRadius: "var(--radius-md)", overflow: "hidden", background: "var(--fondo-elevado)" }}>
            {p.imagen_url ? (
              <img src={p.imagen_url} alt={p.nombre} style={{ width: "100%", height: 120, objectFit: "cover" }} />
            ) : (
              <div style={{ height: 120, background: "var(--fondo-sutil)" }} />
            )}
            <div style={{ padding: 14 }}>
              <p style={{ fontWeight: 600 }}>{p.nombre}</p>
              <p style={{ fontSize: "0.82rem", color: "var(--texto-tenue)" }}>{p.material} · ${p.precio_referencia_m2}/m²</p>
              <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
                <button onClick={() => editar(p)} style={botonChicoEstilo}>Editar</button>
                <button onClick={() => eliminar(p.id)} style={{ ...botonChicoEstilo, color: "var(--ascua-400)" }}>Eliminar</button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

const inputEstilo = {
  width: "100%",
  padding: "10px 12px",
  borderRadius: "var(--radius-sm)",
  border: "1px solid var(--borde)",
  background: "var(--fondo)",
  color: "var(--texto)",
  fontSize: "0.95rem",
};

const botonChicoEstilo = {
  background: "none",
  border: "1px solid var(--borde)",
  borderRadius: "var(--radius-sm)",
  padding: "5px 10px",
  fontSize: "0.8rem",
  color: "var(--texto)",
};
