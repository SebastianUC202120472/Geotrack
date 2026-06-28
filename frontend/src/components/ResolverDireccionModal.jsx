import { useState } from "react";
import { Search, Check, X, AlertCircle } from "lucide-react";
import Input from "./ui/Input";
import Button from "./ui/Button";
import MapaPicker from "./MapaPicker";
import { buscarDireccion, fijarUbicacionPedido } from "../services/api";

// Modal reutilizable para ubicar un pedido sin geocodificar en el mapa (CUS-17).
// Props: pedido (objeto), onClose (fn), onGuardado (fn llamada tras guardar con éxito).
export default function ResolverDireccionModal({ pedido, onClose, onGuardado }) {
  const [busqueda, setBusqueda] = useState(pedido.direccion_destino || "");
  const [lat, setLat] = useState(pedido.latitud ?? null);
  const [lng, setLng] = useState(pedido.longitud ?? null);
  const [buscando, setBuscando] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [aviso, setAviso] = useState(null);

  // Geocodifica la cadena de búsqueda con Nominatim y mueve el pin al resultado.
  const buscar = () => {
    if (!busqueda.trim()) return;
    setBuscando(true);
    setAviso(null);
    buscarDireccion(busqueda.trim())
      .then((r) => {
        if (r.encontrado) {
          setLat(r.latitud);
          setLng(r.longitud);
        } else {
          setAviso({ texto: "No se encontró esa dirección. Ubícala a mano en el mapa (haz clic)." });
        }
      })
      .catch((err) => setAviso({ texto: err.message }))
      .finally(() => setBuscando(false));
  };

  // Envía las coordenadas al backend y notifica al padre si tiene éxito.
  const guardar = () => {
    if (lat == null || lng == null) {
      setAviso({ texto: "Primero ubica el punto en el mapa (busca o haz clic)." });
      return;
    }
    setGuardando(true);
    setAviso(null);
    fijarUbicacionPedido(pedido.id, { latitud: lat, longitud: lng, direccion: busqueda.trim() || null })
      .then(() => {
        onGuardado();
        onClose();
      })
      .catch((err) => {
        setAviso({ texto: err.message });
        setGuardando(false);
      });
  };

  return (
    <>
      <div className="flex items-start justify-between">
        <div>
          <h2 className="font-bold text-slate-900">Ubicar {pedido.codigo || `pedido ${pedido.id}`}</h2>
          <p className="text-sm text-slate-500">{pedido.cliente_origen}</p>
        </div>
        <button onClick={onClose} aria-label="Cerrar" className="rounded-lg p-2 text-slate-500 hover:bg-slate-100">
          <X size={20} />
        </button>
      </div>

      <div className="mt-4 space-y-4">
        <div className="flex items-end gap-2">
          <div className="flex-1">
            <Input
              label="Dirección / lugar"
              value={busqueda}
              onChange={(e) => setBusqueda(e.target.value)}
              placeholder="Av. Arequipa 123, Miraflores, Lima"
              hint="Busca por nombre o dirección; luego ajusta el pin."
            />
          </div>
          <Button variant="secondary" icon={Search} onClick={buscar} disabled={buscando}>
            {buscando ? "…" : "Buscar"}
          </Button>
        </div>

        <MapaPicker lat={lat} lng={lng} onChange={(la, lo) => { setLat(la); setLng(lo); }} />

        <p className="text-xs text-slate-400">
          {lat != null
            ? <>Punto elegido: <b className="nums">{lat.toFixed(5)}, {lng.toFixed(5)}</b> — arrástralo o haz clic para ajustar.</>
            : "Busca una dirección o haz clic en el mapa para colocar el pin."}
        </p>

        {aviso && (
          <div className="flex items-center gap-2 rounded-xl bg-danger-soft px-3.5 py-3 text-sm text-danger-strong">
            <AlertCircle size={18} /> <span>{aviso.texto}</span>
          </div>
        )}

        <div className="flex gap-2">
          <Button variant="secondary" block onClick={onClose} disabled={guardando}>Cancelar</Button>
          <Button icon={Check} block onClick={guardar} disabled={guardando || lat == null}>
            {guardando ? "Guardando…" : "Guardar ubicación"}
          </Button>
        </div>
      </div>
    </>
  );
}
