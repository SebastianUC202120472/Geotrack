// Banner de estado offline / cola pendiente (CUS-27). Se muestra cuando no hay
// conexión o hay acciones por sincronizar; permite sincronizar manualmente.
import { View, Pressable, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Texto } from "@/components/Texto";
import { useConexion } from "@/hooks/useConexion";
import { useCola, useSincronizar } from "@/features/sync/hooks";
import { useTheme, radius, spacing } from "@/theme";

export function BannerSync() {
  const { colors } = useTheme();
  const { online } = useConexion();
  const { pendientes } = useCola();
  const sincronizar = useSincronizar();

  if (online && pendientes === 0) return null;

  // Offline -> rojo; online con cola -> azul (marca). Evita depender de tonos 'warning'.
  const fondo = online ? colors.brandSoft : colors.dangerSoft;
  const tinta = online ? colors.brand : colors.danger;
  const texto = !online
    ? `Sin conexión${pendientes ? ` · ${pendientes} pendiente(s)` : ""}`
    : `${pendientes} pendiente(s) de sincronizar`;

  return (
    <View style={[estilos.caja, { backgroundColor: fondo, borderRadius: radius.md }]}>
      <Ionicons name={online ? "cloud-upload-outline" : "cloud-offline-outline"} size={18} color={tinta} />
      <Texto variante="bodyMedium" color={tinta} style={{ flex: 1 }}>{texto}</Texto>
      {online && pendientes > 0 && (
        <Pressable onPress={sincronizar} accessibilityRole="button" accessibilityLabel="Sincronizar ahora">
          <Texto variante="bodyMedium" color={tinta} style={{ textDecorationLine: "underline" }}>Sincronizar</Texto>
        </Pressable>
      )}
    </View>
  );
}

const estilos = StyleSheet.create({
  caja: { flexDirection: "row", alignItems: "center", gap: spacing.sm, paddingVertical: spacing.sm, paddingHorizontal: spacing.md },
});
