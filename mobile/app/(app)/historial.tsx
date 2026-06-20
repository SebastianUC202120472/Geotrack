// Historial de entregas del conductor: las paradas ya marcadas como ENTREGADO
// en la ruta activa, con la foto de evidencia si se subió en esta sesión.
// TODO: para un historial entre rutas con evidencia persistente haría falta un
//       endpoint del backend (no se toca aquí).
import { FlatList, StyleSheet, View } from "react-native";
import { Image } from "expo-image";
import { Ionicons } from "@expo/vector-icons";
import { Screen } from "@/components/Screen";
import { Card } from "@/components/Card";
import { Cabecera } from "@/components/Cabecera";
import { CamionCargando } from "@/components/CamionCargando";
import { ItemLista } from "@/components/Animations";
import { Vacio } from "@/components/Estados";
import { Texto } from "@/components/Texto";
import { useManifiesto } from "@/features/ruta/hooks";
import { obtenerEvidencia } from "@/store/evidenciaCache";
import type { ParadaManifiesto } from "@/types/api";
import { useTheme, radius, spacing } from "@/theme";

export default function HistorialScreen() {
  const { colors } = useTheme();
  const manifiesto = useManifiesto();
  const entregadas = (manifiesto.data?.paradas ?? []).filter((p: ParadaManifiesto) => p.estado_entrega === "ENTREGADO");

  if (manifiesto.isLoading) {
    return (
      <Screen conPadding={false}>
        <Cabecera titulo="Historial" />
        <CamionCargando texto="Cargando tu historial…" />
      </Screen>
    );
  }

  if (entregadas.length === 0) {
    return (
      <Screen conPadding={false}>
        <Cabecera titulo="Historial" />
        <Vacio titulo="Aún no hay entregas" detalle="Tus pedidos entregados aparecerán aquí." />
      </Screen>
    );
  }

  return (
    <Screen conPadding={false}>
      <Cabecera titulo="Historial" />
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
                  <Texto variante="subtitle" color={colors.ink}>{item.codigo ?? `Pedido ${item.pedido_id}`}</Texto>
                  <Texto variante="bodyMedium" color={colors.text} numberOfLines={1}>{item.nombre_destinatario || item.cliente_origen}</Texto>
                </View>
                <View style={estilos.lineaCliente}>
                  <Ionicons name="cube-outline" size={14} color={colors.muted} />
                  <Texto variante="caption" color={colors.muted} numberOfLines={1} style={estilos.cliente}>{item.cliente_origen}</Texto>
                </View>
                <Texto variante="body" color={colors.muted} style={estilos.direccion}>{item.direccion_destino}</Texto>
                {evidencia ? (
                  <Image source={{ uri: evidencia }} style={estilos.evidencia} contentFit="cover" />
                ) : (
                  <Texto variante="caption" color={colors.success} style={estilos.sinEvidencia}>
                    Entregado (evidencia no disponible en esta sesión)
                  </Texto>
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
  lineaCliente: { flexDirection: "row", alignItems: "center", gap: spacing.xs, marginTop: spacing.xs },
  cliente: { flex: 1 },
  direccion: { marginTop: 2 },
  evidencia: { width: "100%", height: 180, borderRadius: radius.md, marginTop: spacing.md },
  sinEvidencia: { marginTop: spacing.sm },
});
