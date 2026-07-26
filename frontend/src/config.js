// En desarrollo local, VITE_API_URL queda vacío y las peticiones van a rutas
// relativas ("/api/..."), que Vite redirige al backend local (ver vite.config.js).
//
// En producción (Railway), define VITE_API_URL con la URL pública de tu
// servicio backend, por ejemplo: https://herreria-backend.up.railway.app
export const API_BASE = import.meta.env.VITE_API_URL || "";

// El backend guarda imagen_url como ruta relativa ("/uploads/archivo.jpg").
// Como frontend y backend viven en dominios distintos en producción, hay que
// anteponerle API_BASE para que el navegador la pida al dominio correcto
// (si no, intenta cargarla desde el propio dominio del frontend y falla).
export function urlImagen(rutaRelativa) {
  if (!rutaRelativa) return null;
  return `${API_BASE}${rutaRelativa}`;
}