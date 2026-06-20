// Apartado "Pedidos": TODOS los pedidos asignados al conductor, en orden de
// enrutamiento (secuencia), con un resumen cuantitativo arriba. Aquí cada pedido
// refleja su estado; la entrega se realiza desde "Ruta" / el detalle de la parada.
import { useCallback } from "react";
import { FlatList, RefreshControl, StyleSheet, View } from "react-native";
import { useRouter, useFocusEffect } from "expo-router";
import { useQueryClient } from "@tanstack/react-query";
import { Screen } from "@/components/Screen";
import { Card } from "@/components/Card";
import { Cabecera } from "@/components/Cabecera";
import { ParadaItem } from "@/components/ParadaItem";
import { ResumenPedidos } from "@/components/ResumenPedidos";
import { CamionCargando } from "@/components/CamionCargando";
import { Vacio } from "@/components/Estados";
import { ItemLista } from "@/components/Animations";
import { Texto } from "@/components/Texto";
import { useRutaActiva, useManifiesto, claves } from "@/features/ruta/hooks";
import { useTheme, spacing } from "@/theme";
import type { ParadaManifiesto } from "@/types/api";

export default function PedidosScreen() {
  const router = useRouter();
  const { colors } = useTheme();
  const ruta = useRutaActiva();
  const manifiesto = useManifiesto();
  const qc = useQueryClient();

  // Al enfocar la pestaña, refresca los datos.
  useFocusEffect(
    useCallback(() => {
      qc.invalidateQueries({ queryKey: claves.rutaActiva });
      qc.invalidateQueries({ queryKey: claves.manifiesto });
    }, [qc])
  );

  const sinRuta = (ruta.error as { response?: { status?: number } } | null)?.response?.status === 404;
  // Todas las paradas, ordenadas por secuencia de enrutamiento.
  const paradas = [...(manifiesto.data?.paradas ?? [])].sort((a, b) => a.secuencia - b.secuencia);

  const refrescar = () => {
    ruta.refetch();
    manifiesto.refetch();
  };

  if (ruta.isLoading || manifiesto.isLoading) {
    return (
      <Screen conPadding={false}>
        <Cabecera titulo="Pedidos" />
        <CamionCargando texto="Cargando tus pedidos…" />
      </Screen>
    );
  }

  if (sinRuta || paradas.length === 0) {
    return (
      <Screen conPadding={false}>
        <Cabecera titulo="Pedidos" />
        <Vacio titulo="No tienes pedidos asignados" detalle="Cuando el administrador te asigne pedidos, aparecerán aquí en orden." />
      </Screen>
    );
  }

  // Cabecera de la lista: el resumen cuantitativo de los pedidos.
  const Encabezado = (
    <View style={estilos.encabezado}>
      {ruta.data && <ResumenPedidos ruta={ruta.data} />}
      <Texto variante="subtitle" color={colors.ink} style={{ marginTop: spacing.lg }}>
        Todos los pedidos ({paradas.length})
      </Texto>
    </View>
  );

  return (
    <Screen conPadding={false}>
      <Cabecera titulo="Pedidos" />
      <FlatList
        data={paradas}
        keyExtractor={(p) => String(p.pedido_id)}
        ListHeaderComponent={Encabezado}
        renderItem={({ item, index }: { item: ParadaManifiesto; index: number }) => (
          <ItemLista index={index}>
            <ParadaItem parada={item} onPress={() => router.push(`/parada/${item.pedido_id}`)} />
          </ItemLista>
        )}
        contentContainerStyle={estilos.lista}
        ItemSeparatorComponent={() => <View style={{ height: spacing.md }} />}
        refreshControl={<RefreshControl refreshing={manifiesto.isFetching} onRefresh={refrescar} />}
      />
    </Screen>
  );
}

const estilos = StyleSheet.create({
  encabezado: { marginBottom: spacing.md },
  lista: { padding: spacing.lg },
});
