import { Pressable, StyleSheet, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { Ionicons } from "@expo/vector-icons";
import { useTheme, radius, spacing } from "@/theme";
import { Texto } from "@/components/Texto";
import { EstadoBadge } from "./EstadoBadge";
import type { ParadaManifiesto } from "@/types/api";

interface Props {
  parada: ParadaManifiesto;
  onPress: () => void;
}

// Fila táctil de una parada. Recibe parada y onPress.
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
      <LinearGradient
        colors={[colors.brand, colors.brandPressed]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={estilos.numero}
      >
        <Texto variante="subtitle" color={colors.white}>{parada.secuencia || "•"}</Texto>
      </LinearGradient>
      <View style={estilos.centro}>
        <Texto variante="subtitle" color={colors.ink} style={estilos.titulo} numberOfLines={1}>{titulo}</Texto>
        <View style={estilos.lineaCliente}>
          <Ionicons name="cube-outline" size={14} color={colors.muted} />
          <Texto variante="caption" color={colors.muted} style={estilos.cliente} numberOfLines={1}>{parada.cliente_origen}</Texto>
        </View>
        <Texto variante="body" color={colors.muted} numberOfLines={2}>{parada.direccion_destino}</Texto>
        <EstadoBadge estado={parada.estado_entrega} />
      </View>
    </Pressable>
  );
}

const estilos = StyleSheet.create({
  fila: { flexDirection: "row", gap: spacing.md, borderRadius: radius.lg, borderWidth: 1, padding: spacing.lg },
  numero: { width: 36, height: 36, borderRadius: radius.pill, alignItems: "center", justifyContent: "center" },
  centro: { flex: 1, gap: spacing.xs },
  titulo: {},
  lineaCliente: { flexDirection: "row", alignItems: "center", gap: spacing.xs },
  cliente: { flex: 1 },
});
