// Componente del mapa versión WEB (evita importar react-native-maps que es nativo).
import { StyleSheet, Text, View } from "react-native";
import { useTheme, fontSize, radius } from "@/theme";
import type { ParadaManifiesto } from "@/types/api";

interface Props {
  paradas: ParadaManifiesto[];
  alto?: number;
}

export function MapaNativo({ paradas, alto = 260 }: Props) {
  const { colors } = useTheme();

  const puntos = paradas
    .filter((p) => p.latitud != null && p.longitud != null)
    .sort((a, b) => a.secuencia - b.secuencia);

  if (puntos.length === 0) {
    return (
      <View style={[estilos.vacio, { height: alto, backgroundColor: colors.surface, borderColor: colors.border }]}>
        <Text style={{ color: colors.muted, textAlign: "center", fontSize: fontSize.body }}>
          Aún no hay paradas con ubicación para mostrar en el mapa.
        </Text>
      </View>
    );
  }

  return (
    <View style={[estilos.caja, { height: alto, backgroundColor: colors.surface, borderColor: colors.border }]}>
      <View style={estilos.encabezado}>
        <Text style={[estilos.titulo, { color: colors.text }]}>
          🗺️ Vista Web de Ruta ({puntos.length} paradas)
        </Text>
        <Text style={[estilos.subtitulo, { color: colors.muted }]}>
          (El mapa nativo de Google Maps solo se renderiza en dispositivos Android / iOS)
        </Text>
      </View>

      <View style={estilos.listaParadas}>
        {puntos.map((p) => {
          const entregado = p.estado_entrega === "ENTREGADO";
          const fallido = p.estado_entrega === "FALLIDO";
          const colorPin = entregado ? "#16a34a" : fallido ? "#dc2626" : "#2563eb";

          return (
            <View key={p.pedido_id} style={estilos.itemParada}>
              <View style={[estilos.badge, { backgroundColor: colorPin }]}>
                <Text style={estilos.badgeTexto}>{p.secuencia}</Text>
              </View>
              <View style={estilos.infoParada}>
                <Text style={[estilos.destinatario, { color: colors.text }]}>
                  {p.nombre_destinatario || p.cliente_origen}
                </Text>
                <Text style={[estilos.direccion, { color: colors.muted }]} numberOfLines={1}>
                  {p.direccion_destino}
                </Text>
              </View>
            </View>
          );
        })}
      </View>
    </View>
  );
}

const estilos = StyleSheet.create({
  caja: { borderRadius: radius.lg, borderWidth: 1, padding: 12, justifyContent: "flex-start" },
  vacio: { borderRadius: radius.lg, borderWidth: 1, alignItems: "center", justifyContent: "center", padding: 16 },
  encabezado: { marginBottom: 12, borderBottomWidth: 1, borderBottomColor: "#e2e8f0", paddingBottom: 8 },
  titulo: { fontWeight: "700", fontSize: 14 },
  subtitulo: { fontSize: 11, marginTop: 2 },
  listaParadas: { gap: 8 },
  itemParada: { flexDirection: "row", alignItems: "center", gap: 10 },
  badge: { width: 24, height: 24, borderRadius: 12, alignItems: "center", justifyContent: "center" },
  badgeTexto: { color: "#ffffff", fontWeight: "700", fontSize: 12 },
  infoParada: { flex: 1 },
  destinatario: { fontWeight: "600", fontSize: 13 },
  direccion: { fontSize: 11 },
});
