// Mapa con la secuencia de paradas (marcadores numerados), la línea del
// recorrido y la ubicación del conductor.
import { Platform, StyleSheet, Text, View } from "react-native";
import MapView, { Marker, Polyline, UrlTile, PROVIDER_GOOGLE } from "react-native-maps";
import { useTheme, fontSize, radius } from "@/theme";
import type { ParadaNavegacion } from "@/types/api";

interface Props {
  paradas: ParadaNavegacion[]; // paradas con coordenadas, en orden de secuencia
  alto?: number; // alto del mapa en píxeles (por defecto 240)
}

// Región que encuadra todos los puntos. Recibe: paradas. Devuelve la región.
function regionQueEncuadra(paradas: ParadaNavegacion[]) {
  const lats = paradas.map((p) => p.latitud);
  const lngs = paradas.map((p) => p.longitud);
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);
  const minLng = Math.min(...lngs);
  const maxLng = Math.max(...lngs);
  return {
    latitude: (minLat + maxLat) / 2,
    longitude: (minLng + maxLng) / 2,
    latitudeDelta: Math.max(0.02, (maxLat - minLat) * 1.5),
    longitudeDelta: Math.max(0.02, (maxLng - minLng) * 1.5),
  };
}

// Mapa de la ruta. Recibe: { paradas: ParadaNavegacion[], alto?: number }.
export function MapaRuta({ paradas, alto = 240 }: Props) {
  const { colors } = useTheme();

  if (paradas.length === 0) {
    return (
      <View style={[estilos.vacio, { height: alto, backgroundColor: colors.surface, borderColor: colors.border }]}>
        <Text style={{ color: colors.muted, textAlign: "center", fontSize: fontSize.body }}>
          Aún no hay paradas con ubicación para mostrar en el mapa.
        </Text>
      </View>
    );
  }

  // Con clave de Google usamos el mapa nativo (Google en Android). Sin clave,
  // superponemos tiles de OpenStreetMap como respaldo (igual que el panel web).
  const hayClaveGoogle = !!process.env.EXPO_PUBLIC_GOOGLE_MAPS_KEY;
  const provider = hayClaveGoogle && Platform.OS === "android" ? PROVIDER_GOOGLE : undefined;
  const coordenadas = paradas.map((p) => ({ latitude: p.latitud, longitude: p.longitud }));

  return (
    <MapView
      provider={provider}
      style={[estilos.mapa, { height: alto }]}
      initialRegion={regionQueEncuadra(paradas)}
      showsUserLocation
      showsMyLocationButton
    >
      {/* Respaldo OpenStreetMap cuando no hay clave de Google (street de fondo). */}
      {!hayClaveGoogle && (
        <UrlTile urlTemplate="https://tile.openstreetmap.org/{z}/{x}/{y}.png" maximumZ={19} />
      )}
      <Polyline coordinates={coordenadas} strokeColor={colors.brand} strokeWidth={4} />
      {paradas.map((p) => (
        <Marker key={p.pedido_id} coordinate={{ latitude: p.latitud, longitude: p.longitud }}>
          <View style={[estilos.pin, { backgroundColor: colors.brand, borderColor: colors.white }]}>
            <Text style={[estilos.pinTexto, { color: colors.white }]}>{p.secuencia}</Text>
          </View>
        </Marker>
      ))}
    </MapView>
  );
}

const estilos = StyleSheet.create({
  mapa: { width: "100%", borderRadius: radius.lg },
  pin: { width: 30, height: 30, borderRadius: radius.pill, borderWidth: 2, alignItems: "center", justifyContent: "center" },
  pinTexto: { fontWeight: "800", fontSize: fontSize.caption },
  vacio: { borderRadius: radius.lg, borderWidth: 1, alignItems: "center", justifyContent: "center", padding: 16 },
});
