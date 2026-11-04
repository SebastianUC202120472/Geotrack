import { useEffect } from "react";
import { MapContainer, TileLayer, CircleMarker, Tooltip, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";

// Centro por defecto (Lima) cuando no hay puntos que mostrar.
const LIMA = [-12.046, -77.043];

// Ajusta la vista para que entren todos los puntos (solo cuando cambia la cantidad).
// Recibe la lista de [lat, lng].
function Encuadrar({ puntos }) {
  const map = useMap();
  const clave = puntos.map((p) => p.join(",")).join("|");
  useEffect(() => {
    if (puntos.length === 1) map.setView(puntos[0], 14);
    else if (puntos.length > 1) map.fitBounds(puntos, { padding: [30, 30] });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clave, map]);
  return null;
}

// Mapa de los puntos de recojo pendientes para armar la ruta (C12-03). Cada punto se
// puede marcar o desmarcar con un clic. Recibe solicitudes (con latitud/longitud),
// seleccion (ids) y onAlternar(id).
export default function MapaSolicitudesRecojo({ solicitudes, seleccion, onAlternar }) {
  const ubicadas = solicitudes.filter((s) => s.latitud != null && s.longitud != null);
  const puntos = ubicadas.map((s) => [s.latitud, s.longitud]);

  return (
    <div className="overflow-hidden rounded-xl border border-slate-200" style={{ height: 300 }}>
      <MapContainer center={puntos[0] || LIMA} zoom={12} scrollWheelZoom style={{ height: "100%", width: "100%" }}>
        <TileLayer attribution="&copy; OpenStreetMap" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <Encuadrar puntos={puntos} />
        {ubicadas.map((s) => {
          const elegida = seleccion.includes(s.id);
          return (
            <CircleMarker
              key={s.id}
              center={[s.latitud, s.longitud]}
              radius={elegida ? 11 : 8}
              pathOptions={{
                color: "#ffffff",
                weight: 2,
                fillColor: elegida ? "#2563eb" : "#f59e0b",
                fillOpacity: 0.95,
              }}
              eventHandlers={{ click: () => onAlternar(s.id) }}
            >
              <Tooltip direction="top" offset={[0, -6]}>
                <b>{s.codigo}</b> · {s.cliente_origen}
                <br />
                {s.num_pedidos} pedido(s) · {Number(s.volumen_m3 || 0).toFixed(2)} m³
              </Tooltip>
            </CircleMarker>
          );
        })}
      </MapContainer>
    </div>
  );
}
