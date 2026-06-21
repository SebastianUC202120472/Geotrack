// Cliente HTTP del panel: URL base, token JWT y manejo de sesión.
// La URL base viene de VITE_API_URL (en Docker es "/api", servido por Nginx).

const API_URL = import.meta.env.VITE_API_URL;
const TOKEN_KEY = "admin_token";

export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const guardarToken = (token) => localStorage.setItem(TOKEN_KEY, token);
export const borrarToken = () => localStorage.removeItem(TOKEN_KEY);

// Núcleo de las peticiones: adjunta el token y, si caducó (401), cierra sesión.
async function request(ruta, { method = "GET", body, headers = {}, auth = true } = {}) {
  const opciones = { method, headers: { ...headers } };

  if (auth) {
    const token = getToken();
    if (token) opciones.headers.Authorization = `Bearer ${token}`;
  }

  // Si el body es FormData (subir Excel) dejamos que el navegador ponga el
  // Content-Type con su boundary; si es objeto, lo mandamos como JSON.
  if (body instanceof FormData) {
    opciones.body = body;
  } else if (body !== undefined) {
    opciones.headers["Content-Type"] = "application/json";
    opciones.body = JSON.stringify(body);
  }

  const respuesta = await fetch(`${API_URL}${ruta}`, opciones);

  // 401 (token inválido/expirado) o 403 (la cuenta no tiene permisos de admin):
  // cerramos sesión y mandamos a login para no quedar en un panel "colgado".
  if (respuesta.status === 401 || respuesta.status === 403) {
    borrarToken();
    if (window.location.pathname !== "/login") window.location.href = "/login";
    throw new Error(
      respuesta.status === 403
        ? "Tu cuenta no tiene permisos para el panel. Inicia sesión como administrador."
        : "Tu sesión expiró. Vuelve a iniciar sesión."
    );
  }

  // Intentamos leer el cuerpo (puede venir vacío en algunos POST).
  const texto = await respuesta.text();
  const datos = texto ? JSON.parse(texto) : null;

  if (!respuesta.ok) {
    const detalle = datos?.detail || datos?.message || "Ocurrió un error en el servidor";
    throw new Error(typeof detalle === "string" ? detalle : "Solicitud inválida");
  }

  return datos;
}

/* ============================================================
   AUTENTICACIÓN
============================================================ */

// Decodifica el payload de un JWT (base64url) para leer el rol sin librerías.
// Entrada: token (string JWT). Salida: objeto payload, o null si no se puede leer.
function leerPayload(token) {
  try {
    const base64 = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    return JSON.parse(decodeURIComponent(escape(atob(base64))));
  } catch {
    return null;
  }
}

// Login del panel (CUS-02). El backend usa OAuth2: 'username' y 'password' como
// formulario. Solo se permite el acceso a usuarios con rol 'admin' (la app móvil
// es para conductores), así que validamos el rol antes de guardar el token.
export const loginAdmin = async (correo, contrasena) => {
  const formulario = new URLSearchParams();
  formulario.append("username", correo);
  formulario.append("password", contrasena);

  const respuesta = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: formulario,
  });

  if (!respuesta.ok) throw new Error("Correo o contraseña incorrectos");

  const datos = await respuesta.json();

  const payload = leerPayload(datos.access_token);
  if (payload?.rol !== "admin") {
    throw new Error("Esta cuenta no tiene acceso al panel de administración.");
  }

  guardarToken(datos.access_token);
  return datos;
};

// Conductores: listar (con ficha + vehículo asignado) y registrar (cuenta + datos).
export const listarConductores = () => request("/conductores/");

export const crearConductor = (datos) =>
  request("/conductores/", { method: "POST", body: datos });

// Editar la ficha (nombre/teléfono/DNI) de un conductor.
export const actualizarConductor = (id, datos) =>
  request(`/conductores/${id}`, { method: "PATCH", body: datos });

