// Tarjeta con superficie, borde y sombra suave según el tema. Si recibe onPress,
// es táctil y hace una leve escala al presionar.
import { useRef } from "react";
import { Animated, Pressable, StyleSheet, View, type ViewProps } from "react-native";
import { useTheme, radius, spacing } from "@/theme";

interface Props extends ViewProps {
  onPress?: () => void;
}

export function Card({ style, onPress, children, ...props }: Props) {
  const { colors } = useTheme();
  const escala = useRef(new Animated.Value(1)).current;
  const animar = (v: number) => Animated.spring(escala, { toValue: v, useNativeDriver: true, speed: 40, bounciness: 0 }).start();

  const base = [estilos.card, { backgroundColor: colors.surface, borderColor: colors.border }, style];

  if (!onPress) return <View style={base} {...props}>{children}</View>;

  return (
    <Animated.View style={{ transform: [{ scale: escala }] }}>
      <Pressable onPress={onPress} onPressIn={() => animar(0.98)} onPressOut={() => animar(1)} style={base} {...props}>
        {children}
      </Pressable>
    </Animated.View>
  );
}

const estilos = StyleSheet.create({
  card: { borderRadius: radius.lg, borderWidth: 1, padding: spacing.lg, shadowColor: "#0F172A", shadowOpacity: 0.06, shadowRadius: 12, shadowOffset: { width: 0, height: 4 }, elevation: 2 },
});
