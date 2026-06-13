// src/services/api.js
// Cliente HTTP del panel de administración.
// Centraliza la URL base, el envío del token JWT y el manejo de la sesión.
// La URL base viene de VITE_API_URL (en Docker es "/api", servido por Nginx).

const API_URL = import.meta.env.VITE_API_URL;
const TOKEN_KEY = "admin_token";

export const getToken = () => localStorage.getItem(TOKEN_KEY);
export const guardarToken = (token) => localStorage.setItem(TOKEN_KEY, token);
export const borrarToken = () => localStorage.removeItem(TOKEN_KEY);

// Núcleo de todas las peticiones autenticadas.
// Adjunta el token, parsea la respuesta y, si el token caducó (401), limpia la
// sesión y manda al login para no dejar la pantalla en un estado roto.
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

  if (respuesta.status === 401) {
    borrarToken();
    if (window.location.pathname !== "/login") window.location.href = "/login";
    throw new Error("Tu sesión expiró. Vuelve a iniciar sesión.");
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

// Login (CUS-02). El backend usa OAuth2: espera 'username' y 'password' como
// formulario, no como JSON.
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
  guardarToken(datos.access_token);
  return datos;
};

// Alta de usuario conductor (CUS-01). Solo un admin autenticado puede crearlos.
export const registrarConductor = (correo, contrasena) =>
  request("/auth/registro", {
    method: "POST",
    body: { correo, contrasena, rol: "conductor" },
  });

/* ============================================================
   PEDIDOS  (Inbound — CUS-13 / CUS-15 / CUS-16)
============================================================ */

export const subirPedidosExcel = (archivo) => {
  const formData = new FormData();
  formData.append("file", archivo);
  return request("/pedidos/upload", { method: "POST", body: formData });
};

export const listarPedidos = () => request("/pedidos/");

// Devuelve { zonas_operativas: [{ distrito, total_pedidos }] }
export const listarZonas = () => request("/pedidos/zonas");

/* ============================================================
   VEHÍCULOS Y FLOTA  (gestión del admin)
============================================================ */

export const listarVehiculos = () => request("/vehiculos/");

export const crearVehiculo = (datos) =>
  request("/vehiculos/", { method: "POST", body: datos });

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
   DASHBOARD / TRAZABILIDAD  (CUS-33 / CUS-35)
============================================================ */

export const obtenerResumen = () => request("/dashboard/resumen");

// Estado y avance de todas las rutas de la flota.
export const obtenerFlota = () => request("/dashboard/flota");

// Línea de tiempo completa de un paquete por su código (PD-001).
export const obtenerHistorial = (codigo) =>
  request(`/dashboard/pedidos/${encodeURIComponent(codigo)}/historial`);

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
