// Cabecera con degradado de marca, redondeada abajo. Recibe ViewProps y children.
import { StyleSheet, View, type ViewProps } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { useTheme, spacing, radius } from "@/theme";

export function GradientHeader({ style, children, ...props }: ViewProps) {
  const { colors } = useTheme();
  return (
    <LinearGradient colors={[colors.brand, colors.brandPressed]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={[estilos.cab, style]}>
      <View {...props}>{children}</View>
    </LinearGradient>
  );
}

const estilos = StyleSheet.create({
  cab: { paddingTop: spacing.xl, paddingBottom: spacing.xl, paddingHorizontal: spacing.lg, borderBottomLeftRadius: radius.xl, borderBottomRightRadius: radius.xl },
});
