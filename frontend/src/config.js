// En desarrollo local, VITE_API_URL queda vacío y las peticiones van a rutas
// relativas ("/api/..."), que Vite redirige al backend local (ver vite.config.js).
//
// En producción (Railway), define VITE_API_URL con la URL pública de tu
// servicio backend, por ejemplo: https://herreria-backend.up.railway.app
export const API_BASE = import.meta.env.VITE_API_URL || "";
