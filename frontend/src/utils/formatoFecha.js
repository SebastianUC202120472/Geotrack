// Convierte una fecha (string ISO o Date) en texto relativo ("hace 3 min", "hace 2 h"). Recibe fecha; trata naive como UTC.
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
