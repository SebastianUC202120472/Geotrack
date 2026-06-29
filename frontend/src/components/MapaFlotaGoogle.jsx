import { Fragment, useCallback, useEffect, useRef, useState } from "react";
import { GoogleMap, useJsApiLoader, MarkerF, InfoWindowF } from "@react-google-maps/api";

// Centro por defecto (Lima) y estilo del contenedor del mapa.
const LIMA = { lat: -12.046, lng: -77.043 };
const ESTILO_MAPA = { width: "100%", height: "100%" };
const OPCIONES = { streetViewControl: false, mapTypeControl: false, fullscreenControl: false };
// Path SVG de un pin (gota) ~24x24, punta abajo; se usa para las PARADAS.
const PIN_PATH = "M12 0C7.58 0 4 3.58 4 8c0 5.5 8 16 8 16s8-10.5 8-16c0-4.42-3.58-8-8-8z";
// Path SVG de un edificio/almacén (~24x24, base abajo); se usa para los CLIENTES corporativos.
const EDIFICIO_PATH = "M3 23V8l7-4v3l7-4v20h-5v-4h-3v4H3z";

// Mensaje a pantalla completa dentro del marco del mapa (carga / error).
function Aviso({ texto }) {
  return (
    <div className="flex items-center justify-center rounded-card border border-slate-200 bg-white text-sm text-slate-500 shadow-card" style={{ height: 520 }}>
      {texto}
    </div>
  );
}

// Leyenda flotante con los tipos de marcador del mapa. Entrada: `hayClientes`
// (bool) para mostrar u ocultar la fila de cliente corporativo.
function LeyendaMapa({ hayClientes }) {
  return (
    <div className="absolute bottom-3 right-3 z-[1] rounded-lg border border-slate-200 bg-white/95 px-3 py-2 text-xs shadow-card">
      <div className="flex items-center gap-2">
        <span className="inline-block h-3 w-3 rounded-full border border-white bg-slate-500 shadow" aria-hidden="true" />
        <span className="text-slate-600">Conductor</span>
      </div>
      <div className="mt-1 flex items-center gap-2">
        <span
          className="inline-block h-3 w-3 border border-white bg-slate-500 shadow"
          style={{ borderRadius: "50% 50% 50% 0", transform: "rotate(-45deg)" }}
          aria-hidden="true"
        />
        <span className="text-slate-600">Pedido / parada</span>
      </div>
      {hayClientes && (
        <div className="mt-1 flex items-center gap-2">
          <span
            className="inline-flex h-3.5 w-3.5 items-center justify-center rounded-[3px] border border-white bg-slate-500 shadow"
            aria-hidden="true"
          >
            <svg viewBox="0 0 24 24" width="9" height="9" fill="#fff">
              <path d="M3 21V7l7-4v4l7-4v18h-4v-4h-3v4H3z" />
            </svg>
          </span>
          <span className="text-slate-600">Cliente corporativo</span>
        </div>
      )}
    </div>
  );
}

