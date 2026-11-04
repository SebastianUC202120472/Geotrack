// Selector de motivo en forma de chips, con "Otro" que pide escribir el detalle.
import { Pressable, StyleSheet, TextInput, View } from "react-native";
import { Texto } from "@/components/Texto";
import { useTheme, fontSize, radius, spacing } from "@/theme";

export const OTRO_MOTIVO = "Otro";

interface Props {
  motivos: string[];
  valor: string;
  onCambiar: (motivo: string) => void;
  detalle?: string;
  onDetalle?: (texto: string) => void;
  placeholderDetalle?: string;
}

// Chips de motivo + caja de texto para el detalle cuando se elige "Otro". Recibe los motivos,
// el valor elegido, onCambiar y (opcional) el detalle con su manejador.
export function SelectorMotivo({ motivos, valor, onCambiar, detalle = "", onDetalle, placeholderDetalle = "Cuéntanos qué pasó" }: Props) {
  const { colors } = useTheme();
  return (
    <View>
      <View style={estilos.chips}>
        {motivos.map((m) => {
          const activo = valor === m;
          return (
            <Pressable
              key={m}
              onPress={() => onCambiar(m)}
              accessibilityRole="button"
              accessibilityState={{ selected: activo }}
              accessibilityLabel={m}
              style={[estilos.chip, { borderColor: activo ? colors.brand : colors.border, backgroundColor: activo ? colors.brandSoft : colors.surface }]}
            >
              <Texto variante="body" color={activo ? colors.brand : colors.text}>{m}</Texto>
            </Pressable>
          );
        })}
      </View>
      {onDetalle && valor === OTRO_MOTIVO && (
        <TextInput
          value={detalle}
          onChangeText={onDetalle}
          placeholder={placeholderDetalle}
          placeholderTextColor={colors.muted}
          multiline
          maxLength={180}
          style={[estilos.detalle, { borderColor: colors.border, color: colors.ink, backgroundColor: colors.surface }]}
        />
      )}
    </View>
  );
}

const estilos = StyleSheet.create({
  chips: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  chip: { paddingVertical: spacing.sm, paddingHorizontal: spacing.md, borderRadius: radius.md, borderWidth: 1 },
  detalle: { borderWidth: 1, borderRadius: radius.md, padding: spacing.md, marginTop: spacing.sm, minHeight: 72, fontSize: fontSize.body, textAlignVertical: "top" },
});
