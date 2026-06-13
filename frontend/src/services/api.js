// src/services/api.js

const API_URL = import.meta.env.VITE_API_URL;

/* ==========================================================
   HELPERS (Configuración de autenticación)
========================================================== */

const getAuthHeaders = () => {
  const token = localStorage.getItem("admin_token");
  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };
};

/* ==========================================================
   AUTH (Login y registro)
========================================================== */

export const loginAdmin = async (correo, contrasena) => {
  const formData = new URLSearchParams();
  formData.append("username", correo);
  formData.append("password", contrasena);

  const response = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: formData,
  });

  if (!response.ok) throw new Error("Credenciales inválidas");
  const data = await response.json();
  localStorage.setItem("admin_token", data.access_token);
  return data;
};

/* ==========================================================
   DASHBOARD (Resumen y métricas)
========================================================== */

export const getDashboardResumen = async () => {
  const response = await fetch(`${API_URL}/dashboard/resumen`, {
    method: "GET",
    headers: getAuthHeaders(),
  });
  if (!response.ok) throw new Error("Error al cargar el dashboard");
  return response.json();
};

export const getFlotaStatus = async () => {
  const response = await fetch(`${API_URL}/dashboard/flota`, {
    method: "GET",
    headers: getAuthHeaders(),
  });
  if (!response.ok) throw new Error("Error al cargar la flota");
  return response.json();
};

export const getHistorialPedido = async (codigo) => {
  const response = await fetch(`${API_URL}/dashboard/pedidos/${codigo}/historial`, {
    method: "GET",
    headers: getAuthHeaders(),
  });
  if (!response.ok) throw new Error("No se encontró el historial");
  return response.json();
};

/* ==========================================================
   PEDIDOS (Importación y geocodificación)
========================================================== */

export const uploadPedidosExcel = async (file) => {
  const token = localStorage.getItem("admin_token");
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_URL}/pedidos/upload`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || "Error al importar pedidos");
  }
  return response.json();
};

export const getPedidos = async () => {
  const response = await fetch(`${API_URL}/pedidos`, {
    method: "GET",
    headers: getAuthHeaders(),
  });
  if (!response.ok) throw new Error("Error al obtener pedidos");
  return response.json();
};

export const procesarGeocodificacion = async () => {
  const response = await fetch(`${API_URL}/pedidos/geocodificar`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  if (!response.ok) throw new Error("Error en geocodificación");
  return response.json();
};

/* ==========================================================
   ENRUTAMIENTO Y ASIGNACIÓN (Bloques y optimización)
========================================================== */

// Lista las zonas basadas en pedidos
export const getDistritos = async () => {
  const res = await fetch(`${API_URL}/pedidos/zonas`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Error al obtener zonas");
  return res.json();
};

// Lista vehículos (para asignar como conductores)
export const getConductores = async () => {
  const res = await fetch(`${API_URL}/vehiculos`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Error al obtener vehículos/conductores");
  return res.json();
};

export const asignarBloquePedidos = async (data) => {
  const response = await fetch(`${API_URL}/rutas/asignar-bloque`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ ...data, timestamp: new Date().toISOString() }),
  });
  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.detail || "Error asignando bloque");
  }
  return response.json();
};

export const optimizarRutaConductor = async (data) => {
  const response = await fetch(`${API_URL}/rutas/conductor/optimizar`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });
  
  const text = await response.text();
  let result;
  try { result = text ? JSON.parse(text) : {}; } catch { result = { message: text }; }

  if (!response.ok) throw new Error(result.message || result.detail || "Error al optimizar");
  return result;
};

/* ==========================================================
   VEHÍCULOS (Gestión básica)
========================================================== */

export const getVehiculos = async () => {
  const response = await fetch(`${API_URL}/vehiculos`, {
    method: "GET",
    headers: getAuthHeaders(),
  });
  if (!response.ok) throw new Error("Error al obtener vehículos");
  return response.json();
};
/* ==========================================================
   CUS-21: GESTIÓN DE MANIFIESTOS Y APP MÓVIL
========================================================== */

// 1. Consultar la ruta que el conductor tiene activa actualmente
export const getRutaActiva = async () => {
  const response = await fetch(`${API_URL}/conductor/ruta-activa`, {
    method: "GET",
    headers: getAuthHeaders(),
  });
  if (!response.ok) throw new Error("Error al obtener la ruta activa");
  return response.json();
};

// 2. Obtener el manifiesto detallado de la ruta activa
export const getManifiestoConductor = async () => {
  const response = await fetch(`${API_URL}/conductor/ruta-activa/manifiesto`, {
    method: "GET",
    headers: getAuthHeaders(),
  });
  if (!response.ok) throw new Error("Error al cargar el manifiesto");
  return response.json();
};

// 3. Obtener datos para la navegación (Google Maps/Waze)
export const getNavegacionRuta = async () => {
  const response = await fetch(`${API_URL}/conductor/ruta-activa/navegacion`, {
    method: "GET",
    headers: getAuthHeaders(),
  });
  if (!response.ok) throw new Error("Error al cargar navegación");
  return response.json();
};

// 4. Validar un paquete mediante QR
export const validarPaqueteQR = async (qrData) => {
  const response = await fetch(`${API_URL}/conductor/almacen/validar-qr`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ qr_code: qrData }),
  });
  if (!response.ok) throw new Error("Error al validar QR");
  return response.json();
};

// 5. Actualizar estado de una parada (Entregado, Rechazado, etc)
export const actualizarEstadoParada = async (pedido_id, nuevoEstado) => {
  const response = await fetch(`${API_URL}/conductor/paradas/${pedido_id}/estado`, {
    method: "PATCH",
    headers: getAuthHeaders(),
    body: JSON.stringify({ estado: nuevoEstado }),
  });
  if (!response.ok) throw new Error("Error al actualizar el estado");
  return response.json();
};

// 6. Finalizar la ruta completa
export const finalizarRuta = async () => {
  const response = await fetch(`${API_URL}/conductor/ruta-activa/finalizar`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  if (!response.ok) throw new Error("Error al finalizar la ruta");
  return response.json();
};