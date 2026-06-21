// Abre la navegación real a un destino directamente en Google Maps por deep link.
// No usa ninguna API ni clave: solo manda al usuario a la dirección exacta.
import { Alert, Linking } from "react-native";

// Abre el destino (lat/lng) en Google Maps. Recibe coordenadas y una etiqueta
// opcional (ya no se usa para preguntar app). No devuelve nada (efecto externo).
export function abrirNavegacion(latitud: number, longitud: number, _etiqueta?: string): void {
  const googleMaps = `https://www.google.com/maps/dir/?api=1&destination=${latitud},${longitud}`;
  Linking.openURL(googleMaps).catch(() => {
    Alert.alert("No se pudo abrir", "No se pudo abrir Google Maps en este dispositivo.");
  });
}
