// Apartado de notificaciones del conductor (in-app). Por ahora deriva un aviso de
// la ruta activa asignada; el seguimiento de "no leídas" se añade más adelante.
// Pantalla navegable desde la campana de la cabecera.
import { ScrollView, StyleSheet, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Screen } from "@/components/Screen";
import { Card } from "@/components/Card";
import { Cabecera } from "@/components/Cabecera";
import { Cargando, Vacio } from "@/components/Estados";
import { Aparecer } from "@/components/Animations";
import { Texto } from "@/components/Texto";
import { useRutaActiva } from "@/features/ruta/hooks";
import { useTheme, spacing, radius } from "@/theme";

export default function NotificacionesScreen() {
  const { colors } = useTheme();
  const ruta = useRutaActiva();

  const sinRuta = (ruta.error as { response?: { status?: number } } | null)?.response?.status === 404;

  if (ruta.isLoading) return <Screen conPadding={false}><Cabecera titulo="Notificaciones" atras /><Cargando /></Screen>;

  if (sinRuta || !ruta.data) {
    return (
      <Screen conPadding={false}>
        <Cabecera titulo="Notificaciones" atras />
        <Vacio titulo="Sin notificaciones" detalle="Te avisaremos aquí cuando te asignen pedidos." />
      </Screen>
    );
  }

  const r = ruta.data;

  return (
    <Screen conPadding={false}>
      <Cabecera titulo="Notificaciones" atras />
      <ScrollView contentContainerStyle={estilos.cuerpo}>
        <Aparecer>
          <Card>
            <View style={estilos.fila}>
              <View style={[estilos.icono, { backgroundColor: colors.brandSoft }]}>
                <Ionicons name="cube-outline" size={20} color={colors.brand} />
              </View>
              <View style={{ flex: 1 }}>
                <Texto variante="bodyMedium" color={colors.ink}>Pedidos asignados</Texto>
                <Texto variante="caption" color={colors.muted}>
                  {r.nombre} · {r.total_paradas} {r.total_paradas === 1 ? "parada" : "paradas"} ({r.pendientes} pendientes)
                </Texto>
              </View>
            </View>
          </Card>
        </Aparecer>
      </ScrollView>
    </Screen>
  );
}

const estilos = StyleSheet.create({
  cuerpo: { padding: spacing.lg, gap: spacing.md },
  fila: { flexDirection: "row", alignItems: "center", gap: spacing.md },
  icono: { width: 40, height: 40, borderRadius: radius.md, alignItems: "center", justifyContent: "center" },
});
