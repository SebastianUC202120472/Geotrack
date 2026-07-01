// Campo de texto con etiqueta, accesible y de toque amplio.
import { StyleSheet, TextInput, View, type TextInputProps } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useTheme, radius, spacing, touch, fuentes } from "@/theme";
import { Texto } from "@/components/Texto";

interface Props extends TextInputProps {
  label: string; // etiqueta visible encima del campo
  icono?: keyof typeof Ionicons.glyphMap; // icono opcional a la izquierda del input
}

export function Field({ label, icono, style, ...props }: Props) {
  const { colors } = useTheme();
  return (
    <View style={estilos.grupo}>
      <Texto variante="label" color={colors.text}>{label}</Texto>
      <View style={estilos.inputWrapper}>
        {icono && (
          <View style={estilos.iconoContenedor} pointerEvents="none">
            <Ionicons name={icono} size={18} color={colors.muted} />
          </View>
        )}
        <TextInput
          style={[
            estilos.input,
            { borderColor: colors.border, backgroundColor: colors.surface, color: colors.ink },
            icono ? estilos.inputConIcono : null,
            style,
          ]}
          placeholderTextColor={colors.muted}
          accessibilityLabel={label}
          {...props}
        />
      </View>
    </View>
  );
}

const estilos = StyleSheet.create({
  grupo: { gap: spacing.xs },
  inputWrapper: { position: "relative", justifyContent: "center" },
  iconoContenedor: { position: "absolute", left: spacing.md, zIndex: 1 },
  input: {
    minHeight: touch.minTarget,
    borderWidth: 1,
    borderRadius: radius.md,
    paddingHorizontal: spacing.lg,
    fontFamily: fuentes.regular,
  },
  inputConIcono: {
    paddingLeft: 40,
  },
});
