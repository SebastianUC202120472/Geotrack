import { Fragment, useCallback, useState } from "react";
import { GoogleMap, useJsApiLoader, MarkerF, InfoWindowF } from "@react-google-maps/api";

// Centro por defecto (Lima) y estilo del contenedor del mapa.
const LIMA = { lat: -12.046, lng: -77.043 };
const ESTILO_MAPA = { width: "100%", height: "100%" };
const OPCIONES = { streetViewControl: false, mapTypeControl: false, fullscreenControl: false };

// Mensaje a pantalla completa dentro del marco del mapa (carga / error).
function Aviso({ texto }) {
  return (
    <div className="flex items-center justify-center rounded-card border border-slate-200 bg-white text-sm text-slate-500 shadow-card" style={{ height: 520 }}>
      {texto}
    </div>
  );
}

// Mapa de la flota con Google Maps (se usa cuando hay VITE_GOOGLE_MAPS_KEY).
// Entrada: `conductores` (ConductorUbicacion[]) y `apiKey` (string).
export default function MapaFlotaGoogle({ conductores, apiKey }) {
  const { isLoaded, loadError } = useJsApiLoader({ id: "gmaps-script", googleMapsApiKey: apiKey });
  const [abierto, setAbierto] = useState(null); // id del marcador con InfoWindow abierto

  // Al cargar el mapa, encuadra todos los puntos (conductores + paradas).
  const onLoad = useCallback(
    (map) => {
      const puntos = [];
      conductores.forEach((c) => {
        if (c.latitud != null && c.longitud != null) puntos.push({ lat: c.latitud, lng: c.longitud });
        c.paradas.forEach((p) => puntos.push({ lat: p.latitud, lng: p.longitud }));
      });
      if (puntos.length === 0) {
        map.setCenter(LIMA);
        map.setZoom(12);
        return;
      }
      if (puntos.length === 1) {
        map.setCenter(puntos[0]);
        map.setZoom(14);
        return;
      }
      const bounds = new window.google.maps.LatLngBounds();
      puntos.forEach((pt) => bounds.extend(pt));
      map.fitBounds(bounds, 48);
    },
    [conductores]
  );

  if (loadError) return <Aviso texto="No se pudo cargar Google Maps. Revisa la API key." />;
  if (!isLoaded) return <Aviso texto="Cargando mapa…" />;

  // Marcador circular de color (conductor azul/gris, parada ámbar).
  const simbolo = (color) => ({
    path: window.google.maps.SymbolPath.CIRCLE,
    scale: 8,
    fillColor: color,
    fillOpacity: 0.95,
    strokeColor: "#FFFFFF",
    strokeWeight: 2,
  });

  return (
    <div className="overflow-hidden rounded-card border border-slate-200 shadow-card" style={{ height: 520 }}>
      <GoogleMap mapContainerStyle={ESTILO_MAPA} center={LIMA} zoom={12} onLoad={onLoad} options={OPCIONES}>
        {conductores.map((c) => (
          <Fragment key={c.conductor_id}>
            {c.paradas.map((p, i) => {
              const id = `parada-${c.conductor_id}-${i}`;
              return (
                <MarkerF key={id} position={{ lat: p.latitud, lng: p.longitud }} icon={simbolo("#F59E0B")} onClick={() => setAbierto(id)}>
                  {abierto === id && (
                    <InfoWindowF onCloseClick={() => setAbierto(null)}>
                      <div style={{ fontSize: 13 }}>
                        <b>Parada {p.secuencia ?? "—"}</b>
                        <br />
                        {p.destinatario || "Sin destinatario"}
                      </div>
                    </InfoWindowF>
                  )}
                </MarkerF>
              );
            })}

            {c.latitud != null && c.longitud != null && (
              <MarkerF
                position={{ lat: c.latitud, lng: c.longitud }}
                icon={simbolo(c.en_linea ? "#2563EB" : "#94A3B8")}
                onClick={() => setAbierto(`cond-${c.conductor_id}`)}
              >
                {abierto === `cond-${c.conductor_id}` && (
                  <InfoWindowF onCloseClick={() => setAbierto(null)}>
                    <div style={{ fontSize: 13 }}>
                      <b>{c.conductor || "Conductor"}</b>
                      <br />
                      {c.ruta || "Ruta"}
                      <br />
                      {c.en_linea ? "🟢 En línea" : "⚪ Sin señal reciente"}
                    </div>
                  </InfoWindowF>
                )}
              </MarkerF>
            )}
          </Fragment>
        ))}
      </GoogleMap>
    </div>
  );
}
