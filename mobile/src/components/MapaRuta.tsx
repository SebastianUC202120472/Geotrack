// Mapa con la secuencia de paradas (marcadores numerados en orden), la línea
// del recorrido y la ubicación del conductor.
import { StyleSheet, Text, View } from "react-native";
import MapView, { Marker, Polyline, PROVIDER_GOOGLE } from "react-native-maps";
import { Platform } from "react-native";
import { colors, fontSize, radius } from "@/theme";
import type { ParadaNavegacion } from "@/types/api";

interface Props {
  // Paradas con coordenadas, en el orden de la secuencia.
  paradas: ParadaNavegacion[];
  // Alto del mapa en píxeles (por defecto 240).
  alto?: number;
}

// Calcula la región que encuadra todos los puntos. Recibe: paradas. Devuelve región.
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
  if (paradas.length === 0) {
    return (
      <View style={[estilos.vacio, { height: alto }]}>
        <Text style={estilos.vacioTexto}>Aún no hay paradas con ubicación para mostrar en el mapa.</Text>
      </View>
    );
  }

  // En Android usamos Google Maps; en iOS, Apple Maps (provider por defecto).
  const provider = Platform.OS === "android" ? PROVIDER_GOOGLE : undefined;
  const coordenadas = paradas.map((p) => ({ latitude: p.latitud, longitude: p.longitud }));

  return (
    <MapView
      provider={provider}
      style={[estilos.mapa, { height: alto }]}
      initialRegion={regionQueEncuadra(paradas)}
      showsUserLocation
      showsMyLocationButton
    >
      <Polyline coordinates={coordenadas} strokeColor={colors.brand} strokeWidth={4} />
      {paradas.map((p) => (
        <Marker key={p.pedido_id} coordinate={{ latitude: p.latitud, longitude: p.longitud }}>
          <View style={estilos.pin}>
            <Text style={estilos.pinTexto}>{p.secuencia}</Text>
          </View>
        </Marker>
      ))}
    </MapView>
  );
}

const estilos = StyleSheet.create({
  mapa: { width: "100%", borderRadius: radius.lg },
  pin: {
    width: 30,
    height: 30,
    borderRadius: radius.pill,
    backgroundColor: colors.brand,
    borderWidth: 2,
    borderColor: colors.white,
    alignItems: "center",
    justifyContent: "center",
  },
  pinTexto: { color: colors.white, fontWeight: "800", fontSize: fontSize.caption },
  vacio: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: "center",
    justifyContent: "center",
    padding: 16,
  },
  vacioTexto: { color: colors.muted, textAlign: "center", fontSize: fontSize.body },
});
