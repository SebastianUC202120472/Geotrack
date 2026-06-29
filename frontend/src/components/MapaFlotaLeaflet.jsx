import { Fragment, useEffect } from "react";
import { MapContainer, TileLayer, CircleMarker, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Centro por defecto (Lima) cuando todavía no hay puntos que mostrar.
const LIMA = [-12.046, -77.043];

// Colores de la gota de parada según su estado de entrega.
const COLOR_PENDIENTE = "#2563eb";
const COLOR_ENTREGADO = "#16a34a";
const COLOR_FALLIDO = "#dc2626";

// Devuelve el color de una parada según su `estado` (estado_entrega).
// Entrada: `estado` = "PENDIENTE" | "ENTREGADO" | "FALLIDO" (vacío = pendiente).
const colorPorEstado = (estado) => {
  const e = (estado || "PENDIENTE").toUpperCase();
  if (e === "ENTREGADO") return COLOR_ENTREGADO;
  if (e === "FALLIDO") return COLOR_FALLIDO;
  return COLOR_PENDIENTE;
};

// Pin (gota) para una PARADA: color de su estado de entrega + número de orden.
// Distinto del círculo de la ubicación del conductor.
const iconoParada = (color, n) =>
  L.divIcon({
    className: "",
    html: `<div style="background:${color};width:24px;height:24px;border-radius:50% 50% 50% 0;transform:rotate(-45deg);border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center"><span style="transform:rotate(45deg);color:#fff;font-size:11px;font-weight:700">${n}</span></div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 24],
  });

// Icono de CLIENTE CORPORATIVO (origen de recojo): cuadrado redondeado del color
// del conductor con un SVG de edificio/almacén. Distinto de la gota de parada.
// Entrada: `color` = color del conductor.
const iconoCliente = (color) =>
  L.divIcon({
    className: "",
    html: `<div style="background:${color};width:28px;height:28px;border-radius:7px;border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center"><svg viewBox="0 0 24 24" width="16" height="16" fill="#fff" aria-hidden="true"><path d="M3 21V7l7-4v4l7-4v18h-4v-4h-3v4H3zm2-2h3v-3H5v3zm0-5h3v-3H5v3zm0-5h3V6H5v3zm5 10h3v-3h-3v3zm0-5h3v-3h-3v3zm0-5h3V6h-3v3zm5 10h2v-3h-2v3zm0-5h2v-3h-2v3z"/></svg></div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 28],
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

// Leyenda flotante con los tipos de marcador del mapa. Entrada: `hayClientes`
// (bool) para mostrar u ocultar la fila de cliente corporativo.
function LeyendaMapa({ hayClientes }) {
  return (
    <div className="absolute bottom-3 right-3 z-[1000] rounded-lg border border-slate-200 bg-white/95 px-3 py-2 text-xs shadow-card">
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

// Mapa de la flota con OpenStreetMap (gratis, sin API key). Fallback de Google Maps.
// Entrada: `conductores` (ConductorUbicacion[] con _color), `seleccionado` (conductor_id).
export default function MapaFlotaLeaflet({ conductores, seleccionado }) {
  const puntos = [];
  conductores.forEach((c) => {
    if (c.latitud != null && c.longitud != null) puntos.push([c.latitud, c.longitud]);
    c.paradas.forEach((p) => puntos.push([p.latitud, p.longitud]));
    // Los clientes corporativos (orígenes de recojo) también entran en el encuadre.
    (c.clientes || []).forEach((cl) => puntos.push([cl.latitud, cl.longitud]));
  });

  // ¿Hay algún cliente corporativo? Solo entonces se muestra su fila en la leyenda.
  const hayClientes = conductores.some((c) => (c.clientes || []).length > 0);

  return (
    <div className="relative overflow-hidden rounded-card border border-slate-200 shadow-card" style={{ height: 520 }}>
      {/* Leyenda de los tipos de marcador (encima del mapa) */}
      <LeyendaMapa hayClientes={hayClientes} />
      <MapContainer center={LIMA} zoom={12} scrollWheelZoom style={{ height: "100%", width: "100%" }}>
        <TileLayer attribution="&copy; OpenStreetMap" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <AutoEncuadre puntos={puntos} />
        <CentrarEn seleccionado={seleccionado} conductores={conductores} />

        {conductores.map((c) => {
          const color = c._color || "#2563EB";
          return (
            <Fragment key={c.conductor_id}>
              {/* El color de la gota sale del estado de entrega (no del conductor). */}
              {c.paradas.map((p, i) => (
                <Marker
                  key={`parada-${c.conductor_id}-${i}`}
                  position={[p.latitud, p.longitud]}
                  icon={iconoParada(colorPorEstado(p.estado), p.secuencia ?? i + 1)}
                >
                  <Popup>
                    <b>Parada {p.secuencia ?? i + 1}</b> · {c.conductor || "Conductor"}
                    <br />
                    {p.destinatario || "Sin destinatario"}
                  </Popup>
                </Marker>
              ))}

              {/* Clientes corporativos (orígenes de recojo) — icono de edificio */}
              {(c.clientes || []).map((cl, i) => (
                <Marker
                  key={`cliente-${c.conductor_id}-${i}`}
                  position={[cl.latitud, cl.longitud]}
                  icon={iconoCliente(color)}
                >
                  <Popup>
                    <b>{cl.razon_social || "Cliente"}</b>
                    <br />
                    Recojo · {c.conductor || "Conductor"}
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
