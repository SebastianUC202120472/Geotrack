import { useEffect, useState } from "react";
import { MapPinned, Ban } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import SectionCard from "../components/ui/SectionCard";
import DataTable from "../components/ui/DataTable";
import Modal from "../components/ui/Modal";
import ResolverDireccionModal from "../components/ResolverDireccionModal";
import { listarPorUbicar } from "../services/api";

// Resolución manual de direcciones (CUS-17): lista los pedidos que el geocoder no
// pudo ubicar y permite fijarlos a mano en el mapa (con buscador por dirección).
export default function Direcciones() {
  const [pedidos, setPedidos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [seleccionado, setSeleccionado] = useState(null);

  // Carga inicial: setState en el callback de la promesa (evita el lint de effect).
  useEffect(() => {
    let activo = true;
    listarPorUbicar()
      .then((d) => activo && setPedidos(d))
      .catch(() => {})
      .finally(() => activo && setCargando(false));
    return () => { activo = false; };
  }, []);

  const recargar = () => { listarPorUbicar().then(setPedidos).catch(() => {}); };

  const columnas = [
    { key: "codigo", header: "Código", render: (p) => <span className="font-medium text-slate-800 nums">{p.codigo || "—"}</span> },
    { key: "cliente_origen", header: "Cliente", render: (p) => <span className="text-slate-600">{p.cliente_origen}</span> },
    { key: "direccion_destino", header: "Dirección", render: (p) => <span className="text-slate-700">{p.direccion_destino}</span> },
  ];

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-in">
      <PageHeader titulo="Resolver Direcciones" subtitulo="Pedidos cuya dirección no se pudo ubicar en el mapa. Corrígelos a mano." />

      <SectionCard title="Direcciones por resolver" subtitle="Haz clic en una para ubicarla en el mapa.">
        {!cargando && pedidos.length === 0 ? (
          <div className="flex flex-col items-center gap-2 py-10 text-slate-400">
            <Ban size={28} /> <p className="text-sm">No hay direcciones pendientes de resolver. 🎉</p>
          </div>
        ) : (
          <DataTable columns={columnas} rows={pedidos} rowKey={(p) => p.id} loading={cargando}
            empty={{ icon: MapPinned, title: "Sin direcciones por resolver", description: "Todo está geocodificado." }}
            onRowClick={(p) => setSeleccionado(p)} />
        )}
      </SectionCard>

      <Modal open={!!seleccionado} onClose={() => setSeleccionado(null)} variant="center">
        {seleccionado && (
          <ResolverDireccionModal
            pedido={seleccionado}
            onClose={() => setSeleccionado(null)}
            onGuardado={() => { setSeleccionado(null); recargar(); }}
          />
        )}
      </Modal>
    </div>
  );
}
