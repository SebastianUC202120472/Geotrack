// Utilidades de fecha para el panel.

// Convierte una fecha en un texto relativo legible ("hace un momento", "hace 3 min",
// "hace 2 h", "hace 1 d"). Recibe: la fecha (string ISO o Date). Devuelve "" si no
// hay fecha o es inválida.
// Nota: el backend envía los timestamps en UTC SIN sufijo de zona (naive). Si el
// string no trae zona, lo tratamos como UTC (append "Z") para no desfasar la hora.
export function haceCuanto(fecha) {
  if (!fecha) return "";
  const iso =
    typeof fecha === "string" && !/[zZ]|[+-]\d\d:?\d\d$/.test(fecha) ? `${fecha}Z` : fecha;
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return "";
  const seg = Math.max(0, Math.floor((Date.now() - t) / 1000));
  if (seg < 60) return "hace un momento";
  const min = Math.floor(seg / 60);
  if (min < 60) return `hace ${min} min`;
  const horas = Math.floor(min / 60);
  if (horas < 24) return `hace ${horas} h`;
  const dias = Math.floor(horas / 24);
  return `hace ${dias} d`;
}
