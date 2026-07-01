import { Alert, Linking } from "react-native";

// Limite de waypoints intermedios que acepta el deep link de Google Maps.
const MAX_WAYPOINTS = 9;

export interface PuntoNavegacion {
  lat?: number | null;
  lng?: number | null;
}

// Abre una parada en Google Maps por deep link. Recibe lat, lng y etiqueta opcional.
export function abrirNavegacion(latitud: number, longitud: number, _etiqueta?: string): void {
  abrir(`https://www.google.com/maps/dir/?api=1&destination=${latitud},${longitud}&travelmode=driving`);
}

// Abre la ruta completa en Google Maps con waypoints. Recibe lista de paradas ordenada.
export function abrirNavegacionRuta(puntos: PuntoNavegacion[]): void {
  const validos = puntos.filter((p): p is { lat: number; lng: number } => p.lat != null && p.lng != null);
  if (validos.length === 0) {
    Alert.alert("Sin ubicaciones", "Las paradas aún no tienen coordenadas para navegar.");
    return;
  }
  if (validos.length === 1) {
    abrirNavegacion(validos[0].lat, validos[0].lng);
    return;
  }
  const usados = validos.slice(0, MAX_WAYPOINTS + 1);
  const destino = usados[usados.length - 1];
  const intermedias = usados.slice(0, -1).map((p) => `${p.lat},${p.lng}`).join("|");
  const url =
    `https://www.google.com/maps/dir/?api=1&destination=${destino.lat},${destino.lng}` +
    `&waypoints=${encodeURIComponent(intermedias)}&travelmode=driving`;
  abrir(url);
}

// Abre una URL con Linking y muestra alerta si falla.
function abrir(url: string): void {
  Linking.openURL(url).catch(() => {
    Alert.alert("No se pudo abrir", "No se pudo abrir Google Maps en este dispositivo.");
  });
}