// Eliminar (desactivar) un conductor; el backend preserva su historial.
export const eliminarConductor = (id) =>
  request(`/conductores/${id}`, { method: "DELETE" });

// CUS-04: el admin fija una nueva contraseña para un conductor que la olvidó.
export const restablecerContrasenaConductor = (id, contrasena) =>
  request(`/conductores/${id}/restablecer-contrasena`, { method: "POST", body: { contrasena } });

/* ============================================================
   CLIENTES CORPORATIVOS  (CUS-07 — administración)
============================================================ */

export const listarClientes = () => request("/clientes/");

export const crearCliente = (datos) =>
  request("/clientes/", { method: "POST", body: datos });

export const actualizarCliente = (id, datos) =>
  request(`/clientes/${id}`, { method: "PATCH", body: datos });

export const eliminarCliente = (id) =>
  request(`/clientes/${id}`, { method: "DELETE" });

/* ============================================================
   USUARIOS DEL PANEL  (CUS-03 — admin/jefe/almacén)
============================================================ */

export const listarUsuarios = () => request("/usuarios/");

export const crearUsuario = (datos) =>
  request("/usuarios/", { method: "POST", body: datos });

// Cambia rol y/o estado (activo) de un usuario del panel.
export const actualizarUsuario = (id, datos) =>
  request(`/usuarios/${id}`, { method: "PATCH", body: datos });

export const restablecerContrasenaUsuario = (id, contrasena) =>
  request(`/usuarios/${id}/restablecer-contrasena`, { method: "POST", body: { contrasena } });

/* ============================================================
   PARÁMETROS — Motivos de rechazo  (CUS-06)
============================================================ */

export const listarMotivos = () => request("/parametros/motivos");

export const crearMotivo = (texto) =>
  request("/parametros/motivos", { method: "POST", body: { texto } });

export const eliminarMotivo = (id) =>
  request(`/parametros/motivos/${id}`, { method: "DELETE" });

// Sube/reemplaza la foto de un conductor (multipart). La verá en su app móvil.
export const subirFotoConductor = (usuarioId, file) => {
  const formData = new FormData();
  formData.append("file", file);
  return request(`/conductores/${usuarioId}/foto`, { method: "POST", body: formData });
};

// Construye la URL absoluta de un recurso de /media a partir de la ruta del backend.
// Entrada: ruta (ej. "/media/conductores/cond_1.jpg?v=..."). Salida: URL o null.
export const urlMedia = (ruta) =>
  ruta ? `${API_URL.replace(/\/api\/?$/, "")}${ruta}` : null;

/* ============================================================
   REPORTES DE INCIDENCIA  (el conductor reporta fallas; el admin responde)
============================================================ */

// estado opcional: "ABIERTO" | "RESUELTO".
export const listarReportes = (estado) =>
  request(`/reportes/${estado ? `?estado=${encodeURIComponent(estado)}` : ""}`);

export const responderReporte = (id, datos) =>
  request(`/reportes/${id}/responder`, { method: "POST", body: datos });

/* ============================================================
   PEDIDOS  (Inbound — CUS-13 / CUS-15 / CUS-16)
============================================================ */

export const subirPedidosExcel = (archivo) => {
  const formData = new FormData();
  formData.append("file", archivo);
  return request("/pedidos/upload", { method: "POST", body: formData });
};

// El backend limita a 100 por defecto; pedimos un tope alto para poder filtrar
// y paginar del lado del cliente (suficiente para los volúmenes del MVP).
export const listarPedidos = (limit = 1000) => request(`/pedidos/?limit=${limit}`);

// Devuelve un pedido FALLIDO a PENDIENTE para reasignarlo.
export const reabrirPedido = (id) => request(`/pedidos/${id}/reabrir`, { method: "POST" });

// Devuelve { zonas_operativas: [{ distrito, total_pedidos }] }
export const listarZonas = () => request("/pedidos/zonas");

// CUS-17: pedidos con la geocodificación fallida (para resolver a mano).
export const listarPorUbicar = () => request("/pedidos/por-ubicar");

