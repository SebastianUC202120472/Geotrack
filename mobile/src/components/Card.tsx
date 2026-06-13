// Tarjeta blanca con borde suave. Contenedor visual estándar.
import { StyleSheet, View, type ViewProps } from "react-native";
import { colors, radius, spacing } from "@/theme";

// Recibe: las props normales de View (incluye children y style).
export function Card({ style, ...props }: ViewProps) {
  return <View style={[estilos.card, style]} {...props} />;
}

const estilos = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.lg,
  },
});
