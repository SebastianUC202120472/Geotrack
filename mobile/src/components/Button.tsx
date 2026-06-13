// Botón grande y accesible (alto >= 48). Variantes de color y estado de carga.
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme, spacing, fontSize, radius, touch } from "@/theme";

type Variante = "primary" | "secondary" | "danger";

interface Props {
  titulo: string; // texto del botón
  onPress: () => void; // acción al presionar
  variante?: Variante; // estilo de color (por defecto "primary")
  cargando?: boolean; // muestra spinner y deshabilita
  deshabilitado?: boolean; // deshabilita el botón
}

// Botón táctil grande. Recibe: { titulo, onPress, variante?, cargando?, deshabilitado? }.
export function Button({ titulo, onPress, variante = "primary", cargando, deshabilitado }: Props) {
  const { colors } = useTheme();
  const inactivo = cargando || deshabilitado;
  const fondo =
    variante === "secondary" ? colors.surface : variante === "danger" ? colors.danger : colors.brand;
  const colorTexto = variante === "secondary" ? colors.brand : colors.white;

  return (
    <Pressable
      onPress={onPress}
      disabled={inactivo}
      accessibilityRole="button"
      accessibilityLabel={titulo}
      style={({ pressed }) => [
        estilos.base,
        { backgroundColor: fondo, opacity: inactivo ? 0.6 : pressed ? 0.85 : 1 },
        variante === "secondary" && { borderWidth: 1, borderColor: colors.border },
      ]}
    >
      <View style={estilos.contenido}>
        {cargando && <ActivityIndicator color={colorTexto} />}
        <Text style={[estilos.texto, { color: colorTexto }]}>{titulo}</Text>
      </View>
    </Pressable>
  );
}

const estilos = StyleSheet.create({
  base: {
    minHeight: touch.primaryButton,
    borderRadius: radius.md,
    justifyContent: "center",
    paddingHorizontal: spacing.lg,
  },
  contenido: { flexDirection: "row", gap: spacing.sm, justifyContent: "center", alignItems: "center" },
  texto: { fontSize: fontSize.subtitle, fontWeight: "700" },
});
