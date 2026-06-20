// Pestaña "Reportes": lista de los reportes de incidencia del conductor. Cada uno
// es tocable y abre su detalle completo (motivo, descripción, estado y respuesta).
import { useCallback } from "react";
import { FlatList, StyleSheet, View } from "react-native";
import { useRouter, useFocusEffect } from "expo-router";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Screen } from "@/components/Screen";
import { Cabecera } from "@/components/Cabecera";
import { DeslizarPestanas } from "@/components/DeslizarPestanas";
import { Card } from "@/components/Card";
import { Cargando, Vacio } from "@/components/Estados";
import { ItemLista } from "@/components/Animations";
import { Texto } from "@/components/Texto";
import { obtenerMisReportes } from "@/api/conductor";
import { useTheme, spacing, radius } from "@/theme";
import type { Reporte } from "@/types/api";

export default function ReportesScreen() {
  const router = useRouter();
  const { colors } = useTheme();
  const qc = useQueryClient();
  const reportes = useQuery({ queryKey: ["mis-reportes"], queryFn: obtenerMisReportes, refetchInterval: 10_000, refetchOnMount: "always" });

  // Al enfocar la pestaña, refresca la lista de reportes.
  useFocusEffect(useCallback(() => { qc.invalidateQueries({ queryKey: ["mis-reportes"] }); }, [qc]));

  if (reportes.isLoading) {
    return (
      <Screen conPadding={false}>
        <Cabecera titulo="Reportes" />
        <Cargando />
      </Screen>
    );
  }

  const lista = reportes.data ?? [];
  if (lista.length === 0) {
    return (
      <Screen conPadding={false}>
        <Cabecera titulo="Reportes" />
        <Vacio titulo="No tienes reportes" detalle="Cuando reportes un problema en una entrega, aparecerá aquí." />
      </Screen>
    );
  }

  return (
    <Screen conPadding={false}>
      <Cabecera titulo="Reportes" />
      <DeslizarPestanas>
        <FlatList
          data={lista}
          keyExtractor={(r) => String(r.id)}
          contentContainerStyle={estilos.lista}
          ItemSeparatorComponent={() => <View style={{ height: spacing.md }} />}
          renderItem={({ item, index }: { item: Reporte; index: number }) => {
            const resuelto = item.estado === "RESUELTO";
            return (
              <ItemLista index={index}>
                <Card onPress={() => router.push(`/reporte/${item.id}`)}>
                  <View style={estilos.fila}>
                    <Texto variante="bodyMedium" color={colors.ink} style={{ flex: 1 }} numberOfLines={1}>
                      {item.pedido_codigo ?? `Pedido ${item.pedido_id}`}
                    </Texto>
                    <View style={[estilos.badge, { backgroundColor: resuelto ? colors.successSoft : colors.warningSoft }]}>
                      <Texto variante="caption" color={resuelto ? colors.success : colors.warning}>
                        {resuelto ? "Respondido" : "En revisión"}
                      </Texto>
                    </View>
                  </View>
                  <Texto variante="body" color={colors.text} numberOfLines={1} style={{ marginTop: 2 }}>{item.motivo}</Texto>
                  <Texto variante="caption" color={colors.muted} style={{ marginTop: spacing.xs }}>Toca para ver el detalle</Texto>
                </Card>
              </ItemLista>
            );
          }}
        />
      </DeslizarPestanas>
    </Screen>
  );
}

const estilos = StyleSheet.create({
  lista: { padding: spacing.lg },
  fila: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  badge: { borderRadius: radius.pill, paddingHorizontal: spacing.md, paddingVertical: spacing.xs },
});
