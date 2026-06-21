import { Fragment, useEffect } from "react";
import { MapContainer, TileLayer, CircleMarker, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Centro por defecto (Lima) cuando todavía no hay puntos que mostrar.
const LIMA = [-12.046, -77.043];

// Pin (gota) para una PARADA: color del conductor + número de orden. Distinto del
// círculo de la ubicación del conductor.
const iconoParada = (color, n) =>
  L.divIcon({
    className: "",
    html: `<div style="background:${color};width:24px;height:24px;border-radius:50% 50% 50% 0;transform:rotate(-45deg);border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center"><span style="transform:rotate(45deg);color:#fff;font-size:11px;font-weight:700">${n}</span></div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 24],
  });

// Ajusta el encuadre para que entren todos los puntos. Entrada: `puntos` = [lat,lon][].
function AutoEncuadre({ puntos }) {
  const map = useMap();
  useEffect(() => {
    if (puntos.length === 0) return;
    if (puntos.length === 1) map.setView(puntos[0], 14);
    else map.fitBounds(puntos, { padding: [40, 40] });
  }, [puntos, map]);
  return null;
}

// Centra el mapa en el conductor seleccionado al hacer clic en la lista.
function CentrarEn({ seleccionado, conductores }) {
  const map = useMap();
  useEffect(() => {
    if (seleccionado == null) return;
    const c = conductores.find((x) => x.conductor_id === seleccionado);
    if (c && c.latitud != null && c.longitud != null) map.setView([c.latitud, c.longitud], 15);
  }, [seleccionado, conductores, map]);
  return null;
}

// Mapa de la flota con OpenStreetMap (gratis, sin API key). Fallback de Google Maps.
// Entrada: `conductores` (ConductorUbicacion[] con _color), `seleccionado` (conductor_id).
export default function MapaFlotaLeaflet({ conductores, seleccionado }) {
  const puntos = [];
  conductores.forEach((c) => {
    if (c.latitud != null && c.longitud != null) puntos.push([c.latitud, c.longitud]);
    c.paradas.forEach((p) => puntos.push([p.latitud, p.longitud]));
  });

  return (
    <div className="overflow-hidden rounded-card border border-slate-200 shadow-card" style={{ height: 520 }}>
      <MapContainer center={LIMA} zoom={12} scrollWheelZoom style={{ height: "100%", width: "100%" }}>
        <TileLayer attribution="&copy; OpenStreetMap" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <AutoEncuadre puntos={puntos} />
        <CentrarEn seleccionado={seleccionado} conductores={conductores} />

        {conductores.map((c) => {
          const color = c._color || "#2563EB";
          return (
            <Fragment key={c.conductor_id}>
              {c.paradas.map((p, i) => (
                <Marker
                  key={`parada-${c.conductor_id}-${i}`}
                  position={[p.latitud, p.longitud]}
                  icon={iconoParada(color, p.secuencia ?? i + 1)}
                >
                  <Popup>
                    <b>Parada {p.secuencia ?? i + 1}</b> · {c.conductor || "Conductor"}
                    <br />
                    {p.destinatario || "Sin destinatario"}
                  </Popup>
                </Marker>
              ))}

              {c.latitud != null && c.longitud != null && (
                <CircleMarker
                  center={[c.latitud, c.longitud]}
                  radius={10}
                  pathOptions={{ color: "#FFFFFF", fillColor: color, fillOpacity: c.en_linea ? 0.95 : 0.45, weight: 3 }}
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
          );
        })}
      </MapContainer>
    </div>
  );
}
