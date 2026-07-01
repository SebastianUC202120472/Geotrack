// Mapa nativo de la ruta con Google Maps. Recibe paradas y las pinta con marcadores coloreados por estado.
import { useEffect, useMemo, useRef, useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import MapView, { Marker, Callout, Polyline, PROVIDER_GOOGLE, type Region } from "react-native-maps";
import { Ionicons } from "@expo/vector-icons";
import { useTheme, fontSize, radius } from "@/theme";
import type { ParadaManifiesto } from "@/types/api";

// Calcula el rumbo en grados entre dos coordenadas. Recibe lat/lng de origen y destino.
function rumbo(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const rad = Math.PI / 180;
  const dLon = (lon2 - lon1) * rad;
  const y = Math.sin(dLon) * Math.cos(lat2 * rad);
  const x =
    Math.cos(lat1 * rad) * Math.sin(lat2 * rad) -
    Math.sin(lat1 * rad) * Math.cos(lat2 * rad) * Math.cos(dLon);
  return (Math.atan2(y, x) * 180) / Math.PI;
}

interface Props {
  paradas: ParadaManifiesto[]; // paradas (con lat/lng) de la ruta
  alto?: number; // alto del mapa en píxeles (por defecto 260)
}

interface PuntoMapa {
  lat: number;
  lng: number;
  sec: number;
  estado: string;
  dest: string;
  dir: string;
  esSiguiente: boolean; // primera parada PENDIENTE de la secuencia
}

// Devuelve color hex del pin según estado y si es la siguiente parada pendiente.
function colorPorEstado(estado: string, esSiguiente: boolean): string {
  if (estado === "ENTREGADO") return "#16a34a"; // verde
  if (estado === "FALLIDO") return "#dc2626"; // rojo
  return esSiguiente ? "#2563eb" : "#60a5fa";
}

// Calcula la Region que enmarca todos los puntos dados. Recibe lista de puntos (>=1).
function regionQueEnmarca(puntos: PuntoMapa[]): Region {
  const lats = puntos.map((p) => p.lat);
  const lngs = puntos.map((p) => p.lng);
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);
  const minLng = Math.min(...lngs);
  const maxLng = Math.max(...lngs);
  const latDelta = Math.max((maxLat - minLat) * 1.4, 0.02);
  const lngDelta = Math.max((maxLng - minLng) * 1.4, 0.02);
  return {
    latitude: (minLat + maxLat) / 2,
    longitude: (minLng + maxLng) / 2,
    latitudeDelta: latDelta,
    longitudeDelta: lngDelta,
  };
}

