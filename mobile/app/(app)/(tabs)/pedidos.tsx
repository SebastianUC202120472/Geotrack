// Pantalla de pedidos asignados con buscador, filtro por distrito y evidencia de entrega.
import { useCallback, useMemo, useState } from "react";
import { FlatList, RefreshControl, ScrollView, StyleSheet, TextInput, Pressable, View } from "react-native";
import { Image } from "expo-image";
import { Ionicons } from "@expo/vector-icons";
import { useRouter, useFocusEffect } from "expo-router";
import { useQueryClient } from "@tanstack/react-query";
import { Screen } from "@/components/Screen";
import { Cabecera } from "@/components/Cabecera";
import { DeslizarPestanas } from "@/components/DeslizarPestanas";
import { ParadaItem } from "@/components/ParadaItem";
import { ResumenPedidos } from "@/components/ResumenPedidos";
import { Cargando, Vacio } from "@/components/Estados";
import { ItemLista } from "@/components/Animations";
import { Texto } from "@/components/Texto";
import { useRutaActiva, useManifiesto, claves } from "@/features/ruta/hooks";
import { obtenerEvidencia } from "@/store/evidenciaCache";
import { urlMedia } from "@/api/config";
import { useTheme, spacing, radius, fuentes } from "@/theme";
import type { ParadaManifiesto } from "@/types/api";

export default function PedidosScreen() {
  const router = useRouter();
  const { colors } = useTheme();
  const ruta = useRutaActiva();
  const manifiesto = useManifiesto();
  const qc = useQueryClient();

  const [busqueda, setBusqueda] = useState("");
  const [distrito, setDistrito] = useState<string | null>(null);
  const [refrescando, setRefrescando] = useState(false);

  useFocusEffect(
    useCallback(() => {
      qc.invalidateQueries({ queryKey: claves.rutaActiva });
      qc.invalidateQueries({ queryKey: claves.manifiesto });
    }, [qc])
  );

  const sinRuta = (ruta.error as { response?: { status?: number } } | null)?.response?.status === 404;

  // Todas las paradas en orden de enrutamiento.
  const todas = useMemo(
    () => [...(manifiesto.data?.paradas ?? [])].sort((a, b) => a.secuencia - b.secuencia),
    [manifiesto.data]
  );
  // Distritos únicos para el filtro.
  const distritos = useMemo(
    () => Array.from(new Set(todas.map((p) => p.distrito).filter(Boolean))) as string[],
    [todas]
  );
  // Lista filtrada por distrito y búsqueda.
  const filtradas = useMemo(() => {
    const q = busqueda.trim().toLowerCase();
    return todas.filter((p) => {
      if (distrito && p.distrito !== distrito) return false;
      if (!q) return true;
      return [p.codigo, p.nombre_destinatario, p.cliente_origen, p.direccion_destino, p.distrito]
        .some((v) => (v ?? "").toLowerCase().includes(q));
    });
  }, [todas, busqueda, distrito]);

  const refrescar = async () => {
    setRefrescando(true);
    try {
      await Promise.all([ruta.refetch(), manifiesto.refetch()]);
    } finally {
      setRefrescando(false);
    }
  };

  if (ruta.isLoading || manifiesto.isLoading) {
    return (
      <Screen conPadding={false}>
        <Cabecera titulo="Pedidos" />
        <Cargando />
      </Screen>
    );
  }

  if (sinRuta || todas.length === 0) {
    return (
      <Screen conPadding={false}>
        <Cabecera titulo="Pedidos" />
        <Vacio titulo="No tienes pedidos asignados" detalle="Cuando el administrador te asigne pedidos, aparecerán aquí en orden." />
      </Screen>
    );
  }

  const Encabezado = (
    <View style={estilos.encabezado}>
      {ruta.data && <ResumenPedidos ruta={ruta.data} />}

      <View style={[estilos.buscador, { backgroundColor: colors.surface, borderColor: colors.border }]}>
        <Ionicons name="search" size={18} color={colors.muted} />
        <TextInput
          value={busqueda}
          onChangeText={setBusqueda}
          placeholder="Buscar por código, cliente o dirección"
          placeholderTextColor={colors.muted}
          style={[estilos.buscadorInput, { color: colors.ink }]}
          returnKeyType="search"
          autoCapitalize="none"
        />
        {busqueda.length > 0 && (
          <Pressable onPress={() => setBusqueda("")} hitSlop={8} accessibilityLabel="Limpiar búsqueda">
            <Ionicons name="close-circle" size={18} color={colors.muted} />
          </Pressable>
        )}
      </View>

      {distritos.length > 0 && (
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={estilos.chips}>
          <ChipDistrito etiqueta="Todos" activo={distrito === null} onPress={() => setDistrito(null)} c={colors} />
          {distritos.map((d) => (
            <ChipDistrito key={d} etiqueta={d} activo={distrito === d} onPress={() => setDistrito(d)} c={colors} />
          ))}
        </ScrollView>
      )}

      <Texto variante="subtitle" color={colors.ink} style={{ marginTop: spacing.md }}>
        {filtradas.length} {filtradas.length === 1 ? "pedido" : "pedidos"}
      </Texto>
    </View>
  );

  return (
    <Screen conPadding={false}>
      <Cabecera titulo="Pedidos" />
      <DeslizarPestanas>
      <FlatList
        data={filtradas}
        keyExtractor={(p) => String(p.pedido_id)}
        ListHeaderComponent={Encabezado}
        keyboardShouldPersistTaps="handled"
        ListEmptyComponent={<Texto variante="body" color={colors.muted} style={estilos.vacioFiltro}>Sin resultados para tu búsqueda.</Texto>}
        renderItem={({ item, index }: { item: ParadaManifiesto; index: number }) => {
          // Foto POD: del backend si ya se refrescó, si no desde la caché de sesión.
          const evidencia = item.estado_entrega === "ENTREGADO"
            ? (urlMedia(item.url_evidencia) ?? obtenerEvidencia(item.pedido_id))
            : undefined;
          return (
            <ItemLista index={index}>
              <ParadaItem parada={item} onPress={() => router.push(`/parada/${item.pedido_id}`)} />
              {evidencia && (
                <Image source={{ uri: evidencia }} style={[estilos.evidencia, { borderColor: colors.border }]} contentFit="cover" transition={200} />
              )}
            </ItemLista>
          );
        }}
        contentContainerStyle={estilos.lista}
        ItemSeparatorComponent={() => <View style={{ height: spacing.md }} />}
        refreshControl={<RefreshControl refreshing={refrescando} onRefresh={refrescar} />}
      />
      </DeslizarPestanas>
    </Screen>
  );
}

