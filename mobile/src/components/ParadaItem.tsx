// Fila de una parada: número de secuencia, destinatario, dirección y estado.
// Táctil para abrir el detalle.
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme, fontSize, radius, spacing } from "@/theme";
import { EstadoBadge } from "./EstadoBadge";
import type { ParadaManifiesto } from "@/types/api";

interface Props {
  parada: ParadaManifiesto; // datos de la parada
  onPress: () => void; // acción al tocar la fila
}

// Recibe: { parada: ParadaManifiesto, onPress: () => void }.
export function ParadaItem({ parada, onPress }: Props) {
  const { colors } = useTheme();
  const titulo = parada.nombre_destinatario || parada.cliente_origen;
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={`Parada ${parada.secuencia}: ${titulo}`}
      style={({ pressed }) => [
        estilos.fila,
        { backgroundColor: colors.surface, borderColor: colors.border },
        pressed && { opacity: 0.85 },
      ]}
    >
      <View style={[estilos.numero, { backgroundColor: colors.brand }]}>
        <Text style={[estilos.numeroTexto, { color: colors.white }]}>{parada.secuencia || "•"}</Text>
      </View>
      <View style={estilos.centro}>
        <Text style={[estilos.titulo, { color: colors.ink }]} numberOfLines={1}>{titulo}</Text>
        <Text style={[estilos.direccion, { color: colors.muted }]} numberOfLines={2}>{parada.direccion_destino}</Text>
        <EstadoBadge estado={parada.estado_entrega} />
      </View>
    </Pressable>
  );
}

const estilos = StyleSheet.create({
  fila: { flexDirection: "row", gap: spacing.md, borderRadius: radius.lg, borderWidth: 1, padding: spacing.lg },
  numero: { width: 36, height: 36, borderRadius: radius.pill, alignItems: "center", justifyContent: "center" },
  numeroTexto: { fontWeight: "800", fontSize: fontSize.body },
  centro: { flex: 1, gap: spacing.xs },
  titulo: { fontSize: fontSize.subtitle, fontWeight: "700" },
  direccion: { fontSize: fontSize.body },
});
