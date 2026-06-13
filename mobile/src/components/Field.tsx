// Campo de texto con etiqueta, accesible y de toque amplio.
import { StyleSheet, Text, TextInput, View, type TextInputProps } from "react-native";
import { useTheme, fontSize, radius, spacing, touch } from "@/theme";

interface Props extends TextInputProps {
  label: string; // etiqueta visible encima del campo
}

// Recibe: { label, ...props de TextInput }.
export function Field({ label, style, ...props }: Props) {
  const { colors } = useTheme();
  return (
    <View style={estilos.grupo}>
      <Text style={[estilos.label, { color: colors.text }]}>{label}</Text>
      <TextInput
        style={[
          estilos.input,
          { borderColor: colors.border, backgroundColor: colors.surface, color: colors.ink },
          style,
        ]}
        placeholderTextColor={colors.muted}
        accessibilityLabel={label}
        {...props}
      />
    </View>
  );
}

const estilos = StyleSheet.create({
  grupo: { gap: spacing.xs },
  label: { fontSize: fontSize.body, fontWeight: "600" },
  input: {
    minHeight: touch.minTarget,
    borderWidth: 1,
    borderRadius: radius.md,
    paddingHorizontal: spacing.lg,
    fontSize: fontSize.body,
  },
});
