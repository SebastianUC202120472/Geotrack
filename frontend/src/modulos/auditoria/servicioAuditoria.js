import { getToken, borrarToken } from "../../services/api";

const BASE = "/api/auditoria";

async function peticion(ruta, { method = "GET", body } = {}) {
  const token = getToken();
  const headers = {};
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body !== undefined) headers["Content-Type"] = "application/json";

  const resp = await fetch(`${BASE}${ruta}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (resp.status === 401) {
    borrarToken();
    if (window.location.pathname !== "/panel/login") window.location.href = "/panel/login";
    throw new Error("Tu sesión expiró. Vuelve a iniciar sesión.");
  }

  const texto = await resp.text();
  let datos = null;
  if (texto) {
    try {
      datos = JSON.parse(texto);
    } catch {
      datos = null;
    }
  }
  if (!resp.ok) {
    const detalle = datos?.detail || `Error del servidor (${resp.status})`;
    throw new Error(typeof detalle === "string" ? detalle : "Solicitud inválida");
  }
  return datos;
}

export async function obtenerEstadoAuditoria() {
  try {
    const resp = await fetch(`${BASE}/salud`, { signal: AbortSignal.timeout(4000) });
    if (!resp.ok) return { activo: false };
    return await resp.json();
  } catch {
    return { activo: false };
  }
}

export function listarEvidencias({ semaforo, estadoRevision, pedidoCodigo, soloConReclamo } = {}) {
  const params = new URLSearchParams();
  if (semaforo) params.set("semaforo", semaforo);
  if (estadoRevision) params.set("estado_revision", estadoRevision);
  if (pedidoCodigo?.trim()) params.set("pedido_codigo", pedidoCodigo.trim());
  if (soloConReclamo) params.set("solo_con_reclamo", "true");
  const qs = params.toString();
  return peticion(`/evidencias${qs ? `?${qs}` : ""}`);
}

export function obtenerDetalleEvidencia(id) {
  return peticion(`/evidencias/${id}`);
}

export async function obtenerUrlImagenEvidencia(id) {
  const token = getToken();
  const resp = await fetch(`${BASE}/evidencias/${id}/imagen`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!resp.ok) throw new Error("No se pudo cargar la fotografía de evidencia");
  const blob = await resp.blob();
  return URL.createObjectURL(blob);
}

export function registrarDictamen(id, dictamen, motivo) {
  return peticion(`/evidencias/${id}/dictamen`, {
    method: "POST",
    body: { dictamen, motivo: motivo || null },
  });
}

export function obtenerMetricasAuditoria() {
  return peticion("/metricas");
}

export function sincronizarAuditoriaAhora() {
  return peticion("/sincronizar", { method: "POST" });
}

export function sembrarDemoAuditoria() {
  return peticion("/demo", { method: "POST" });
}
