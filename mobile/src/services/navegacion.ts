// Abre la navegación real en una app externa (Google Maps o Waze) por deep link.
// No usa ninguna API ni clave: solo manda al usuario a la dirección exacta.
import { Alert, Linking } from "react-native";

// Pregunta a qué app navegar y abre el destino (lat/lng). Recibe coordenadas y
// una etiqueta opcional para el título. No devuelve nada (efecto externo).
export function abrirNavegacion(latitud: number, longitud: number, etiqueta?: string): void {
  const googleMaps = `https://www.google.com/maps/dir/?api=1&destination=${latitud},${longitud}`;
  const waze = `https://waze.com/ul?ll=${latitud},${longitud}&navigate=yes`;

  Alert.alert(
    "Navegar",
    etiqueta ? `Ir a: ${etiqueta}` : "Abrir la dirección en:",
    [
      { text: "Google Maps", onPress: () => Linking.openURL(googleMaps) },
      { text: "Waze", onPress: () => Linking.openURL(waze) },
      { text: "Cancelar", style: "cancel" },
    ],
    { cancelable: true }
  );
}
