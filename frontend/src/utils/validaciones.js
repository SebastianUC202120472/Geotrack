// Validaciones de formularios (estándar Perú). Devuelven "" si es válido o mensaje de error.

export const validarNombre = (v) =>
  (v || "").trim().length < 3 ? "El nombre debe tener al menos 3 caracteres" : "";

export const validarCorreo = (v) =>
  /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test((v || "").trim()) ? "" : "Correo inválido (ej. nombre@dominio.com)";

// Contraseña segura: 8+ caracteres, con mayúscula, minúscula y número.
export const validarPassword = (v) => {
  v = v || "";
  if (v.length < 8) return "Mínimo 8 caracteres";
  if (!/[A-Z]/.test(v)) return "Debe incluir al menos una mayúscula";
  if (!/[a-z]/.test(v)) return "Debe incluir al menos una minúscula";
  if (!/\d/.test(v)) return "Debe incluir al menos un número";
  if (!/[^A-Za-z0-9]/.test(v)) return "Debe incluir al menos un carácter especial";
  return "";
};

// Celular Perú: 9 dígitos, empieza en 9.
export const validarTelefono = (v) =>
  /^9\d{8}$/.test((v || "").replace(/\s/g, "")) ? "" : "Debe tener 9 dígitos y empezar en 9";

// DNI Perú: exactamente 8 dígitos.
export const validarDni = (v) =>
  /^\d{8}$/.test((v || "").trim()) ? "" : "Debe tener exactamente 8 dígitos";

// Licencia de conducir Perú: una letra y 8 dígitos (ej. Q12345678).
export const validarLicencia = (v) =>
  /^[A-Za-z]\d{8}$/.test((v || "").replace(/[\s-]/g, "")) ? "" : "Una letra y 8 dígitos (ej. Q12345678)";

// Vencimiento de licencia: obligatorio y no pasado. Recibe la fecha "AAAA-MM-DD".
export const validarVencimientoLicencia = (v) => {
  if (!v) return "Indica la fecha de vencimiento";
  const hoy = new Date().toLocaleDateString("en-CA"); // AAAA-MM-DD en la hora local
  return v < hoy ? "La licencia está vencida" : "";
};

// Estado de una licencia segun su vencimiento ("AAAA-MM-DD"): vencida, por vencer (30 días) o vigente.
export const estadoLicencia = (vencimiento) => {
  if (!vencimiento) return null;
  const hoy = new Date(new Date().toLocaleDateString("en-CA"));
  const dias = Math.round((new Date(vencimiento) - hoy) / 86400000);
  if (dias < 0) return { tono: "danger", texto: "Licencia vencida", dias };
  if (dias <= 30) return { tono: "warning", texto: `Licencia vence en ${dias} d`, dias };
  return { tono: "success", texto: "Licencia vigente", dias };
};

// Fecha "AAAA-MM-DD" a texto corto local (dd/mm/aaaa). Recibe la fecha.
export const fechaCorta = (v) => (v ? v.split("-").reverse().join("/") : "—");

// Placa de auto Perú: 3 letras + 3 dígitos (acepta con o sin guion/espacios).
export const validarPlaca = (v) =>
  /^[A-Za-z]{3}[-\s]?\d{3}$/.test((v || "").trim()) ? "" : "Formato: ABC-123 (3 letras y 3 dígitos)";

export const validarCapacidad = (v) => {
  if (v === "" || v === null || v === undefined) return ""; // opcional
  const n = Number(v);
  if (Number.isNaN(n) || n <= 0) return "Debe ser un número mayor a 0";
  if (n > 100) return "Máximo 100 m³";
  return "";
};

// Solo dígitos, recortado a un máximo (para inputs de teléfono/DNI).
export const soloDigitos = (v, max) => (v || "").replace(/\D/g, "").slice(0, max);
