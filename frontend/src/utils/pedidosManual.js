// Utilidades del registro manual de pedidos de una solicitud de recojo (C11-02).

// Fila vacia del editor de pedidos manual.
export const PEDIDO_VACIO = {
  referencia_externa: "",
  nombre_destinatario: "",
  telefono_destinatario: "",
  dni_destinatario: "",
  direccion_destino: "",
  peso_kg: "",
  volumen_m3: "",
};

// Revisa las filas del editor y devuelve { errores: {indice: texto}, pedidos: [...] } listo para la API.
// Recibe la lista de filas tal como las escribio el usuario.
export function validarPedidosManual(filas) {
  const errores = {};
  const vistas = new Set();
  const pedidos = [];
  filas.forEach((f, i) => {
    const ref = f.referencia_externa.trim();
    const dir = f.direccion_destino.trim();
    const dni = f.dni_destinatario.trim();
    if (!ref) errores[i] = "Falta la referencia del pedido";
    else if (vistas.has(ref)) errores[i] = `La referencia ${ref} está repetida`;
    else if (!dir) errores[i] = "Falta la dirección de entrega";
    else if (dni && !/^\d{8}$/.test(dni)) errores[i] = "El DNI debe tener 8 dígitos";
    vistas.add(ref);
    pedidos.push({
      referencia_externa: ref,
      direccion_destino: dir,
      nombre_destinatario: f.nombre_destinatario.trim() || null,
      telefono_destinatario: f.telefono_destinatario.trim() || null,
      dni_destinatario: dni || null,
      peso_kg: f.peso_kg === "" ? null : Number(f.peso_kg),
      volumen_m3: f.volumen_m3 === "" ? null : Number(f.volumen_m3),
    });
  });
  return { errores, pedidos };
}
