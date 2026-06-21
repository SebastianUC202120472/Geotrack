import { useEffect, useState } from "react";
import { PackageX, RotateCcw, Ban, MapPin } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import SectionCard from "../components/ui/SectionCard";
import KpiCard from "../components/ui/KpiCard";
import Button from "../components/ui/Button";
import EmptyState from "../components/ui/EmptyState";
import { listarDevueltos, reprogramarPedido, cancelarPedido } from "../services/api";

// CUS-31: el admin revisa los paquetes fallidos y decide reprogramarlos o cancelarlos.
export default function Devueltos() {
  const [pedidos, setPedidos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [accionando, setAccionando] = useState(null);

  // Recarga la lista (setState en callbacks de promesa, no síncrono).
  const cargar = () => {
    listarDevueltos()
      .then(setPedidos)
      .catch((e) => console.error("No se pudieron cargar devueltos:", e.message))
      .finally(() => setCargando(false));
  };

  useEffect(() => {
    let activo = true;
    listarDevueltos()
      .then((d) => activo && setPedidos(d))
      .catch(() => {})
      .finally(() => activo && setCargando(false));
    return () => { activo = false; };
  }, []);

  // Ejecuta reprogramar/cancelar y refresca la lista.
  const decidir = (id, fn, confirmar) => {
    if (confirmar && !window.confirm(confirmar)) return;
    setAccionando(id);
    fn(id)
      .then(cargar)
      .catch((e) => alert(e.message))
      .finally(() => setAccionando(null));
  };

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-in">
      <PageHeader titulo="Paquetes Devueltos" subtitulo="Pedidos con entrega fallida. Decide si se reintentan mañana o se cancelan." />

      <div className="grid gap-4 sm:grid-cols-2 animate-fade-up">
        <KpiCard label="Devueltos por decidir" value={pedidos.length} tone="warning" icon={PackageX} live={pedidos.length > 0} />
      </div>

      <SectionCard title="Pendientes de decisión">
        {cargando ? (
          <p className="text-sm text-slate-400">Cargando…</p>
        ) : pedidos.length === 0 ? (
          <EmptyState icon={PackageX} title="Sin devueltos" description="No hay paquetes fallidos por decidir." />
        ) : (
          <ul className="divide-y divide-slate-100">
            {pedidos.map((p) => (
              <li key={p.id} className="flex flex-wrap items-center justify-between gap-3 py-3.5">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-800">{p.codigo ?? `PD-${p.id}`}</span>
                    <span className="text-xs text-slate-500">{p.cliente_origen}</span>
                  </div>
                  <p className="mt-0.5 flex items-center gap-1 truncate text-sm text-slate-600">
                    <MapPin size={13} className="text-slate-400" /> {p.direccion_destino}{p.distrito ? ` · ${p.distrito}` : ""}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button variant="secondary" size="sm" icon={RotateCcw} disabled={accionando === p.id}
                    onClick={() => decidir(p.id, reprogramarPedido)}>Reprogramar</Button>
                  <Button variant="ghost" size="sm" icon={Ban} disabled={accionando === p.id}
                    onClick={() => decidir(p.id, cancelarPedido, `¿Cancelar definitivamente ${p.codigo ?? "este pedido"}?`)}>Cancelar</Button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </SectionCard>
    </div>
  );
}