// Componente principal del mapa nativo. Recibe { paradas, alto? }.
export function MapaNativo({ paradas, alto = 260 }: Props) {
  const { colors } = useTheme();
  const mapRef = useRef<MapView | null>(null);

  const puntos = useMemo<PuntoMapa[]>(() => {
    let siguienteUsada = false;
    return paradas
      .filter((p) => p.latitud != null && p.longitud != null)
      .slice()
      .sort((a, b) => a.secuencia - b.secuencia)
      .map((p) => {
        const pendiente = p.estado_entrega === "PENDIENTE";
        const esSiguiente = pendiente && !siguienteUsada;
        if (esSiguiente) siguienteUsada = true;
        return {
          lat: p.latitud as number,
          lng: p.longitud as number,
          sec: p.secuencia,
          estado: p.estado_entrega,
          dest: p.nombre_destinatario || p.cliente_origen,
          dir: p.direccion_destino,
          esSiguiente,
        };
      });
  }, [paradas]);

  // Activa tracksViewChanges brevemente para que Android rasterice los marcadores custom.
  const [rastrearVistas, setRastrearVistas] = useState(true);
  useEffect(() => {
    setRastrearVistas(true);
    const t = setTimeout(() => setRastrearVistas(false), 1200);
    return () => clearTimeout(t);
  }, [puntos]);

  if (puntos.length === 0) {
    return (
      <View style={[estilos.vacio, { height: alto, backgroundColor: colors.surface, borderColor: colors.border }]}>
        <Text style={{ color: colors.muted, textAlign: "center", fontSize: fontSize.body }}>
          Aún no hay paradas con ubicación para mostrar en el mapa.
        </Text>
      </View>
    );
  }

  const region = regionQueEnmarca(puntos);

  // Ajusta el encuadre del mapa para mostrar todas las paradas.
  const ajustarEncuadre = () => {
    if (puntos.length < 2) return;
    mapRef.current?.fitToCoordinates(
      puntos.map((p) => ({ latitude: p.lat, longitude: p.lng })),
      { edgePadding: { top: 50, right: 50, bottom: 50, left: 50 }, animated: false }
    );
  };

  return (
    <View style={[estilos.caja, { height: alto, borderColor: colors.border }]}>
      <MapView
        ref={mapRef}
        provider={PROVIDER_GOOGLE}
        style={StyleSheet.absoluteFill}
        initialRegion={region}
        showsUserLocation
        showsMyLocationButton
        onMapReady={ajustarEncuadre}
      >
        {puntos.length > 1 && (
          <Polyline
            coordinates={puntos.map((p) => ({ latitude: p.lat, longitude: p.lng }))}
            strokeColor="#2563eb"
            strokeWidth={4}
          />
        )}
        {puntos.slice(0, -1).map((p, i) => {
          const q = puntos[i + 1];
          const medio = { latitude: (p.lat + q.lat) / 2, longitude: (p.lng + q.lng) / 2 };
          return (
            <Marker
              key={`flecha-${p.sec}-${i}`}
              coordinate={medio}
              anchor={{ x: 0.5, y: 0.5 }}
              flat
              rotation={rumbo(p.lat, p.lng, q.lat, q.lng)}
              tracksViewChanges={rastrearVistas}
            >
              <Ionicons name="caret-up" size={20} color="#1d4ed8" />
            </Marker>
          );
        })}
        {puntos.map((p, i) => {
          const color = colorPorEstado(p.estado, p.esSiguiente);
          const tam = p.esSiguiente ? 38 : 30;
          return (
            <Marker
              key={`${p.sec}-${i}`}
              coordinate={{ latitude: p.lat, longitude: p.lng }}
              anchor={{ x: 0.5, y: 0.5 }}
              title={`${p.sec}. ${p.dest}`}
              tracksViewChanges={rastrearVistas}
            >
              <View
                style={[
                  estilos.pin,
                  { width: tam, height: tam, borderRadius: tam / 2, backgroundColor: color },
                ]}
              >
                <Text style={[estilos.pinTexto, { fontSize: p.esSiguiente ? 15 : 13 }]}>{p.sec}</Text>
              </View>
              <Callout tooltip={false}>
                <View style={estilos.callout}>
                  <Text style={estilos.calloutTitulo}>{`${p.sec}. ${p.dest}`}</Text>
                  {!!p.dir && <Text style={estilos.calloutDir}>{p.dir}</Text>}
                </View>
              </Callout>
            </Marker>
          );
        })}
      </MapView>
    </View>
  );
}

const estilos = StyleSheet.create({
  caja: { borderRadius: radius.lg, borderWidth: 1, overflow: "hidden" },
  vacio: { borderRadius: radius.lg, borderWidth: 1, alignItems: "center", justifyContent: "center", padding: 16 },
  pin: {
    alignItems: "center",
    justifyContent: "center",
    borderWidth: 2,
    borderColor: "#ffffff",
    shadowColor: "#000",
    shadowOpacity: 0.3,
    shadowRadius: 2,
    shadowOffset: { width: 0, height: 1 },
    elevation: 3,
  },
  pinTexto: { color: "#ffffff", fontWeight: "700" },
  callout: { maxWidth: 220, paddingVertical: 2 },
  calloutTitulo: { fontWeight: "700", color: "#0f172a", fontSize: 14 },
  calloutDir: { color: "#475569", fontSize: 12, marginTop: 2 },
});
