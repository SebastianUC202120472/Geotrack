// Historial de entregas del conductor: las paradas ya marcadas como ENTREGADO
// en la ruta activa, con la foto de evidencia si se subió en esta sesión.
// TODO: para un historial entre rutas con evidencia persistente haría falta un
//       endpoint del backend (no se toca aquí).
import { FlatList, StyleSheet, Text, View } from "react-native";
import { Image } from "expo-image";
import { Ionicons } from "@expo/vector-icons";
import { Screen } from "@/components/Screen";
import { Card } from "@/components/Card";
import { ItemLista } from "@/components/Animations";
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
        renderItem={({ item, index }) => {
          const evidencia = obtenerEvidencia(item.pedido_id);
          return (
            <ItemLista index={index}>
              <Card>
                <View style={estilos.encabezado}>
                  <Text style={[estilos.codigo, { color: colors.ink }]}>{item.codigo ?? `Pedido ${item.pedido_id}`}</Text>
                  <Text style={[estilos.destinatario, { color: colors.text }]} numberOfLines={1}>{item.nombre_destinatario || item.cliente_origen}</Text>
                </View>
                <View style={estilos.lineaCliente}>
                  <Ionicons name="cube-outline" size={14} color={colors.muted} />
                  <Text style={[estilos.cliente, { color: colors.muted }]} numberOfLines={1}>{item.cliente_origen}</Text>
                </View>
                <Text style={[estilos.direccion, { color: colors.muted }]}>{item.direccion_destino}</Text>
                {evidencia ? (
                  <Image source={{ uri: evidencia }} style={estilos.evidencia} contentFit="cover" />
                ) : (
                  <Text style={[estilos.sinEvidencia, { color: colors.success }]}>
                    Entregado (evidencia no disponible en esta sesión)
                  </Text>
                )}
              </Card>
            </ItemLista>
          );
        }}
      />
    </Screen>
  );
}

const estilos = StyleSheet.create({
  lista: { padding: spacing.lg },
  encabezado: { gap: 2 },
  codigo: { fontSize: fontSize.subtitle, fontWeight: "800" },
  destinatario: { fontSize: fontSize.body, fontWeight: "600" },
  lineaCliente: { flexDirection: "row", alignItems: "center", gap: spacing.xs, marginTop: spacing.xs },
  cliente: { fontSize: fontSize.caption, flex: 1 },
  direccion: { fontSize: fontSize.body, marginTop: 2 },
  evidencia: { width: "100%", height: 180, borderRadius: radius.md, marginTop: spacing.md },
  sinEvidencia: { marginTop: spacing.sm, fontSize: fontSize.caption, fontWeight: "600" },
});
