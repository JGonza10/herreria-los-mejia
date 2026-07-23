import { API_BASE } from "./config.js";

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
    fetch(`${API_BASE}${ruta}`, { credentials: "include" }).then(manejarRespuesta),

  post: (ruta, body) =>
    fetch(`${API_BASE}${ruta}`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(manejarRespuesta),

  put: (ruta, body) =>
    fetch(`${API_BASE}${ruta}`, {
      method: "PUT",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(manejarRespuesta),

  del: (ruta) =>
    fetch(`${API_BASE}${ruta}`, { method: "DELETE", credentials: "include" }).then(manejarRespuesta),

  /** Para form-data (subida de imágenes) */
  postForm: (ruta, formData) =>
    fetch(`${API_BASE}${ruta}`, { method: "POST", credentials: "include", body: formData }).then(manejarRespuesta),

  putForm: (ruta, formData) =>
    fetch(`${API_BASE}${ruta}`, { method: "PUT", credentials: "include", body: formData }).then(manejarRespuesta),
};
