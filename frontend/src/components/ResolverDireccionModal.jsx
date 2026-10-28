import { useState } from "react";
import { Search, Check, X, AlertCircle, MapPin } from "lucide-react";
import Input from "./ui/Input";
import Button from "./ui/Button";
import MapaPicker from "./MapaPicker";
import { buscarDireccion, fijarUbicacionPedido } from "../services/api";

// Modal para ubicar un pedido sin geocodificar o corregir uno mal ubicado. Recibe pedido, onClose y onGuardado.
export default function ResolverDireccionModal({ pedido, onClose, onGuardado }) {
  const corrigiendo = pedido.latitud != null && pedido.longitud != null;
  const [busqueda, setBusqueda] = useState(pedido.direccion_destino || "");
  const [lat, setLat] = useState(pedido.latitud ?? null);
  const [lng, setLng] = useState(pedido.longitud ?? null);
  const [coincidencias, setCoincidencias] = useState([]);
  const [elegida, setElegida] = useState(null);
  const [buscando, setBuscando] = useState(false);
  const [guardando, setGuardando] = useState(false);
  const [aviso, setAviso] = useState(null);

  // Mueve el pin a una coincidencia de la lista. Recibe la coincidencia y su posición.
  const elegir = (c, i) => {
    setElegida(i);
    setLat(c.latitud);
    setLng(c.longitud);
  };

  // Geocodifica la cadena de búsqueda; muestra las coincidencias y pone el pin en la primera.
  const buscar = () => {
    if (!busqueda.trim()) return;
    setBuscando(true);
    setAviso(null);
    buscarDireccion(busqueda.trim())
      .then((r) => {
        const lista = r.coincidencias || [];
        setCoincidencias(lista);
        if (lista.length) {
          elegir(lista[0], 0);
        } else {
          setElegida(null);
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
          <h2 className="font-bold text-slate-900">
            {corrigiendo ? "Corregir ubicación de" : "Ubicar"} {pedido.codigo || `pedido ${pedido.id}`}
          </h2>
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
              onKeyDown={(e) => { if (e.key === "Enter") buscar(); }}
              placeholder="Av. Arequipa 123, Miraflores, Lima"
              hint="Busca por nombre o dirección; elige la coincidencia correcta y ajusta el pin."
            />
          </div>
          <Button variant="secondary" icon={Search} onClick={buscar} disabled={buscando}>
            {buscando ? "…" : "Buscar"}
          </Button>
        </div>

        {coincidencias.length > 1 && (
          <div>
            <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-slate-500">
              {coincidencias.length} coincidencias: elige la correcta
            </p>
            <ul className="max-h-40 space-y-1 overflow-y-auto pr-1">
              {coincidencias.map((c, i) => (
                <li key={`${c.latitud},${c.longitud},${i}`}>
                  <button
                    type="button"
                    onClick={() => elegir(c, i)}
                    aria-pressed={elegida === i}
                    className={`flex w-full items-start gap-2 rounded-lg border px-3 py-2 text-left text-sm transition ${
                      elegida === i
                        ? "border-brand-300 bg-brand-50 text-brand-800"
                        : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
                    }`}
                  >
                    <MapPin size={15} className={`mt-0.5 shrink-0 ${elegida === i ? "text-brand-600" : "text-slate-400"}`} />
                    <span className="flex-1">
                      {c.direccion}
                      {c.distrito && <span className="ml-1.5 text-xs font-semibold text-slate-400">· {c.distrito}</span>}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}

        <MapaPicker lat={lat} lng={lng} onChange={(la, lo) => { setLat(la); setLng(lo); setElegida(null); }} />

        <p className="text-xs text-slate-400">
          {lat != null
            ? <>Punto elegido: <b className="nums">{lat.toFixed(5)}, {lng.toFixed(5)}</b> — arrástralo o haz clic para ajustar. La zona se recalcula con el punto.</>
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
