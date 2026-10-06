// Campo de texto con etiqueta, accesible y de toque amplio.
import { useState } from "react";
import { Pressable, StyleSheet, TextInput, View, type TextInputProps } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useTheme, radius, spacing, touch, fuentes } from "@/theme";
import { Texto } from "@/components/Texto";

interface Props extends TextInputProps {
  label: string; // etiqueta visible encima del campo
  icono?: keyof typeof Ionicons.glyphMap; // icono opcional a la izquierda del input
  permitirMostrarOcultar?: boolean; // si es true o se pasa secureTextEntry, añade botón de ojito
}

export function Field({ label, icono, permitirMostrarOcultar, secureTextEntry, style, ...props }: Props) {
  const { colors } = useTheme();
  const [oculto, setOculto] = useState(Boolean(secureTextEntry));

  const mostrarBotonOjo = permitirMostrarOcultar ?? Boolean(secureTextEntry);

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
            mostrarBotonOjo ? estilos.inputConBotonDerecho : null,
            style,
          ]}
          placeholderTextColor={colors.muted}
          accessibilityLabel={label}
          secureTextEntry={mostrarBotonOjo ? oculto : secureTextEntry}
          {...props}
        />
        {mostrarBotonOjo && (
          <Pressable
            onPress={() => setOculto(!oculto)}
            style={estilos.botonDerechoContenedor}
            accessibilityRole="button"
            accessibilityLabel={oculto ? "Mostrar contraseña" : "Ocultar contraseña"}
            hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
          >
            <Ionicons name={oculto ? "eye-outline" : "eye-off-outline"} size={20} color={colors.muted} />
          </Pressable>
        )}
      </View>
    </View>
  );
}

const estilos = StyleSheet.create({
  grupo: { gap: spacing.xs },
  inputWrapper: { position: "relative", justifyContent: "center" },
  iconoContenedor: { position: "absolute", left: spacing.md, zIndex: 1 },
  botonDerechoContenedor: { position: "absolute", right: spacing.md, zIndex: 1, padding: spacing.xs },
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
  inputConBotonDerecho: {
    paddingRight: 44,
  },
});
