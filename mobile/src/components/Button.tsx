// Botón grande y accesible (alto >= 48). Variantes de color y estado de carga.
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";
import { colors, fontSize, radius, spacing, touch } from "@/theme";

type Variante = "primary" | "secondary" | "danger";

interface Props {
  // Texto del botón.
  titulo: string;
  // Acción al presionar.
  onPress: () => void;
  // Estilo de color (por defecto "primary").
  variante?: Variante;
  // Muestra spinner y deshabilita mientras true.
  cargando?: boolean;
  // Deshabilita el botón.
  deshabilitado?: boolean;
}

// Botón táctil grande. Recibe: { titulo, onPress, variante?, cargando?, deshabilitado? }.
export function Button({ titulo, onPress, variante = "primary", cargando, deshabilitado }: Props) {
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
        variante === "secondary" && estilos.bordeSecundario,
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
  bordeSecundario: { borderWidth: 1, borderColor: colors.border },
  contenido: { flexDirection: "row", gap: spacing.sm, justifyContent: "center", alignItems: "center" },
  texto: { fontSize: fontSize.subtitle, fontWeight: "700" },
});
