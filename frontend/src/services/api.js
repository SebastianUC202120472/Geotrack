// Cliente HTTP del panel. URL base desde VITE_API_URL.

const API_URL = import.meta.env.VITE_API_URL;
const TOKEN_KEY = "admin_token";

export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const guardarToken = (token) => localStorage.setItem(TOKEN_KEY, token);
export const borrarToken = () => localStorage.removeItem(TOKEN_KEY);

// Envia una peticion autenticada. Cierra sesion si recibe 401.
async function request(ruta, { method = "GET", body, headers = {}, auth = true } = {}) {
  const opciones = { method, headers: { ...headers } };

  if (auth) {
    const token = getToken();
    if (token) opciones.headers.Authorization = `Bearer ${token}`;
  }

  if (body instanceof FormData) {
    opciones.body = body;
  } else if (body !== undefined) {
    opciones.headers["Content-Type"] = "application/json";
    opciones.body = JSON.stringify(body);
  }

  const respuesta = await fetch(`${API_URL}${ruta}`, opciones);

  if (respuesta.status === 401) {
    borrarToken();
    if (window.location.pathname !== "/login") window.location.href = "/login";
    throw new Error("Tu sesión expiró. Vuelve a iniciar sesión.");
  }

  const texto = await respuesta.text();
  const datos = texto ? JSON.parse(texto) : null;

  if (!respuesta.ok) {
    const detalle = datos?.detail || datos?.message || "Ocurrió un error en el servidor";
    throw new Error(typeof detalle === "string" ? detalle : "Solicitud inválida");
  }

  return datos;
}

// Decodifica el payload de un JWT. Recibe token (string).
function leerPayload(token) {
  try {
    const base64 = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/");
    return JSON.parse(decodeURIComponent(escape(atob(base64))));
  } catch {
    return null;
  }
}

// Login del panel. Valida rol (admin/almacen) antes de guardar el token. Recibe correo y contrasena.
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
  const ROLES_PANEL = ["admin", "almacen"];
  if (!ROLES_PANEL.includes(payload?.rol)) {
    throw new Error("Esta cuenta no tiene acceso al panel.");
  }

  guardarToken(datos.access_token);
  return datos;
};

// Lee el rol del JWT. Recibe token (string).
export const leerRol = (token) => leerPayload(token)?.rol ?? null;

export const listarConductores = () => request("/conductores/");

export const crearConductor = (datos) =>
  request("/conductores/", { method: "POST", body: datos });

// Edita la ficha de un conductor. Recibe id y datos.
export const actualizarConductor = (id, datos) =>
  request(`/conductores/${id}`, { method: "PATCH", body: datos });

// Desactiva un conductor (soft-delete). Recibe id.
export const eliminarConductor = (id) =>
  request(`/conductores/${id}`, { method: "DELETE" });

// Restablece la contrasena de un conductor. Recibe id y contrasena.
export const restablecerContrasenaConductor = (id, contrasena) =>
  request(`/conductores/${id}/restablecer-contrasena`, { method: "POST", body: { contrasena } });

export const listarClientes = () => request("/clientes/");

export const crearCliente = (datos) =>
  request("/clientes/", { method: "POST", body: datos });

export const actualizarCliente = (id, datos) =>
  request(`/clientes/${id}`, { method: "PATCH", body: datos });

export const eliminarCliente = (id) =>
  request(`/clientes/${id}`, { method: "DELETE" });

export const listarUsuarios = () => request("/usuarios/");

export const obtenerMiPerfil = () => request("/usuarios/yo");

export const crearUsuario = (datos) =>
  request("/usuarios/", { method: "POST", body: datos });

// Actualiza rol o estado de un usuario del panel. Recibe id y datos.
export const actualizarUsuario = (id, datos) =>
  request(`/usuarios/${id}`, { method: "PATCH", body: datos });

export const restablecerContrasenaUsuario = (id, contrasena) =>
  request(`/usuarios/${id}/restablecer-contrasena`, { method: "POST", body: { contrasena } });

export const listarMotivos = () => request("/parametros/motivos");

export const crearMotivo = (texto) =>
  request("/parametros/motivos", { method: "POST", body: { texto } });

export const eliminarMotivo = (id) =>
  request(`/parametros/motivos/${id}`, { method: "DELETE" });

