// Etiqueta de color según el estado de entrega de una parada.
import { StyleSheet, View } from "react-native";
import { useTheme, radius, spacing } from "@/theme";
import { Texto } from "@/components/Texto";
import type { EstadoEntrega } from "@/types/api";

// Badge de estado. Recibe: estado (EstadoEntrega).
export function EstadoBadge({ estado }: { estado: EstadoEntrega }) {
  const { colors } = useTheme();
  const mapa: Record<EstadoEntrega, { fondo: string; texto: string; etiqueta: string }> = {
    PENDIENTE: { fondo: colors.warningSoft, texto: colors.warning, etiqueta: "Pendiente" },
    ENTREGADO: { fondo: colors.successSoft, texto: colors.success, etiqueta: "Entregado" },
    FALLIDO: { fondo: colors.dangerSoft, texto: colors.danger, etiqueta: "Fallido" },
  };
  const cfg = mapa[estado] ?? mapa.PENDIENTE;
  return (
    <View style={[estilos.badge, { backgroundColor: cfg.fondo }]}>
      <Texto variante="caption" color={cfg.texto}>{cfg.etiqueta}</Texto>
    </View>
  );
}

const estilos = StyleSheet.create({
  badge: {
    alignSelf: "flex-start",
    borderRadius: radius.pill,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.xs,
  },
});
