// Campo de texto con etiqueta, accesible y de toque amplio.
import { StyleSheet, Text, TextInput, View, type TextInputProps } from "react-native";
import { colors, fontSize, radius, spacing, touch } from "@/theme";

interface Props extends TextInputProps {
  // Etiqueta visible encima del campo.
  label: string;
}

// Recibe: { label, ...props de TextInput }.
export function Field({ label, style, ...props }: Props) {
  return (
    <View style={estilos.grupo}>
      <Text style={estilos.label}>{label}</Text>
      <TextInput
        style={[estilos.input, style]}
        placeholderTextColor={colors.muted}
        accessibilityLabel={label}
        {...props}
      />
    </View>
  );
}

const estilos = StyleSheet.create({
  grupo: { gap: spacing.xs },
  label: { fontSize: fontSize.body, fontWeight: "600", color: colors.text },
  input: {
    minHeight: touch.minTarget,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    backgroundColor: colors.surface,
    paddingHorizontal: spacing.lg,
    fontSize: fontSize.body,
    color: colors.ink,
  },
});