// Sube la foto de un conductor. Recibe usuarioId y file.
export const subirFotoConductor = (usuarioId, file) => {
  const formData = new FormData();
  formData.append("file", file);
  return request(`/conductores/${usuarioId}/foto`, { method: "POST", body: formData });
};

// Construye la URL absoluta de un recurso /media. Recibe ruta relativa.
export const urlMedia = (ruta) =>
  ruta ? `${API_URL.replace(/\/api\/?$/, "")}${ruta}` : null;

// Lista reportes de incidencia. Recibe estado opcional ("ABIERTO"|"RESUELTO").
export const listarReportes = (estado) =>
  request(`/reportes/${estado ? `?estado=${encodeURIComponent(estado)}` : ""}`);

export const responderReporte = (id, datos) =>
  request(`/reportes/${id}/responder`, { method: "POST", body: datos });

export const listarPedidos = (limit = 1000) => request(`/pedidos/?limit=${limit}`);

export const listarZonas = () => request("/pedidos/zonas");

// Lista pedidos sin geocodificacion valida (para ubicar a mano).
export const listarPorUbicar = () => request("/pedidos/por-ubicar");

// Geocodifica un texto de busqueda. Recibe q (string).
export const buscarDireccion = (q) => request(`/pedidos/buscar-direccion?q=${encodeURIComponent(q)}`);

// Fija la ubicacion (lat/lng) de un pedido. Recibe id y datos.
export const fijarUbicacionPedido = (id, datos) =>
  request(`/pedidos/${id}/ubicacion`, { method: "PATCH", body: datos });

export const obtenerSeguimientoClientes = () => request("/dashboard/clientes");

export const obtenerUbicacionesFlota = () => request("/dashboard/flota/ubicaciones");

export const obtenerUbicacionesRecojo = () => request("/almacen/flota/ubicaciones-recojo");

export const listarVehiculos = () => request("/vehiculos/");

export const crearVehiculo = (datos) =>
  request("/vehiculos/", { method: "POST", body: datos });

// Edita un vehiculo o reasigna su conductor. Recibe id y datos.
export const actualizarVehiculo = (id, datos) =>
  request(`/vehiculos/${id}`, { method: "PATCH", body: datos });

// Da de baja (logica) un vehiculo. Recibe id.
export const eliminarVehiculo = (id) =>
  request(`/vehiculos/${id}`, { method: "DELETE" });

// Asigna un bloque de pedidos a un conductor. Recibe nombre_ruta, distrito y conductor_id.
export const asignarBloque = ({ nombre_ruta, distrito, conductor_id }) =>
  request("/rutas/asignar-bloque", {
    method: "POST",
    body: { nombre_ruta, distrito, conductor_id },
  });

// Descarga el manifiesto de una ruta en Excel. Recibe rutaId y nombre.
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

export const obtenerResumen = () => request("/dashboard/resumen");

export const obtenerFlota = () => request("/dashboard/flota");

// Historial de un pedido por su codigo. Recibe codigo (string).
export const obtenerHistorial = (codigo) =>
  request(`/dashboard/pedidos/${encodeURIComponent(codigo)}/historial`);

// Genera la liquidacion de un cliente. Recibe cliente, periodo_inicio y periodo_fin.
export const generarLiquidacion = ({ cliente, periodo_inicio, periodo_fin } = {}) =>
  request("/dashboard/clientes/liquidacion", {
    method: "POST",
    body: { cliente, periodo_inicio, periodo_fin },
  });

// Descarga la liquidacion (autenticado). Recibe descargaUrl y nombre.
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

export const listarConversaciones = () => request("/correos/conversaciones");

export const obtenerConversacion = (id) => request(`/correos/conversaciones/${id}`);

// Sincroniza la bandeja por IMAP e importa correos nuevos.
export const sincronizarCorreos = () => request("/correos/sincronizar", { method: "POST" });

// Responde un correo por SMTP. Recibe id y cuerpo.
export const responderCorreo = (id, cuerpo) =>
  request(`/correos/conversaciones/${id}/responder`, { method: "POST", body: { cuerpo } });

export const marcarConversacion = (id, estado) =>
  request(`/correos/conversaciones/${id}/estado?estado=${encodeURIComponent(estado)}`, { method: "PATCH" });

