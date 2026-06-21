import MapaFlotaLeaflet from "./MapaFlotaLeaflet";
import MapaFlotaGoogle from "./MapaFlotaGoogle";

// Mapa de la flota. Híbrido: si hay clave de Google Maps (VITE_GOOGLE_MAPS_KEY)
// usa Google Maps; si no, cae a OpenStreetMap/Leaflet (gratis, sin clave).
// Entrada: `conductores` (ConductorUbicacion[]). "Pega la clave y funciona".
const GMAPS_KEY = import.meta.env.VITE_GOOGLE_MAPS_KEY;

export default function MapaFlota({ conductores, seleccionado }) {
  if (GMAPS_KEY) return <MapaFlotaGoogle conductores={conductores} apiKey={GMAPS_KEY} seleccionado={seleccionado} />;
  return <MapaFlotaLeaflet conductores={conductores} seleccionado={seleccionado} />;
}
