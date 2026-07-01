import { Fragment, useCallback, useEffect, useRef, useState } from "react";
import { GoogleMap, useJsApiLoader, MarkerF, InfoWindowF, PolylineF } from "@react-google-maps/api";
import { haceCuanto } from "../utils/formatoFecha";

const LIMA = { lat: -12.046, lng: -77.043 };
const ESTILO_MAPA = { width: "100%", height: "100%" };
const OPCIONES = { streetViewControl: false, mapTypeControl: false, fullscreenControl: false };
const PIN_PATH = "M12 0C7.58 0 4 3.58 4 8c0 5.5 8 16 8 16s8-10.5 8-16c0-4.42-3.58-8-8-8z";
const EDIFICIO_PATH = "M3 23V8l7-4v3l7-4v20h-5v-4h-3v4H3z";
const COLOR_PENDIENTE = "#2563eb";
const COLOR_ENTREGADO = "#16a34a";
const COLOR_FALLIDO = "#dc2626";

// Devuelve el color de marcador segun el estado de entrega de una parada.
function colorPorEstado(estado) {
  const e = (estado || "PENDIENTE").toUpperCase();
  if (e === "ENTREGADO") return COLOR_ENTREGADO;
  if (e === "FALLIDO") return COLOR_FALLIDO;
  return COLOR_PENDIENTE;
}

// Mensaje centrado en el area del mapa. Recibe `texto`.
function Aviso({ texto }) {
  return (
    <div className="flex items-center justify-center rounded-card border border-slate-200 bg-white text-sm text-slate-500 shadow-card" style={{ height: 520 }}>
      {texto}
    </div>
  );
}

// Leyenda flotante de tipos de marcador. Recibe `hayClientes` para mostrar u ocultar esa fila.
function LeyendaMapa({ hayClientes }) {
  return (
    <div className="absolute bottom-3 right-3 z-[1] rounded-lg border border-slate-200 bg-white/95 px-3 py-2 text-xs shadow-card">
      <div className="flex items-center gap-2">
        <span className="inline-block h-3 w-3 rounded-full border border-white bg-slate-500 shadow" aria-hidden="true" />
        <span className="text-slate-600">Conductor</span>
      </div>
      <div className="mt-1 flex items-center gap-2">
        <span
          className="inline-block h-3 w-3 border border-white shadow"
          style={{ borderRadius: "50% 50% 50% 0", transform: "rotate(-45deg)", background: COLOR_PENDIENTE }}
          aria-hidden="true"
        />
        <span className="text-slate-600">Parada pendiente</span>
      </div>
      <div className="mt-1 flex items-center gap-2">
        <span
          className="inline-block h-3 w-3 border border-white shadow"
          style={{ borderRadius: "50% 50% 50% 0", transform: "rotate(-45deg)", background: COLOR_ENTREGADO }}
          aria-hidden="true"
        />
        <span className="text-slate-600">Entregado</span>
      </div>
      <div className="mt-1 flex items-center gap-2">
        <span
          className="inline-block h-3 w-3 border border-white shadow"
          style={{ borderRadius: "50% 50% 50% 0", transform: "rotate(-45deg)", background: COLOR_FALLIDO }}
          aria-hidden="true"
        />
        <span className="text-slate-600">Fallido</span>
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

// Mapa de flota con Google Maps. Recibe `conductores`, `apiKey`, `seleccionado` y `mostrar` ("TODO"|"CONDUCTORES"|"PEDIDOS").
export default function MapaFlotaGoogle({ conductores, apiKey, seleccionado, mostrar = "TODO" }) {
  const { isLoaded, loadError } = useJsApiLoader({ id: "gmaps-script", googleMapsApiKey: apiKey });
  const [abierto, setAbierto] = useState(null); // id del marcador con InfoWindow abierto
  const mapRef = useRef(null);

  // Ajusta el encuadre del mapa para mostrar todos los puntos al cargar.
  const onLoad = useCallback(
    (map) => {
      mapRef.current = map;
      const puntos = [];
      conductores.forEach((c) => {
        if (c.latitud != null && c.longitud != null) puntos.push({ lat: c.latitud, lng: c.longitud });
        c.paradas.forEach((p) => puntos.push({ lat: p.latitud, lng: p.longitud }));
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

  // Centra el mapa en el conductor seleccionado.
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

  // Icono circular para la ubicacion del conductor.
  const circulo = (color, opacidad) => ({
    path: window.google.maps.SymbolPath.CIRCLE,
    scale: 8,
    fillColor: color,
    fillOpacity: opacidad,
    strokeColor: "#FFFFFF",
    strokeWeight: 2,
  });
  // Icono de gota para una parada. Recibe el color segun estado.
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
  // Icono de edificio para un cliente corporativo (origen de recojo).
  const iconoCliente = (color) => ({
    path: EDIFICIO_PATH,
    fillColor: color,
    fillOpacity: 1,
    strokeColor: "#FFFFFF",
    strokeWeight: 1.5,
    scale: 1.6,
    anchor: new window.google.maps.Point(12, 23),
  });

  const hayClientes = conductores.some((c) => (c.clientes || []).length > 0);

  return (
    <div className="relative overflow-hidden rounded-card border border-slate-200 shadow-card" style={{ height: 520 }}>
      <LeyendaMapa hayClientes={hayClientes} />
      <GoogleMap mapContainerStyle={ESTILO_MAPA} center={LIMA} zoom={12} onLoad={onLoad} options={OPCIONES}>
        {conductores.map((c) => {
          const color = c._color || "#2563EB";
          return (
            <Fragment key={c.conductor_id}>
              {seleccionado != null && mostrar !== "CONDUCTORES" && c.paradas.length >= 2 && (
                <PolylineF
                  path={c.paradas.map((p) => ({ lat: p.latitud, lng: p.longitud }))}
                  options={{ strokeColor: color, strokeOpacity: 0.8, strokeWeight: 4 }}
                />
              )}
              {mostrar !== "CONDUCTORES" && c.paradas.map((p, i) => {
                const id = `parada-${c.conductor_id}-${i}`;
                const orden = p.secuencia ?? i + 1;
                return (
                  <MarkerF
                    key={id}
                    position={{ lat: p.latitud, lng: p.longitud }}
                    icon={pinParada(colorPorEstado(p.estado))}
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

              {mostrar !== "CONDUCTORES" && (c.clientes || []).map((cl, i) => {
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

              {mostrar !== "PEDIDOS" && c.latitud != null && c.longitud != null && (
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
                        {c.actualizado_en && (
                          <>
                            <br />
                            Última señal {haceCuanto(c.actualizado_en)}
                          </>
                        )}
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
