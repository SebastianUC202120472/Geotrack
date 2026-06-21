import { useEffect } from "react";
import { MapContainer, TileLayer, Marker, useMap, useMapEvents } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Centro por defecto (Lima) cuando aún no hay un punto elegido.
const LIMA = [-12.046, -77.043];

// Pin rojo (gota) para el punto elegido. Usamos divIcon para no depender de las
// imágenes por defecto de Leaflet (que suelen romperse con el bundler).
const iconoPin = L.divIcon({
  className: "",
  html: `<div style="background:#cf3b3b;width:26px;height:26px;border-radius:50% 50% 50% 0;transform:rotate(-45deg);border:2px solid #fff;box-shadow:0 1px 5px rgba(0,0,0,.45)"></div>`,
  iconSize: [26, 26],
  iconAnchor: [13, 26],
});

// Captura el clic en el mapa para colocar/mover el pin.
function CapturaClic({ onPick }) {
  useMapEvents({ click: (e) => onPick(e.latlng.lat, e.latlng.lng) });
  return null;
}

// Recentra el mapa cuando cambian las coordenadas (p. ej. tras una búsqueda).
function Recentrar({ lat, lng }) {
  const map = useMap();
  useEffect(() => {
    if (lat != null && lng != null) map.setView([lat, lng], 16);
  }, [lat, lng, map]);
  return null;
}

// Mapa para ELEGIR una ubicación (CUS-17). El admin hace clic o arrastra el pin.
// Props: lat, lng (number|null) y onChange(lat, lng) que se llama al elegir.
export default function MapaPicker({ lat, lng, onChange }) {
  const hayPunto = lat != null && lng != null;
  const centro = hayPunto ? [lat, lng] : LIMA;

  return (
    <div className="overflow-hidden rounded-xl border border-slate-200" style={{ height: 320 }}>
      <MapContainer center={centro} zoom={hayPunto ? 16 : 12} scrollWheelZoom style={{ height: "100%", width: "100%" }}>
        <TileLayer attribution="&copy; OpenStreetMap" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <CapturaClic onPick={onChange} />
        <Recentrar lat={lat} lng={lng} />
        {hayPunto && (
          <Marker
            position={[lat, lng]}
            icon={iconoPin}
            draggable
            eventHandlers={{ dragend: (e) => { const p = e.target.getLatLng(); onChange(p.lat, p.lng); } }}
          />
        )}
      </MapContainer>
    </div>
  );
}