export const obtenerEficienciaConductores = () => request("/dashboard/eficiencia-conductores");

export const obtenerCombustible = () => request("/parametros/combustible");

// Actualiza parametros de combustible. Recibe consumo_l_100km y precio_soles_litro.
export const actualizarCombustible = (consumo_l_100km, precio_soles_litro) =>
  request("/parametros/combustible", { method: "PUT", body: { consumo_l_100km, precio_soles_litro } });

// Reprograma un pedido fallido (vuelve a LISTO_PARA_ENVIO). Recibe id.
export const reprogramarPedido = (id) => request(`/pedidos/${id}/reprogramar`, { method: "POST" });

// Cancela un pedido. Recibe id.
export const cancelarPedido = (id) => request(`/pedidos/${id}/cancelar`, { method: "POST" });

// Acepta una solicitud de recojo y crea pedidos en POR_RECOGER. Recibe clienteId, archivo y extras.
export const aceptarSolicitud = (clienteId, archivo, extras = {}) => {
  const fd = new FormData();
  fd.append("cliente_id", clienteId);
  if (extras.referencia) fd.append("referencia", extras.referencia);
  if (extras.contacto_origen) fd.append("contacto_origen", extras.contacto_origen);
  if (extras.conversacion_id) fd.append("conversacion_id", extras.conversacion_id);
  fd.append("file", archivo);
  return request("/recojos/aceptar", { method: "POST", body: fd });
};

// Lista incidencias de auxilio. Recibe estado opcional ("ABIERTA"|"RESUELTA").
export const listarIncidencias = (estado) =>
  request(`/incidencias${estado ? `?estado=${encodeURIComponent(estado)}` : ""}`);

// Manda ayuda a una incidencia. Recibe id y datos { tipo, nota? }.
export const mandarAyuda = (id, datos) =>
  request(`/incidencias/${id}/mandar-ayuda`, { method: "POST", body: datos });

// Obtiene notificaciones del admin. Recibe limite opcional.
export const obtenerNotificaciones = (limite) =>
  request(`/notificaciones${limite ? `?limite=${limite}` : ""}`);

export const marcarNotificacionesVistas = () =>
  request("/notificaciones/marcar-vistas", { method: "POST" });

// Descarga un adjunto de correo (autenticado). Recibe id y nombre.
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

// Lista solicitudes de recojo del almacen. Recibe estado (default SOLICITADO).
export const listarSolicitudesAlmacen = (estado = "SOLICITADO") =>
  request(`/almacen/solicitudes?estado=${encodeURIComponent(estado)}`);

// Asigna una ruta de recojo desde solicitudes seleccionadas. Recibe datos { recojo_ids, conductor_id, vehiculo_placa, nombre_ruta? }.
export const asignarRutaRecojoAlmacen = (datos) =>
  request("/almacen/solicitudes/asignar-ruta", { method: "POST", body: datos });

// Lista recojos del almacen. Recibe estado opcional.
export const listarRecojosAlmacen = (estado) =>
  request(`/almacen/recojos${estado ? `?estado=${encodeURIComponent(estado)}` : ""}`);

// Detalle de conciliacion de un recojo. Recibe id.
export const obtenerConciliacion = (id) => request(`/almacen/recojos/${id}/conciliacion`);

// Confirma el ingreso manual de un recojo. Recibe recojoId y referenciasFaltantes (array).
export const confirmarIngreso = (recojoId, referenciasFaltantes = []) =>
  request(`/almacen/recojos/${recojoId}/confirmar-ingreso`, {
    method: "POST",
    body: { referencias_faltantes: referenciasFaltantes },
  });

// Resuelve un pedido OBSERVADO. Recibe pedidoId.
export const resolverObservado = (pedidoId) =>
  request(`/almacen/pedidos/${pedidoId}/resolver-observado`, { method: "POST" });

export const listarRutasRetorno = () => request("/almacen/retornos/rutas");

// Detalle del retorno de una ruta. Recibe id.
export const obtenerRetornoRuta = (id) => request(`/almacen/retornos/rutas/${id}`);

// Registra el escaneo de un paquete devuelto. Recibe id y codigo.
export const escanearRetorno = (id, codigo) =>
  request(`/almacen/retornos/rutas/${id}/escanear`, { method: "POST", body: { codigo } });
