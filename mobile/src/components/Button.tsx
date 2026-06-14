// Botón grande y accesible (alto >= 56). Primario con degradado de marca y leve
// escala al presionar. Variantes: primary | secondary | danger.
import { useRef } from "react";
import { ActivityIndicator, Animated, Pressable, StyleSheet, Text, View } from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import { useTheme, spacing, fontSize, radius, touch } from "@/theme";

type Variante = "primary" | "secondary" | "danger";

interface Props {
  titulo: string;
  onPress: () => void;
  variante?: Variante;
  cargando?: boolean;
  deshabilitado?: boolean;
}

export function Button({ titulo, onPress, variante = "primary", cargando, deshabilitado }: Props) {
  const { colors } = useTheme();
  const inactivo = cargando || deshabilitado;
  const escala = useRef(new Animated.Value(1)).current;
  const animar = (v: number) => Animated.spring(escala, { toValue: v, useNativeDriver: true, speed: 40, bounciness: 0 }).start();

  const colorTexto = variante === "secondary" ? colors.brand : colors.white;

  const Contenido = (
    <View style={estilos.contenido}>
      {cargando && <ActivityIndicator color={colorTexto} />}
      <Text style={[estilos.texto, { color: colorTexto }]}>{titulo}</Text>
    </View>
  );

  return (
    <Animated.View style={{ transform: [{ scale: escala }], opacity: inactivo ? 0.6 : 1 }}>
      <Pressable
        onPress={onPress}
        disabled={inactivo}
        onPressIn={() => animar(0.97)}
        onPressOut={() => animar(1)}
        accessibilityRole="button"
        accessibilityLabel={titulo}
        style={[
          estilos.base,
          variante === "secondary" && { backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border },
          variante === "danger" && { backgroundColor: colors.danger },
        ]}
      >
        {variante === "primary" ? (
          <LinearGradient colors={[colors.brand, colors.brandPressed]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={estilos.gradiente}>
            {Contenido}
          </LinearGradient>
        ) : (
          Contenido
        )}
      </Pressable>
    </Animated.View>
  );
}

const estilos = StyleSheet.create({
  base: { minHeight: touch.primaryButton, borderRadius: radius.md, justifyContent: "center", overflow: "hidden" },
  gradiente: { minHeight: touch.primaryButton, justifyContent: "center", paddingHorizontal: spacing.lg },
  contenido: { flexDirection: "row", gap: spacing.sm, justifyContent: "center", alignItems: "center", paddingHorizontal: spacing.lg },
  texto: { fontSize: fontSize.subtitle, fontWeight: "700" },
});
