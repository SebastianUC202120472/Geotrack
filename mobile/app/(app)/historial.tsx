// Historial de entregas del conductor: las paradas ya marcadas como ENTREGADO
// en la ruta activa, con la foto de evidencia si se subió en esta sesión.
// TODO: para un historial entre rutas con evidencia persistente haría falta un
//       endpoint del backend (no se toca aquí).
import { FlatList, StyleSheet, Text, View } from "react-native";
import { Image } from "expo-image";
import { Screen } from "@/components/Screen";
import { Card } from "@/components/Card";
import { Cargando, Vacio } from "@/components/Estados";
import { useManifiesto } from "@/features/ruta/hooks";
import { obtenerEvidencia } from "@/store/evidenciaCache";
import type { ParadaManifiesto } from "@/types/api";
import { useTheme, fontSize, radius, spacing } from "@/theme";

export default function HistorialScreen() {
  const { colors } = useTheme();
  const manifiesto = useManifiesto();
  const entregadas = (manifiesto.data?.paradas ?? []).filter((p: ParadaManifiesto) => p.estado_entrega === "ENTREGADO");

  if (manifiesto.isLoading) return <Screen><Cargando /></Screen>;

  if (entregadas.length === 0) {
    return <Screen><Vacio titulo="Aún no hay entregas" detalle="Tus pedidos entregados aparecerán aquí." /></Screen>;
  }

  return (
    <Screen conPadding={false}>
      <FlatList
        data={entregadas}
        keyExtractor={(p) => String(p.pedido_id)}
        contentContainerStyle={estilos.lista}
        ItemSeparatorComponent={() => <View style={{ height: spacing.md }} />}
        renderItem={({ item }) => {
          const evidencia = obtenerEvidencia(item.pedido_id);
          return (
            <Card>
              <Text style={[estilos.codigo, { color: colors.ink }]}>{item.codigo ?? `Pedido ${item.pedido_id}`}</Text>
              <Text style={[estilos.destinatario, { color: colors.text }]}>{item.nombre_destinatario || item.cliente_origen}</Text>
              <Text style={[estilos.direccion, { color: colors.muted }]}>{item.direccion_destino}</Text>
              {evidencia ? (
                <Image source={{ uri: evidencia }} style={estilos.evidencia} contentFit="cover" />
              ) : (
                <Text style={[estilos.sinEvidencia, { color: colors.success }]}>
                  Entregado (evidencia no disponible en esta sesión)
                </Text>
              )}
            </Card>
          );
        }}
      />
    </Screen>
  );
}

const estilos = StyleSheet.create({
  lista: { padding: spacing.lg },
  codigo: { fontSize: fontSize.subtitle, fontWeight: "800" },
  destinatario: { fontSize: fontSize.body, marginTop: 2, fontWeight: "600" },
  direccion: { fontSize: fontSize.body, marginTop: 2 },
  evidencia: { width: "100%", height: 180, borderRadius: radius.md, marginTop: spacing.md },
  sinEvidencia: { marginTop: spacing.sm, fontSize: fontSize.caption, fontWeight: "600" },
});
