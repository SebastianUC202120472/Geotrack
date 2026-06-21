import { Fragment, useEffect } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";

// Centro por defecto (Lima) cuando todavía no hay puntos que mostrar.
const LIMA = [-12.046, -77.043];

// Ajusta el encuadre del mapa para que entren todos los puntos (conductores +
// paradas). Entrada: `puntos` = lista de [lat, lon].
function AutoEncuadre({ puntos }) {
  const map = useMap();
  useEffect(() => {
    if (puntos.length === 0) return;
    if (puntos.length === 1) {
      map.setView(puntos[0], 14);
    } else {
      map.fitBounds(puntos, { padding: [40, 40] });
    }
  }, [puntos, map]);
  return null;
}

// Mapa de la flota con OpenStreetMap (gratis, sin API key). Es el fallback cuando
// no hay clave de Google Maps. Entrada: `conductores` (array de ConductorUbicacion).
export default function MapaFlotaLeaflet({ conductores }) {
  const puntos = [];
  conductores.forEach((c) => {
    if (c.latitud != null && c.longitud != null) puntos.push([c.latitud, c.longitud]);
    c.paradas.forEach((p) => puntos.push([p.latitud, p.longitud]));
  });

  return (
    <div className="overflow-hidden rounded-card border border-slate-200 shadow-card" style={{ height: 520 }}>
      <MapContainer center={LIMA} zoom={12} scrollWheelZoom style={{ height: "100%", width: "100%" }}>
        <TileLayer attribution='&copy; OpenStreetMap' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <AutoEncuadre puntos={puntos} />

        {conductores.map((c) => (
          <Fragment key={c.conductor_id}>
            {c.paradas.map((p, i) => (
              <CircleMarker
                key={`parada-${c.conductor_id}-${i}`}
                center={[p.latitud, p.longitud]}
                radius={6}
                pathOptions={{ color: "#f59e0b", fillColor: "#f59e0b", fillOpacity: 0.7, weight: 2 }}
              >
                <Popup>
                  <b>Parada {p.secuencia ?? "—"}</b>
                  <br />
                  {p.destinatario || "Sin destinatario"}
                </Popup>
              </CircleMarker>
            ))}

            {c.latitud != null && c.longitud != null && (
              <CircleMarker
                center={[c.latitud, c.longitud]}
                radius={10}
                pathOptions={{ color: "#1d4ed8", fillColor: c.en_linea ? "#2563eb" : "#94a3b8", fillOpacity: 0.9, weight: 3 }}
              >
                <Popup>
                  <b>{c.conductor || "Conductor"}</b>
                  <br />
                  {c.ruta || "Ruta"}
                  <br />
                  {c.en_linea ? "🟢 En línea" : "⚪ Sin señal reciente"}
                </Popup>
              </CircleMarker>
            )}
          </Fragment>
        ))}
      </MapContainer>
    </div>
  );
}