// CUS-17: geocodifica un texto de búsqueda para ubicar el pin en el mapa.
export const buscarDireccion = (q) => request(`/pedidos/buscar-direccion?q=${encodeURIComponent(q)}`);

// CUS-17: fija a mano la ubicación (lat/lng) de un pedido.
export const fijarUbicacionPedido = (id, datos) =>
  request(`/pedidos/${id}/ubicacion`, { method: "PATCH", body: datos });

// Seguimiento de repartos agregado por empresa cliente (no por ruta).
export const obtenerSeguimientoClientes = () => request("/dashboard/clientes");

// Posición en vivo de cada conductor con ruta activa + sus paradas pendientes.
export const obtenerUbicacionesFlota = () => request("/dashboard/flota/ubicaciones");

/* ============================================================
   VEHÍCULOS Y FLOTA  (gestión del admin)
============================================================ */

export const listarVehiculos = () => request("/vehiculos/");

export const crearVehiculo = (datos) =>
  request("/vehiculos/", { method: "POST", body: datos });

// CUS-08/09: edita un vehículo (marca/capacidades) o reasigna su conductor.
export const actualizarVehiculo = (id, datos) =>
  request(`/vehiculos/${id}`, { method: "PATCH", body: datos });

// CUS-08: da de baja (lógica) un vehículo.
export const eliminarVehiculo = (id) =>
  request(`/vehiculos/${id}`, { method: "DELETE" });

/* ============================================================
   ENRUTAMIENTO  (CUS-18)
============================================================ */

// conductor_id es el id del USUARIO conductor (no el del vehículo).
export const asignarBloque = ({ nombre_ruta, distrito, conductor_id }) =>
  request("/rutas/asignar-bloque", {
    method: "POST",
    body: { nombre_ruta, distrito, conductor_id },
  });

/* ============================================================
   MANIFIESTO  (CUS-21)
============================================================ */

// CUS-21: descarga el manifiesto de carga de una ruta en Excel (autenticado).
export async function descargarManifiesto(rutaId, nombre) {
  const token = getToken();
  const resp = await fetch(`${API_URL}/rutas/${rutaId}/manifiesto`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!resp.ok) throw new Error("No se pudo descargar el manifiesto");
  const blob = await resp.blob();
  const url = URL.createObjectURL(blob);
  const enlace = document.createElement("a");
  enlace.href = url;
  enlace.download = nombre || `manifiesto_${rutaId}.xlsx`;
  document.body.appendChild(enlace);
  enlace.click();
  enlace.remove();
  URL.revokeObjectURL(url);
}

/* ============================================================
   DASHBOARD / TRAZABILIDAD  (CUS-33 / CUS-35)
============================================================ */

export const obtenerResumen = () => request("/dashboard/resumen");

// Estado y avance de todas las rutas de la flota.
export const obtenerFlota = () => request("/dashboard/flota");

// Línea de tiempo completa de un paquete por su código (PD-001).
export const obtenerHistorial = (codigo) =>
  request(`/dashboard/pedidos/${encodeURIComponent(codigo)}/historial`);

// CUS-36: genera la liquidación (.xlsx) de un cliente y la registra en la BD.
// Devuelve { liquidacion_id, descarga_url, archivo, total_pedidos, ... }.
export const generarLiquidacion = ({ cliente, periodo_inicio, periodo_fin } = {}) =>
  request("/dashboard/clientes/liquidacion", {
    method: "POST",
    body: { cliente, periodo_inicio, periodo_fin },
  });

