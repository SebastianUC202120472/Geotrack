// Pantalla principal del conductor: su ruta activa con la secuencia de paradas,
// el mapa del recorrido y los botones para iniciar (desde su ubicación) y
// finalizar la ruta.
import { useMemo } from "react";
import { Alert, FlatList, RefreshControl, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { Screen } from "@/components/Screen";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { MapaRuta } from "@/components/MapaRuta";
import { ParadaItem } from "@/components/ParadaItem";
import { Cargando, ErrorVista, Vacio } from "@/components/Estados";
import { useRutaActiva, useManifiesto, useNavegacion, useIniciarRuta, useFinalizarRuta } from "@/features/ruta/hooks";
import { useUbicacionActual } from "@/hooks/useUbicacionActual";
import { mensajeDeError } from "@/api/client";
import { colors, fontSize, spacing } from "@/theme";

export default function RutaScreen() {
  const router = useRouter();
  const ruta = useRutaActiva();
  const manifiesto = useManifiesto();
  const navegacion = useNavegacion();
  const ubicacion = useUbicacionActual();
  const iniciar = useIniciarRuta();
  const finalizar = useFinalizarRuta();

  const paradas = manifiesto.data?.paradas ?? [];
  const sinRuta = (ruta.error as { response?: { status?: number } } | null)?.response?.status === 404;

  // Refresca las tres consultas a la vez (pull-to-refresh).
  const refrescar = () => {
    ruta.refetch();
    manifiesto.refetch();
    navegacion.refetch();
  };

  // Inicia la ruta: toma la ubicación actual y pide la optimización al backend.
  const iniciarRuta = async () => {
    if (!ruta.data) return;
    const coords = await ubicacion.obtener();
    if (!coords) {
      if (ubicacion.error) Alert.alert("Ubicación", ubicacion.error);
      return;
    }
    iniciar.mutate(
      { rutaId: ruta.data.ruta_id, coords },
      {
        onSuccess: (total) => Alert.alert("Ruta lista", `Se ordenaron ${total} paradas desde tu ubicación.`),
        onError: (e) => Alert.alert("Error", mensajeDeError(e)),
      }
    );
  };

  // Finaliza la ruta del día (con confirmación).
  const finalizarRuta = () => {
    Alert.alert("Finalizar ruta", "¿Seguro que quieres cerrar la ruta de hoy?", [
      { text: "Cancelar", style: "cancel" },
      {
        text: "Finalizar",
        style: "destructive",
        onPress: () =>
          finalizar.mutate(undefined, {
            onSuccess: (r) => Alert.alert("Ruta finalizada", r.mensaje),
            onError: (e) => Alert.alert("Error", mensajeDeError(e)),
          }),
      },
    ]);
  };

  // Cabecera de la lista: resumen, mapa y acciones.
  const Cabecera = useMemo(
    () => (
      <View style={estilos.cabecera}>
        {ruta.data && (
          <Card>
            <Text style={estilos.nombreRuta}>{ruta.data.nombre}</Text>
            <Text style={estilos.codigo}>
              {ruta.data.codigo ?? "—"} · {ruta.data.estado.replace("_", " ").toLowerCase()}
            </Text>
            <View style={estilos.contadores}>
              <Contador valor={ruta.data.pendientes} etiqueta="Pendientes" color={colors.warning} />
              <Contador valor={ruta.data.entregadas} etiqueta="Entregadas" color={colors.success} />
              <Contador valor={ruta.data.fallidas} etiqueta="Fallidas" color={colors.danger} />
            </View>
          </Card>
        )}

        <MapaRuta paradas={navegacion.data?.paradas ?? []} />

        <Button
          titulo="Iniciar ruta desde mi ubicación"
          onPress={iniciarRuta}
          cargando={ubicacion.cargando || iniciar.isPending}
        />
        <Button titulo="Finalizar ruta" variante="secondary" onPress={finalizarRuta} cargando={finalizar.isPending} />

        <Text style={estilos.seccion}>Paradas ({paradas.length})</Text>
      </View>
    ),
    [ruta.data, navegacion.data, paradas.length, ubicacion.cargando, iniciar.isPending, finalizar.isPending]
  );

  if (ruta.isLoading || manifiesto.isLoading) return <Screen><Cargando /></Screen>;

  if (sinRuta) {
    return (
      <Screen>
        <Vacio
          titulo="No tienes una ruta asignada"
          detalle="Cuando el administrador te asigne pedidos, aparecerán aquí."
        />
      </Screen>
    );
  }

  if (ruta.isError) {
    return (
      <Screen>
        <ErrorVista mensaje={mensajeDeError(ruta.error)} onReintentar={refrescar} />
      </Screen>
    );
  }

  return (
    <Screen conPadding={false}>
      <FlatList
        data={paradas}
        keyExtractor={(p) => String(p.pedido_id)}
        ListHeaderComponent={Cabecera}
        renderItem={({ item }) => (
          <ParadaItem parada={item} onPress={() => router.push(`/parada/${item.pedido_id}`)} />
        )}
        contentContainerStyle={estilos.lista}
        ItemSeparatorComponent={() => <View style={{ height: spacing.md }} />}
        refreshControl={<RefreshControl refreshing={manifiesto.isFetching} onRefresh={refrescar} />}
      />
    </Screen>
  );
}

// Contador compacto para el resumen. Recibe: { valor, etiqueta, color }.
function Contador({ valor, etiqueta, color }: { valor: number; etiqueta: string; color: string }) {
  return (
    <View style={estilos.contador}>
      <Text style={[estilos.contadorValor, { color }]}>{valor}</Text>
      <Text style={estilos.contadorEtiqueta}>{etiqueta}</Text>
    </View>
  );
}

const estilos = StyleSheet.create({
  lista: { padding: spacing.lg },
  cabecera: { gap: spacing.md, marginBottom: spacing.md },
  nombreRuta: { fontSize: fontSize.title, fontWeight: "800", color: colors.ink },
  codigo: { fontSize: fontSize.body, color: colors.muted, marginTop: 2, textTransform: "capitalize" },
  contadores: { flexDirection: "row", justifyContent: "space-around", marginTop: spacing.lg },
  contador: { alignItems: "center" },
  contadorValor: { fontSize: fontSize.title, fontWeight: "800" },
  contadorEtiqueta: { fontSize: fontSize.caption, color: colors.muted },
  seccion: { fontSize: fontSize.subtitle, fontWeight: "700", color: colors.ink, marginTop: spacing.sm },
});
