import { useEffect, useState } from "react";
import { MapPinned, Search, Check, X, AlertCircle, Ban } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import SectionCard from "../components/ui/SectionCard";
import DataTable from "../components/ui/DataTable";
import Input from "../components/ui/Input";
import Button from "../components/ui/Button";
import Modal from "../components/ui/Modal";
import MapaPicker from "../components/MapaPicker";
import { listarPorUbicar, buscarDireccion, fijarUbicacionPedido } from "../services/api";

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
          <ResolverDireccion pedido={seleccionado} onCerrar={() => setSeleccionado(null)} onResuelto={() => { setSeleccionado(null); recargar(); }} />
        )}
      </Modal>
    </div>
  );
}

// Modal: buscar por dirección + ubicar el pin en el mapa + guardar las coordenadas.
function ResolverDireccion({ pedido, onCerrar, onResuelto }) {
  const [busqueda, setBusqueda] = useState(pedido.direccion_destino || "");
  const [lat, setLat] = useState(pedido.latitud ?? null);
  const [lng, setLng] = useState(pedido.longitud ?? null);
  const [buscando, setBuscando] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [aviso, setAviso] = useState(null);

  const buscar = async () => {
    if (!busqueda.trim()) return;
    setBuscando(true); setAviso(null);
    try {
      const r = await buscarDireccion(busqueda.trim());
      if (r.encontrado) { setLat(r.latitud); setLng(r.longitud); }
      else setAviso({ texto: "No se encontró esa dirección. Ubícala a mano en el mapa (haz clic)." });
    } catch (err) { setAviso({ texto: err.message }); }
    finally { setBuscando(false); }
  };

  const guardar = async () => {
    if (lat == null || lng == null) { setAviso({ texto: "Primero ubica el punto en el mapa (busca o haz clic)." }); return; }
    setGuardando(true); setAviso(null);
    try {
      await fijarUbicacionPedido(pedido.id, { latitud: lat, longitud: lng, direccion: busqueda.trim() || null });
      onResuelto();
    } catch (err) { setAviso({ texto: err.message }); setGuardando(false); }
  };

  return (
    <>
      <div className="flex items-start justify-between">
        <div>
          <h2 className="font-bold text-slate-900">Ubicar {pedido.codigo || `pedido ${pedido.id}`}</h2>
          <p className="text-sm text-slate-500">{pedido.cliente_origen}</p>
        </div>
        <button onClick={onCerrar} aria-label="Cerrar" className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"><X size={20} /></button>
      </div>

      <div className="mt-4 space-y-4">
        <div className="flex items-end gap-2">
          <div className="flex-1">
            <Input label="Dirección / lugar" value={busqueda} onChange={(e) => setBusqueda(e.target.value)}
              placeholder="Av. Arequipa 123, Miraflores, Lima" hint="Busca por nombre o dirección; luego ajusta el pin." />
          </div>
          <Button variant="secondary" icon={Search} onClick={buscar} disabled={buscando}>{buscando ? "…" : "Buscar"}</Button>
        </div>

        <MapaPicker lat={lat} lng={lng} onChange={(la, lo) => { setLat(la); setLng(lo); }} />

        <p className="text-xs text-slate-400">
          {lat != null ? <>Punto elegido: <b className="nums">{lat.toFixed(5)}, {lng.toFixed(5)}</b> — arrástralo o haz clic para ajustar.</> : "Busca una dirección o haz clic en el mapa para colocar el pin."}
        </p>

        {aviso && (
          <div className="flex items-center gap-2 rounded-xl bg-danger-soft px-3.5 py-3 text-sm text-danger-strong">
            <AlertCircle size={18} /> <span>{aviso.texto}</span>
          </div>
        )}

        <div className="flex gap-2">
          <Button variant="secondary" block onClick={onCerrar} disabled={guardando}>Cancelar</Button>
          <Button icon={Check} block onClick={guardar} disabled={guardando || lat == null}>{guardando ? "Guardando…" : "Guardar ubicación"}</Button>
        </div>
      </div>
    </>
  );
}