// Descarga la liquidación por el endpoint AUTENTICADO (lleva el token en el header:
// el .xlsx tiene datos personales y NO es público). Entrada: descarga_url (relativa a
// /api) y el nombre del archivo. Dispara la descarga en el navegador.
export async function descargarLiquidacion(descargaUrl, nombre) {
  const token = getToken();
  const resp = await fetch(`${API_URL}${descargaUrl}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!resp.ok) throw new Error("No se pudo descargar la liquidación");
  const blob = await resp.blob();
  const url = URL.createObjectURL(blob);
  const enlace = document.createElement("a");
  enlace.href = url;
  enlace.download = nombre || "liquidacion.xlsx";
  document.body.appendChild(enlace);
  enlace.click();
  enlace.remove();
  URL.revokeObjectURL(url);
}

/* ============================================================
   BANDEJA DE CORREOS  (solicitudes de recojo)
============================================================ */

export const listarConversaciones = () => request("/correos/conversaciones");

export const obtenerConversacion = (id) => request(`/correos/conversaciones/${id}`);

// Lee la bandeja real por IMAP e importa los correos nuevos.
export const sincronizarCorreos = () => request("/correos/sincronizar", { method: "POST" });

// Envía una respuesta por SMTP y la guarda en el hilo.
export const responderCorreo = (id, cuerpo) =>
  request(`/correos/conversaciones/${id}/responder`, { method: "POST", body: { cuerpo } });

export const marcarConversacion = (id, estado) =>
  request(`/correos/conversaciones/${id}/estado?estado=${encodeURIComponent(estado)}`, { method: "PATCH" });

/* ============================================================
   EFICIENCIA / COMBUSTIBLE (CUS-34)
============================================================ */

// CUS-34: eficiencia (km y ahorro de combustible) acumulada por cada conductor.
export const obtenerEficienciaConductores = () => request("/dashboard/eficiencia-conductores");

// Lee los parámetros de combustible. Salida: { consumo_l_100km, precio_soles_litro }.
export const obtenerCombustible = () => request("/parametros/combustible");

// Actualiza los parámetros de combustible. Entrada: consumo (L/100km) y precio (S//L).
export const actualizarCombustible = (consumo_l_100km, precio_soles_litro) =>
  request("/parametros/combustible", { method: "PUT", body: { consumo_l_100km, precio_soles_litro } });

/* ============================================================
   DECISIONES SOBRE PEDIDOS FALLIDOS (CUS-31)
============================================================ */

// Reprograma un pedido (vuelve a PENDIENTE). Entrada: id. Salida: { mensaje, codigo }.
export const reprogramarPedido = (id) => request(`/pedidos/${id}/reprogramar`, { method: "POST" });

// Cancela un pedido (estado CANCELADO). Entrada: id. Salida: { mensaje, codigo }.
export const cancelarPedido = (id) => request(`/pedidos/${id}/cancelar`, { method: "POST" });

/* ============================================================
   INCIDENCIAS — Auxilio mecánico (CUS-30)
============================================================ */

// Lista las incidencias. Entrada: estado opcional ("ABIERTA"|"RESUELTA"). Salida: array.
export const listarIncidencias = (estado) =>
  request(`/incidencias${estado ? `?estado=${encodeURIComponent(estado)}` : ""}`);

// Marca una incidencia como resuelta. Entrada: id y nota opcional. Salida: la incidencia.
export const resolverIncidencia = (id, nota) =>
  request(`/incidencias/${id}/resolver`, { method: "POST", body: { nota: nota ?? null } });

// Cuántas incidencias hay abiertas (aviso del sidebar/dashboard). Salida: { abiertas }.
export const contadorIncidencias = () => request("/incidencias/contador");

// Descarga un adjunto (ej. el Excel del recojo) y dispara la descarga en el
// navegador. Va con el token en el header, por eso no se usa un <a href> directo.
export async function descargarAdjunto(id, nombre) {
  const token = getToken();
  const resp = await fetch(`${API_URL}/correos/adjuntos/${id}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!resp.ok) throw new Error("No se pudo descargar el adjunto");
  const blob = await resp.blob();
  const url = URL.createObjectURL(blob);
  const enlace = document.createElement("a");
  enlace.href = url;
  enlace.download = nombre || "adjunto";
  document.body.appendChild(enlace);
  enlace.click();
  enlace.remove();
  URL.revokeObjectURL(url);
}
