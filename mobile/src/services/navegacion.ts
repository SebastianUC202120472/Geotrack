// Abre la navegación real a un destino directamente en Google Maps por deep link.
// No usa ninguna API ni clave: solo manda al usuario a la dirección exacta.
import { Alert, Linking } from "react-native";

// Google limita cuántos puntos intermedios (waypoints) admite el deep link de
// direcciones; más allá de ~9 el enlace falla. Recortamos la ruta a ese tope.
const MAX_WAYPOINTS = 9;

// Un punto de la ruta (parada con coordenadas) para armar la navegación.
export interface PuntoNavegacion {
  lat?: number | null;
  lng?: number | null;
}

// Abre el destino (lat/lng) en Google Maps. Recibe coordenadas y una etiqueta
// opcional (ya no se usa para preguntar app). No devuelve nada (efecto externo).
export function abrirNavegacion(latitud: number, longitud: number, _etiqueta?: string): void {
  abrir(`https://www.google.com/maps/dir/?api=1&destination=${latitud},${longitud}&travelmode=driving`);
}

// Abre la RUTA completa en Google Maps con indicaciones turn-by-turn: usa la
// ubicación actual como origen (Google la resuelve solo), la última parada como
// destino y las intermedias como waypoints (en orden, con tope MAX_WAYPOINTS).
// Recibe la lista de paradas ya ordenada; efecto externo, no devuelve nada.
export function abrirNavegacionRuta(puntos: PuntoNavegacion[]): void {
  const validos = puntos.filter((p): p is { lat: number; lng: number } => p.lat != null && p.lng != null);
  if (validos.length === 0) {
    Alert.alert("Sin ubicaciones", "Las paradas aún no tienen coordenadas para navegar.");
    return;
  }
  // Con una sola parada, es una navegación directa (sin waypoints).
  if (validos.length === 1) {
    abrirNavegacion(validos[0].lat, validos[0].lng);
    return;
  }
  // Toma como mucho MAX_WAYPOINTS intermedias + 1 destino (recorta el resto).
  const usados = validos.slice(0, MAX_WAYPOINTS + 1);
  const destino = usados[usados.length - 1];
  const intermedias = usados.slice(0, -1).map((p) => `${p.lat},${p.lng}`).join("|");
  const url =
    `https://www.google.com/maps/dir/?api=1&destination=${destino.lat},${destino.lng}` +
    `&waypoints=${encodeURIComponent(intermedias)}&travelmode=driving`;
  abrir(url);
}

// Abre una URL externa (Google Maps) avisando si el dispositivo no puede.
function abrir(url: string): void {
  Linking.openURL(url).catch(() => {
    Alert.alert("No se pudo abrir", "No se pudo abrir Google Maps en este dispositivo.");
  });
}
