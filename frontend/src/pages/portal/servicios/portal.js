// Cliente HTTP del portal público. Base /api (proxy Nginx). El token del portal
// se pasa por parámetro y vive en memoria del componente (no en localStorage).

const BASE = "/api/portal";

// pedir: hace un fetch JSON y normaliza el error como { status, data }.
async function pedir(url, opciones = {}) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(opciones.headers || {}) },
    ...opciones,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) return Promise.reject({ status: res.status, data });
  return data;
}

// --- Persona natural ---
export const buscarPedido = (codigo) =>
  pedir(`${BASE}/pedidos/${encodeURIComponent(codigo)}/buscar`, { method: "POST" });

export const verificarPedido = (codigo, dni) =>
  pedir(`${BASE}/pedidos/${encodeURIComponent(codigo)}/verificar`, {
    method: "POST",
    body: JSON.stringify({ dni }),
  });

export const detallePedido = (codigo, token) =>
  pedir(`${BASE}/pedidos/${encodeURIComponent(codigo)}`, {
    headers: { Authorization: `Bearer ${token}` },
  });

export const reprogramar = (codigo, franja, token) =>
  pedir(`${BASE}/pedidos/${encodeURIComponent(codigo)}/reprogramar`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ franja }),
  });

export const urlPod = (codigo) => `${BASE}/pedidos/${encodeURIComponent(codigo)}/pod`;

// --- Empresa ---
export const empresaLogin = (codigoAcceso, clave) =>
  pedir(`${BASE}/empresa/login`, {
    method: "POST",
    body: JSON.stringify({ codigoAcceso, clave }),
  });

export const empresaVerificar = (codigoAcceso, otp) =>
  pedir(`${BASE}/empresa/verificar`, {
    method: "POST",
    body: JSON.stringify({ codigoAcceso, otp }),
  });

// Pedidos de la empresa en una fecha ("AAAA-MM-DD"; vacia = hoy). Recibe token y fecha.
export const empresaPedidos = (token, fecha) =>
  pedir(`${BASE}/empresa/pedidos${fecha ? `?fecha=${encodeURIComponent(fecha)}` : ""}`, {
    headers: { Authorization: `Bearer ${token}` },
  });

// Descarga en Excel los pedidos de la empresa en una fecha y lo guarda en el equipo.
// Recibe token y fecha ("AAAA-MM-DD"). Rechaza con { status, data } como pedir().
export async function descargarExcelEmpresa(token, fecha) {
  const res = await fetch(`${BASE}/empresa/pedidos/excel?fecha=${encodeURIComponent(fecha)}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    return Promise.reject({ status: res.status, data });
  }
  const blob = await res.blob();
  const nombre = /filename="([^"]+)"/.exec(res.headers.get("Content-Disposition") || "")?.[1] || `pedidos_${fecha}.xlsx`;
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = nombre;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

// --- Ayuda de la demostración (vacía si el backend no está en modo demo) ---
export const ayudaDemo = () => pedir(`${BASE}/demo`);

// --- Landing (estadísticas públicas agregadas, sin datos personales) ---
export const estadisticasPublicas = () => pedir(`${BASE}/estadisticas`);

// --- Formularios landing ---
export const enviarContacto = (datos) =>
  pedir(`${BASE}/contacto`, { method: "POST", body: JSON.stringify(datos) });

export const enviarReclamo = (datos) =>
  pedir(`${BASE}/reclamos`, { method: "POST", body: JSON.stringify(datos) });
