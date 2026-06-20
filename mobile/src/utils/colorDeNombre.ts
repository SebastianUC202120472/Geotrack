// Color de fondo determinista para el avatar de respaldo (sin foto).
// Recibe: nombre (string). Devuelve: un color hex estable para ese nombre.
const PALETA = ["#2563EB", "#7C3AED", "#0891B2", "#059669", "#D97706", "#DC2626", "#DB2777", "#4F46E5"];

export function colorDeNombre(nombre?: string | null): string {
  const base = (nombre || "?").trim();
  let suma = 0;
  for (let i = 0; i < base.length; i++) suma += base.charCodeAt(i);
  return PALETA[suma % PALETA.length];
}
