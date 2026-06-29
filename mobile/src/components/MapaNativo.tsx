// Mapa NATIVO de la ruta con Google Maps (react-native-maps). Reemplaza al
// WebView+Leaflet (MapaWeb) en el build de desarrollo: dibuja un marcador por
// cada parada coloreado según su estado (pendiente/entregado/fallido) y resalta
// la siguiente pendiente. Necesita la clave de Google (app.config.js) y NO
// funciona en Expo Go (requiere dev build).
import { useMemo, useRef } from "react";
import { StyleSheet, Text, View } from "react-native";
import MapView, { Marker, Callout, PROVIDER_GOOGLE, type Region } from "react-native-maps";
import { useTheme, fontSize, radius } from "@/theme";
import type { ParadaManifiesto } from "@/types/api";

interface Props {
  paradas: ParadaManifiesto[]; // paradas (con lat/lng) de la ruta
  alto?: number; // alto del mapa en píxeles (por defecto 260)
}

// Punto ya validado y normalizado para pintar en el mapa.
interface PuntoMapa {
  lat: number;
  lng: number;
  sec: number;
  estado: string;
  dest: string;
  dir: string;
  esSiguiente: boolean; // primera parada PENDIENTE de la secuencia
}

// Color del pin según el estado de entrega. Recibe: estado y si es la siguiente
// pendiente. Devuelve: un color hex válido para `pinColor` de <Marker>.
function colorPorEstado(estado: string, esSiguiente: boolean): string {
  if (estado === "ENTREGADO") return "#16a34a"; // verde
  if (estado === "FALLIDO") return "#dc2626"; // rojo
  // Pendiente: la siguiente se resalta en azul; las demás en azul más claro.
  return esSiguiente ? "#2563eb" : "#60a5fa";
}

// Calcula una región (centro + deltas) que enmarque todos los puntos. Recibe:
// la lista de puntos (>=1). Devuelve: una Region para `initialRegion`.
function regionQueEnmarca(puntos: PuntoMapa[]): Region {
  const lats = puntos.map((p) => p.lat);
  const lngs = puntos.map((p) => p.lng);
  const minLat = Math.min(...lats);
  const maxLat = Math.max(...lats);
  const minLng = Math.min(...lngs);
  const maxLng = Math.max(...lngs);
  // Margen para que los pines no queden pegados al borde.
  const latDelta = Math.max((maxLat - minLat) * 1.4, 0.02);
  const lngDelta = Math.max((maxLng - minLng) * 1.4, 0.02);
  return {
    latitude: (minLat + maxLat) / 2,
    longitude: (minLng + maxLng) / 2,
    latitudeDelta: latDelta,
    longitudeDelta: lngDelta,
  };
}

// Mapa de calles nativo de la ruta. Recibe: { paradas, alto? }.
export function MapaNativo({ paradas, alto = 260 }: Props) {
  const { colors } = useTheme();
  const mapRef = useRef<MapView | null>(null);

  // Normaliza: solo paradas con coords, ordenadas por secuencia, marcando la
  // primera PENDIENTE como "siguiente".
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

  // Al terminar de montar el mapa, ajusta el encuadre a todas las paradas.
  const ajustarEncuadre = () => {
    if (puntos.length < 2) return; // con un solo punto basta initialRegion
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
        {puntos.map((p, i) => {
          // Marcador PERSONALIZADO: círculo de color con el NÚMERO del pedido dentro
          // (como en el panel web). La siguiente parada se dibuja más grande para destacarla.
          const color = colorPorEstado(p.estado, p.esSiguiente);
          const tam = p.esSiguiente ? 38 : 30;
          return (
            <Marker
              key={`${p.sec}-${i}`}
              coordinate={{ latitude: p.lat, longitude: p.lng }}
              anchor={{ x: 0.5, y: 0.5 }}
              title={`${p.sec}. ${p.dest}`}
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
  // Pin numerado: círculo de color con borde blanco y el número del pedido al centro.
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
