// Tarjeta con superficie y borde según el tema activo.
import { StyleSheet, View, type ViewProps } from "react-native";
import { useTheme, radius, spacing } from "@/theme";

// Recibe: las props normales de View (incluye children y style).
export function Card({ style, ...props }: ViewProps) {
  const { colors } = useTheme();
  return (
    <View
      style={[
        estilos.card,
        { backgroundColor: colors.surface, borderColor: colors.border },
        style,
      ]}
      {...props}
    />
  );
}

const estilos = StyleSheet.create({
  card: { borderRadius: radius.lg, borderWidth: 1, padding: spacing.lg },
});
