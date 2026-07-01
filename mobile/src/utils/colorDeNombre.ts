// Devuelve un color hex estable de la paleta para el nombre recibido.
const PALETA = ["#2563EB", "#7C3AED", "#0891B2", "#059669", "#D97706", "#DC2626", "#DB2777", "#4F46E5"];

export function colorDeNombre(nombre?: string | null): string {
  const base = (nombre || "?").trim();
  let suma = 0;
  for (let i = 0; i < base.length; i++) suma += base.charCodeAt(i);
  return PALETA[suma % PALETA.length];
}
