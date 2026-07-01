const DIAS_ES = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"];

// Agrupa pedidos por día y devuelve los últimos `dias` días con conteo. Recibe array de pedidos y número de días.
export function agruparPedidosPorDia(pedidos = [], dias = 7) {
  const conteo = new Map();
  for (const p of pedidos) {
    if (!p?.fecha_creacion) continue;
    const f = new Date(p.fecha_creacion);
    if (Number.isNaN(f.getTime())) continue;
    const clave = `${f.getFullYear()}-${f.getMonth()}-${f.getDate()}`;
    conteo.set(clave, (conteo.get(clave) || 0) + 1);
  }

  const resultado = [];
  const hoy = new Date();
  for (let i = dias - 1; i >= 0; i--) {
    const d = new Date(hoy);
    d.setDate(hoy.getDate() - i);
    const clave = `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
    resultado.push({
      dia: `${DIAS_ES[d.getDay()]} ${String(d.getDate()).padStart(2, "0")}`,
      pedidos: conteo.get(clave) || 0,
    });
  }
  return resultado;
}
