import MapaFlotaLeaflet from "./MapaFlotaLeaflet";
import MapaFlotaGoogle from "./MapaFlotaGoogle";

// Selector de mapa de flota: Google Maps si hay VITE_GOOGLE_MAPS_KEY, si no OSM/Leaflet. Recibe conductores, seleccionado, mostrar.
const GMAPS_KEY = import.meta.env.VITE_GOOGLE_MAPS_KEY;

export default function MapaFlota({ conductores, seleccionado, mostrar = "TODO" }) {
  if (GMAPS_KEY) return <MapaFlotaGoogle conductores={conductores} apiKey={GMAPS_KEY} seleccionado={seleccionado} mostrar={mostrar} />;
  return <MapaFlotaLeaflet conductores={conductores} seleccionado={seleccionado} mostrar={mostrar} />;
}