// Chip de filtro por distrito. Recibe: { etiqueta, activo, onPress, c (paleta) }.
function ChipDistrito({ etiqueta, activo, onPress, c }: { etiqueta: string; activo: boolean; onPress: () => void; c: { brand: string; brandSoft: string; surface: string; border: string; text: string } }) {
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={`Filtrar por ${etiqueta}`}
      style={[estilos.chip, { backgroundColor: activo ? c.brandSoft : c.surface, borderColor: activo ? c.brand : c.border }]}
    >
      <Texto variante="label" color={activo ? c.brand : c.text}>{etiqueta}</Texto>
    </Pressable>
  );
}

const estilos = StyleSheet.create({
  encabezado: { marginBottom: spacing.md },
  lista: { padding: spacing.lg },
  buscador: { flexDirection: "row", alignItems: "center", gap: spacing.sm, borderWidth: 1, borderRadius: radius.md, paddingHorizontal: spacing.md, marginTop: spacing.md, minHeight: 48 },
  buscadorInput: { flex: 1, fontFamily: fuentes.regular, fontSize: 16 },
  chips: { gap: spacing.sm, paddingVertical: spacing.md, paddingRight: spacing.lg },
  chip: { paddingHorizontal: spacing.md, paddingVertical: spacing.sm, borderRadius: radius.pill, borderWidth: 1 },
  evidencia: { width: "100%", height: 150, borderRadius: radius.md, borderWidth: 1, marginTop: spacing.sm },
  vacioFiltro: { textAlign: "center", paddingVertical: spacing.xl },
});
