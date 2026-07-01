// Muestra totales por estado y avance de la ruta. Recibe: { ruta } (RutaActiva).
import { StyleSheet, View } from "react-native";
import { Card } from "@/components/Card";
import { Contador, BarraProgreso } from "@/components/Animations";
import { Texto } from "@/components/Texto";
import { useTheme, spacing, radius } from "@/theme";
import type { RutaActiva } from "@/types/api";

export function ResumenPedidos({ ruta }: { ruta: RutaActiva }) {
  const { colors } = useTheme();
  const total = ruta.total_paradas;
  const pct = total > 0 ? Math.round((ruta.entregadas / total) * 100) : 0;

  return (
    <Card>
      <View style={estilos.filaTitulo}>
        <Texto variante="subtitle" color={colors.ink}>Resumen</Texto>
        <Texto variante="caption" color={colors.muted}>{pct}% avanzado</Texto>
      </View>

      <View style={estilos.metricas}>
        <Metrica valor={total} etiqueta="Total" color={colors.ink} fondo={colors.canvas} />
        <Metrica valor={ruta.pendientes} etiqueta="Pendientes" color={colors.warning} fondo={colors.warningSoft} />
        <Metrica valor={ruta.entregadas} etiqueta="Entregados" color={colors.success} fondo={colors.successSoft} />
        <Metrica valor={ruta.fallidas} etiqueta="Fallidos" color={colors.danger} fondo={colors.dangerSoft} />
      </View>

      <View style={{ marginTop: spacing.md }}>
        <BarraProgreso valor={ruta.entregadas} total={total} fondo={colors.border} porEstado />
      </View>
    </Card>
  );
}

// Métrica individual (número animado + etiqueta) sobre un fondo de color suave.
function Metrica({ valor, etiqueta, color, fondo }: { valor: number; etiqueta: string; color: string; fondo: string }) {
  return (
    <View style={[estilos.metrica, { backgroundColor: fondo }]}>
      <Contador valor={valor} variante="title" color={color} />
      <Texto variante="caption" color={color} numberOfLines={1}>{etiqueta}</Texto>
    </View>
  );
}

const estilos = StyleSheet.create({
  filaTitulo: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: spacing.md },
  metricas: { flexDirection: "row", gap: spacing.sm },
  metrica: { flex: 1, borderRadius: radius.md, paddingVertical: spacing.md, paddingHorizontal: spacing.xs, alignItems: "center", gap: 2 },
});
