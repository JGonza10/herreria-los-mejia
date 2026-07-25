import { API_BASE } from "./config.js";

const CLAVE_TOKEN = "token";

function headersAuth(extra = {}) {
  const token = localStorage.getItem(CLAVE_TOKEN);
  return token ? { ...extra, Authorization: `Bearer ${token}` } : extra;
}

async function manejarRespuesta(r) {
  const contentType = r.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await r.json() : null;
  if (!r.ok) {
    throw new Error((data && data.error) || `Error ${r.status}`);
  }
  return data;
}

export const api = {
  get: (ruta) =>
    fetch(`${API_BASE}${ruta}`, { headers: headersAuth() }).then(manejarRespuesta),

  post: (ruta, body) =>
    fetch(`${API_BASE}${ruta}`, {
      method: "POST",
      headers: headersAuth({ "Content-Type": "application/json" }),
      body: JSON.stringify(body),
    }).then(manejarRespuesta),

  put: (ruta, body) =>
    fetch(`${API_BASE}${ruta}`, {
      method: "PUT",
      headers: headersAuth({ "Content-Type": "application/json" }),
      body: JSON.stringify(body),
    }).then(manejarRespuesta),

  del: (ruta) =>
    fetch(`${API_BASE}${ruta}`, { method: "DELETE", headers: headersAuth() }).then(manejarRespuesta),

  /** Para form-data (subida de imágenes) */
  postForm: (ruta, formData) =>
    fetch(`${API_BASE}${ruta}`, { method: "POST", headers: headersAuth(), body: formData }).then(manejarRespuesta),

  putForm: (ruta, formData) =>
    fetch(`${API_BASE}${ruta}`, { method: "PUT", headers: headersAuth(), body: formData }).then(manejarRespuesta),
};
