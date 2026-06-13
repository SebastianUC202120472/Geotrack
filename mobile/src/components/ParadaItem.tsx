// Fila de una parada en la lista de la ruta: número de secuencia, destinatario,
// dirección y estado. Es táctil para abrir el detalle.
import { Pressable, StyleSheet, Text, View } from "react-native";
import { colors, fontSize, radius, spacing } from "@/theme";
import { EstadoBadge } from "./EstadoBadge";
import type { ParadaManifiesto } from "@/types/api";

interface Props {
  // Datos de la parada a mostrar.
  parada: ParadaManifiesto;
  // Acción al tocar la fila.
  onPress: () => void;
}

// Recibe: { parada: ParadaManifiesto, onPress: () => void }.
export function ParadaItem({ parada, onPress }: Props) {
  const titulo = parada.nombre_destinatario || parada.cliente_origen;
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={`Parada ${parada.secuencia}: ${titulo}`}
      style={({ pressed }) => [estilos.fila, pressed && { opacity: 0.85 }]}
    >
      <View style={estilos.numero}>
        <Text style={estilos.numeroTexto}>{parada.secuencia || "•"}</Text>
      </View>
      <View style={estilos.centro}>
        <Text style={estilos.titulo} numberOfLines={1}>{titulo}</Text>
        <Text style={estilos.direccion} numberOfLines={2}>{parada.direccion_destino}</Text>
        <EstadoBadge estado={parada.estado_entrega} />
      </View>
    </Pressable>
  );
}

const estilos = StyleSheet.create({
  fila: {
    flexDirection: "row",
    gap: spacing.md,
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.lg,
  },
  numero: {
    width: 36,
    height: 36,
    borderRadius: radius.pill,
    backgroundColor: colors.brand,
    alignItems: "center",
    justifyContent: "center",
  },
  numeroTexto: { color: colors.white, fontWeight: "800", fontSize: fontSize.body },
  centro: { flex: 1, gap: spacing.xs },
  titulo: { fontSize: fontSize.subtitle, fontWeight: "700", color: colors.ink },
  direccion: { fontSize: fontSize.body, color: colors.muted },
});