// Mapa de la flota con Google Maps (se usa cuando hay VITE_GOOGLE_MAPS_KEY).
// Entrada: `conductores` (ConductorUbicacion[] con _color), `apiKey`, y
// `seleccionado` (conductor_id a centrar al hacer clic en la lista).
export default function MapaFlotaGoogle({ conductores, apiKey, seleccionado }) {
  const { isLoaded, loadError } = useJsApiLoader({ id: "gmaps-script", googleMapsApiKey: apiKey });
  const [abierto, setAbierto] = useState(null); // id del marcador con InfoWindow abierto
  const mapRef = useRef(null);

  // Al cargar el mapa, encuadra todos los puntos (conductores + paradas).
  const onLoad = useCallback(
    (map) => {
      mapRef.current = map;
      const puntos = [];
      conductores.forEach((c) => {
        if (c.latitud != null && c.longitud != null) puntos.push({ lat: c.latitud, lng: c.longitud });
        c.paradas.forEach((p) => puntos.push({ lat: p.latitud, lng: p.longitud }));
        // Los clientes corporativos (orígenes de recojo) también entran en el encuadre.
        (c.clientes || []).forEach((cl) => puntos.push({ lat: cl.latitud, lng: cl.longitud }));
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

  // Al seleccionar un conductor en la lista, centra el mapa en su ubicación actual.
  useEffect(() => {
    if (!mapRef.current || seleccionado == null) return;
    const c = conductores.find((x) => x.conductor_id === seleccionado);
    if (c && c.latitud != null && c.longitud != null) {
      mapRef.current.panTo({ lat: c.latitud, lng: c.longitud });
      mapRef.current.setZoom(15);
    }
  }, [seleccionado, conductores]);

  if (loadError) return <Aviso texto="No se pudo cargar Google Maps. Revisa la API key." />;
  if (!isLoaded) return <Aviso texto="Cargando mapa…" />;

  // Marcador circular (ubicación del conductor). Atenuado si no tiene señal.
  const circulo = (color, opacidad) => ({
    path: window.google.maps.SymbolPath.CIRCLE,
    scale: 8,
    fillColor: color,
    fillOpacity: opacidad,
    strokeColor: "#FFFFFF",
    strokeWeight: 2,
  });
  // Pin (gota) para una PARADA, con el color del conductor y un número de orden.
  const pinParada = (color) => ({
    path: PIN_PATH,
    fillColor: color,
    fillOpacity: 1,
    strokeColor: "#FFFFFF",
    strokeWeight: 1.5,
    scale: 1.7,
    anchor: new window.google.maps.Point(12, 23),
    labelOrigin: new window.google.maps.Point(12, 9),
  });
  // Icono de edificio/almacén para un CLIENTE corporativo (origen de recojo), con
  // el color del conductor. Distinto de la gota de parada.
  const iconoCliente = (color) => ({
    path: EDIFICIO_PATH,
    fillColor: color,
    fillOpacity: 1,
    strokeColor: "#FFFFFF",
    strokeWeight: 1.5,
    scale: 1.6,
    anchor: new window.google.maps.Point(12, 23),
  });

  // ¿Hay algún cliente corporativo? Solo entonces se muestra su fila en la leyenda.
  const hayClientes = conductores.some((c) => (c.clientes || []).length > 0);

  return (
    <div className="relative overflow-hidden rounded-card border border-slate-200 shadow-card" style={{ height: 520 }}>
      {/* Leyenda de los tipos de marcador (encima del mapa) */}
      <LeyendaMapa hayClientes={hayClientes} />
      <GoogleMap mapContainerStyle={ESTILO_MAPA} center={LIMA} zoom={12} onLoad={onLoad} options={OPCIONES}>
        {conductores.map((c) => {
          const color = c._color || "#2563EB";
          return (
            <Fragment key={c.conductor_id}>
              {c.paradas.map((p, i) => {
                const id = `parada-${c.conductor_id}-${i}`;
                const orden = p.secuencia ?? i + 1;
                return (
                  <MarkerF
                    key={id}
                    position={{ lat: p.latitud, lng: p.longitud }}
                    icon={pinParada(color)}
                    label={{ text: String(orden), color: "#FFFFFF", fontSize: "10px", fontWeight: "700" }}
                    onClick={() => setAbierto(id)}
                  >
                    {abierto === id && (
                      <InfoWindowF onCloseClick={() => setAbierto(null)}>
                        <div style={{ fontSize: 13 }}>
                          <b>Parada {orden}</b> · {c.conductor || "Conductor"}
                          <br />
                          {p.destinatario || "Sin destinatario"}
                        </div>
                      </InfoWindowF>
                    )}
                  </MarkerF>
                );
              })}

              {/* Clientes corporativos (orígenes de recojo) — icono de edificio */}
              {(c.clientes || []).map((cl, i) => {
                const id = `cliente-${c.conductor_id}-${i}`;
                return (
                  <MarkerF
                    key={id}
                    position={{ lat: cl.latitud, lng: cl.longitud }}
                    icon={iconoCliente(color)}
                    onClick={() => setAbierto(id)}
                  >
                    {abierto === id && (
                      <InfoWindowF onCloseClick={() => setAbierto(null)}>
                        <div style={{ fontSize: 13 }}>
                          <b>{cl.razon_social || "Cliente"}</b>
                          <br />
                          Recojo · {c.conductor || "Conductor"}
                        </div>
                      </InfoWindowF>
                    )}
                  </MarkerF>
                );
              })}

              {c.latitud != null && c.longitud != null && (
                <MarkerF
                  position={{ lat: c.latitud, lng: c.longitud }}
                  icon={circulo(color, c.en_linea ? 0.95 : 0.45)}
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
          );
        })}
      </GoogleMap>
    </div>
  );
}
