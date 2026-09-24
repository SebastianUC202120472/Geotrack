import { useEffect, useState } from "react";
import { X, ChevronUp, ChevronDown, Trash2, CheckCircle2, AlertCircle, Loader2, Save, Route } from "lucide-react";
import Button from "./ui/Button";
import { EstadoBadge } from "./ui/Badge";
import { obtenerParadasRuta, reordenarParadasRuta, quitarParadaRuta } from "../services/api";

// Modal para reordenar y quitar paradas de una ruta (CUS-21: Ajuste Manual de Ruta).
export default function ModalEditarRuta({ ruta, onCerrar, onCambios }) {
  const [paradas, setParadas] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [guardando, setGuardando] = useState(false);
  const [quitandoId, setQuitandoId] = useState(null);
  const [aviso, setAviso] = useState(null);

  const cargar = async () => {
    setCargando(true);
    setAviso(null);
    try {
      const res = await obtenerParadasRuta(ruta.ruta_id);
      setParadas(res.paradas || []);
    } catch (err) {
      setAviso({ ok: false, texto: err.message });
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargar();
  }, [ruta.ruta_id]);

  // Mueve una parada hacia arriba (-1) o hacia abajo (+1) en el estado local.
  const mover = (idx, dir) => {
    const nuevoIdx = idx + dir;
    if (nuevoIdx < 0 || nuevoIdx >= paradas.length) return;
    const copia = [...paradas];
    const temp = copia[idx];
    copia[idx] = copia[nuevoIdx];
    copia[nuevoIdx] = temp;
    setParadas(copia);
    setAviso(null);
  };

  // Envía la nueva secuencia ordenada al backend (PATCH /api/rutas/{id}/reordenar).
  const guardarOrden = async () => {
    setGuardando(true);
    setAviso(null);
    try {
      const orden = paradas.map((p) => p.pedido_id);
      await reordenarParadasRuta(ruta.ruta_id, orden);
      if (onCambios) onCambios();
      if (onCerrar) onCerrar();
    } catch (err) {
      setAviso({ ok: false, texto: err.message });
      setGuardando(false);
    }
  };

  // Retira un pedido de la ruta (DELETE /api/rutas/{id}/paradas/{pedido_id}).
  const quitar = async (pedidoId, codigo) => {
    setQuitandoId(pedidoId);
    setAviso(null);
    try {
      const res = await quitarParadaRuta(ruta.ruta_id, pedidoId);
      setAviso({ ok: true, texto: res.mensaje || `Pedido ${codigo} quitado de la ruta.` });
      setParadas((prev) => prev.filter((p) => p.pedido_id !== pedidoId));
      if (onCambios) onCambios();
    } catch (err) {
      setAviso({ ok: false, texto: err.message });
    } finally {
      setQuitandoId(null);
    }
  };

  return (
    <div className="w-full space-y-5">
      <div className="flex items-center justify-between border-b border-slate-100 pb-4">
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-600 text-white">
            <Route size={20} />
          </span>
          <div>
            <h2 className="font-bold text-slate-900">Editar Ruta: {ruta.nombre}</h2>
            <p className="text-xs text-slate-500">
              {ruta.conductor_nombre || "Sin conductor"} · {paradas.length} parada(s)
            </p>
          </div>
        </div>
        <button onClick={onCerrar} aria-label="Cerrar" className="rounded-lg p-2 text-slate-500 hover:bg-slate-100">
          <X size={20} />
        </button>
      </div>

      {aviso && (
        <div
          className={`flex items-center gap-2 rounded-xl px-4 py-3 text-sm ${
            aviso.ok ? "bg-success-soft text-success-strong" : "bg-danger-soft text-danger-strong"
          }`}
        >
          {aviso.ok ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
          <span>{aviso.texto}</span>
        </div>
      )}

      {cargando ? (
        <div className="flex justify-center py-12 text-slate-400">
          <Loader2 className="animate-spin" size={24} />
        </div>
      ) : paradas.length === 0 ? (
        <div className="py-8 text-center text-slate-500">Esta ruta no tiene paradas asignadas.</div>
      ) : (
        <>
          <div className="max-h-[500px] overflow-y-auto overflow-x-hidden rounded-xl border border-slate-200 bg-white">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs font-semibold text-slate-500">
                <tr>
                  <th className="px-3 py-2.5 text-center">#</th>
                  <th className="px-3 py-2.5">Código</th>
                  <th className="px-3 py-2.5">Destinatario / Dirección</th>
                  <th className="px-3 py-2.5">Estado</th>
                  <th className="px-3 py-2.5 text-center">Orden</th>
                  <th className="px-3 py-2.5 text-right">Acción</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {paradas.map((p, idx) => {
                  const gestionada = p.estado_entrega === "ENTREGADO" || p.estado_entrega === "FALLIDO";
                  const procesandoEsta = quitandoId === p.pedido_id;

                  return (
                    <tr key={p.pedido_id} className="hover:bg-slate-50/80">
                      <td className="px-3 py-3 text-center font-bold text-slate-400 nums">
                        {idx + 1}
                      </td>
                      <td className="px-3 py-3 font-semibold text-slate-800 nums">
                        {p.codigo}
                      </td>
                      <td className="px-3 py-3">
                        <p className="font-medium text-slate-800">{p.nombre_destinatario || "—"}</p>
                        <p className="text-xs text-slate-500">
                          {p.direccion_destino} {p.distrito ? `(${p.distrito})` : ""}
                        </p>
                      </td>
                      <td className="px-3 py-3">
                        <EstadoBadge estado={p.estado_entrega || "PENDIENTE"} />
                      </td>
                      <td className="px-3 py-3 text-center">
                        <div className="inline-flex items-center gap-1">
                          <button
                            type="button"
                            onClick={() => mover(idx, -1)}
                            disabled={idx === 0 || guardando}
                            title="Subir posición"
                            className="rounded p-1 text-slate-500 hover:bg-slate-200 disabled:opacity-30"
                          >
                            <ChevronUp size={16} />
                          </button>
                          <button
                            type="button"
                            onClick={() => mover(idx, 1)}
                            disabled={idx === paradas.length - 1 || guardando}
                            title="Bajar posición"
                            className="rounded p-1 text-slate-500 hover:bg-slate-200 disabled:opacity-30"
                          >
                            <ChevronDown size={16} />
                          </button>
                        </div>
                      </td>
                      <td className="px-3 py-3 text-right">
                        {gestionada ? (
                          <span className="text-xs text-slate-400" title="No se puede quitar una parada ya entregada o fallida">
                            Gestionada
                          </span>
                        ) : (
                          <button
                            type="button"
                            onClick={() => quitar(p.pedido_id, p.codigo)}
                            disabled={procesandoEsta || guardando}
                            title="Quitar de la ruta (vuelve a Listo para envío)"
                            className="inline-flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-semibold text-danger hover:bg-danger-soft disabled:opacity-50"
                          >
                            {procesandoEsta ? (
                              <Loader2 className="animate-spin" size={14} />
                            ) : (
                              <>
                                <Trash2 size={14} />
                                Quitar
                              </>
                            )}
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-end gap-3 pt-2">
            <Button variant="secondary" onClick={onCerrar} disabled={guardando}>
              Cerrar
            </Button>
            <Button icon={Save} onClick={guardarOrden} disabled={guardando || paradas.length === 0}>
              {guardando ? "Guardando orden…" : "Guardar orden de paradas"}
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
