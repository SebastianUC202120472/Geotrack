import { Plus, Trash2 } from "lucide-react";
import Button from "./ui/Button";
import { PEDIDO_VACIO } from "../utils/pedidosManual";

const CAMPO = "w-full rounded-lg border border-slate-200 bg-white px-2.5 py-2 text-sm text-slate-800 placeholder:text-slate-400 outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30";

// Editor de pedidos para registrar una solicitud sin Excel (C11-02): una tarjeta por pedido.
// Recibe filas (array), onCambiar(nuevasFilas) y errores ({indice: texto}).
export default function EditorPedidosManual({ filas, onCambiar, errores = {} }) {
  // Cambia un campo de una fila. Recibe el indice, el campo y el valor.
  const cambiar = (i, campo, valor) =>
    onCambiar(filas.map((f, j) => (j === i ? { ...f, [campo]: valor } : f)));

  const agregar = () => onCambiar([...filas, { ...PEDIDO_VACIO }]);
  const quitar = (i) => onCambiar(filas.filter((_, j) => j !== i));

  return (
    <div className="space-y-3">
      {filas.map((f, i) => (
        <div key={i} className={`rounded-xl border p-3 ${errores[i] ? "border-danger/40 bg-danger-soft/40" : "border-slate-200 bg-slate-50/60"}`}>
          <div className="mb-2 flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">Pedido {i + 1}</span>
            {filas.length > 1 && (
              <button type="button" onClick={() => quitar(i)} aria-label={`Quitar pedido ${i + 1}`}
                className="rounded-lg p-1.5 text-slate-400 hover:bg-white hover:text-danger">
                <Trash2 size={16} />
              </button>
            )}
          </div>
          <div className="grid gap-2 sm:grid-cols-3">
            <input className={CAMPO} placeholder="Referencia del cliente *" value={f.referencia_externa}
              onChange={(e) => cambiar(i, "referencia_externa", e.target.value)} aria-label="Referencia del pedido" />
            <input className={CAMPO} placeholder="Destinatario" value={f.nombre_destinatario}
              onChange={(e) => cambiar(i, "nombre_destinatario", e.target.value)} aria-label="Destinatario" />
            <div className="grid grid-cols-2 gap-2">
              <input className={CAMPO} placeholder="Teléfono" inputMode="tel" value={f.telefono_destinatario}
                onChange={(e) => cambiar(i, "telefono_destinatario", e.target.value)} aria-label="Teléfono" />
              <input className={CAMPO} placeholder="DNI" inputMode="numeric" value={f.dni_destinatario}
                onChange={(e) => cambiar(i, "dni_destinatario", e.target.value.replace(/\D/g, "").slice(0, 8))} aria-label="DNI" />
            </div>
            <input className={`${CAMPO} sm:col-span-2`} placeholder="Dirección de entrega, distrito *" value={f.direccion_destino}
              onChange={(e) => cambiar(i, "direccion_destino", e.target.value)} aria-label="Dirección de entrega" />
            <div className="grid grid-cols-2 gap-2">
              <input className={CAMPO} placeholder="Peso kg" type="number" min="0" step="0.1" value={f.peso_kg}
                onChange={(e) => cambiar(i, "peso_kg", e.target.value)} aria-label="Peso en kg" />
              <input className={CAMPO} placeholder="Vol. m³" type="number" min="0" step="0.01" value={f.volumen_m3}
                onChange={(e) => cambiar(i, "volumen_m3", e.target.value)} aria-label="Volumen en m³" />
            </div>
          </div>
          {errores[i] && <p className="mt-2 text-xs font-medium text-danger-strong">{errores[i]}</p>}
        </div>
      ))}
      <Button type="button" variant="secondary" icon={Plus} onClick={agregar} disabled={filas.length >= 500}>
        Agregar otro pedido
      </Button>
    </div>
  );
}
