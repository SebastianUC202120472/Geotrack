// Pantalla principal del conductor: su ruta activa con la secuencia de paradas,
// el mapa del recorrido y los botones para iniciar (desde su ubicación) y
// finalizar la ruta.
import { useCallback } from "react";
import { Alert, FlatList, RefreshControl, StyleSheet, Text, View } from "react-native";
import { useRouter, useFocusEffect } from "expo-router";
import { useQueryClient } from "@tanstack/react-query";
import { Screen } from "@/components/Screen";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { MapaRuta } from "@/components/MapaRuta";
import { ParadaItem } from "@/components/ParadaItem";
import { Cargando, ErrorVista, Vacio } from "@/components/Estados";
import { GradientHeader } from "@/components/GradientHeader";
import { Aparecer, ItemLista } from "@/components/Animations";
import { useRutaActiva, useManifiesto, useNavegacion, useIniciarRuta, useFinalizarRuta, claves } from "@/features/ruta/hooks";
import { useUbicacionActual } from "@/hooks/useUbicacionActual";
import { useEnviarUbicacion } from "@/hooks/useEnviarUbicacion";
import { mensajeDeError } from "@/api/client";
import { useTheme, fontSize, spacing } from "@/theme";

export default function RutaScreen() {
  const router = useRouter();
  const { colors } = useTheme();
  const ruta = useRutaActiva();
  const manifiesto = useManifiesto();
  const navegacion = useNavegacion();
  const ubicacion = useUbicacionActual();
  const iniciar = useIniciarRuta();
  const finalizar = useFinalizarRuta();
  const qc = useQueryClient();

  // Envía la posición del conductor mientras tenga una ruta activa (foreground).
  useEnviarUbicacion(!!ruta.data && ruta.data.estado !== "FINALIZADA");

  // Al volver a esta pestaña, vuelve a pedir los datos (se ven los cambios al instante).
  useFocusEffect(
    useCallback(() => {
      qc.invalidateQueries({ queryKey: claves.rutaActiva });
      qc.invalidateQueries({ queryKey: claves.manifiesto });
      qc.invalidateQueries({ queryKey: claves.navegacion });
    }, [qc])
  );

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

  // Cierra el día (con confirmación). Solo disponible si no quedan pendientes.
  const finalizarRuta = () => {
    Alert.alert("Cerrar el día", "¿Cerrar la ruta de hoy? Ya gestionaste todas las paradas.", [
      { text: "Cancelar", style: "cancel" },
      {
        text: "Cerrar",
        style: "destructive",
        onPress: () =>
          finalizar.mutate(undefined, {
            onSuccess: (r) => Alert.alert("Día cerrado", r.mensaje),
            onError: (e) => Alert.alert("No se pudo cerrar", mensajeDeError(e)),
          }),
      },
    ]);
  };

  // Total y pendientes de la ruta; solo se puede cerrar el día sin pendientes.
  const totalParadas = ruta.data?.total_paradas ?? 0;
  const pendientes = ruta.data?.pendientes ?? 0;
  const puedeCerrar = !!ruta.data && totalParadas > 0 && pendientes === 0;

  // Cabecera de la lista: degradado con resumen, mapa montado y acciones.
  const Cabecera = (
    <View style={estilos.cabecera}>
      {ruta.data && (
        <GradientHeader>
          <Text style={estilos.saludo}>Hola 👋</Text>
          <Text style={estilos.nombreRuta}>{ruta.data.nombre}</Text>
          <Text style={estilos.codigo}>
            {ruta.data.codigo ?? "—"} · {ruta.data.estado.replace("_", " ").toLowerCase()}
          </Text>
          <View style={estilos.contadores}>
            <Contador valor={ruta.data.pendientes} etiqueta="Pendientes" />
            <Contador valor={ruta.data.entregadas} etiqueta="Entregadas" />
            <Contador valor={ruta.data.fallidas} etiqueta="Fallidas" />
          </View>
        </GradientHeader>
      )}

      <Aparecer style={estilos.secciones}>
        <Card style={{ marginTop: -spacing.lg, padding: spacing.sm }}>
          <MapaRuta paradas={navegacion.data?.paradas ?? []} />
        </Card>

        <Button titulo="Iniciar ruta desde mi ubicación" onPress={iniciarRuta} cargando={ubicacion.cargando || iniciar.isPending} />

        <Text style={[estilos.seccion, { color: colors.ink }]}>Paradas ({paradas.length})</Text>
      </Aparecer>
    </View>
  );

  // Pie de la lista: cierre del día. El botón solo aparece cuando ya no hay
  // paradas pendientes; mientras tanto, muestra el progreso que falta.
  const Pie = ruta.data ? (
    <Aparecer style={estilos.pie}>
      <Card>
        <Text style={[estilos.cierreTitulo, { color: colors.ink }]}>Cierre del día</Text>
        {puedeCerrar ? (
          <>
            <Text style={[estilos.cierreTexto, { color: colors.muted }]}>
              Todas las paradas están gestionadas. Ya puedes cerrar el día.
            </Text>
            <Button titulo="Cerrar el día" onPress={finalizarRuta} cargando={finalizar.isPending} />
          </>
        ) : (
          <Text style={[estilos.cierreTexto, { color: colors.muted }]}>
            Entrega o reporta todas las paradas para cerrar el día. Faltan {pendientes} de {totalParadas}.
          </Text>
        )}
      </Card>
    </Aparecer>
  ) : null;

  if (ruta.isLoading || manifiesto.isLoading) return <Screen><Cargando /></Screen>;

  if (sinRuta) {
    return (
      <Screen>
        <Vacio titulo="No tienes una ruta asignada" detalle="Cuando el administrador te asigne pedidos, aparecerán aquí." />
      </Screen>
    );
  }

  if (ruta.isError) {
    return <Screen><ErrorVista mensaje={mensajeDeError(ruta.error)} onReintentar={refrescar} /></Screen>;
  }

  return (
    <Screen conPadding={false}>
      <FlatList
        data={paradas}
        keyExtractor={(p) => String(p.pedido_id)}
        ListHeaderComponent={Cabecera}
        ListFooterComponent={Pie}
        renderItem={({ item, index }) => (
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

// Contador compacto para el resumen en degradado (texto blanco). Recibe: { valor, etiqueta }.
function Contador({ valor, etiqueta }: { valor: number; etiqueta: string }) {
  return (
    <View style={estilos.contador}>
      <Text style={estilos.contadorValor}>{valor}</Text>
      <Text style={estilos.contadorEtiqueta}>{etiqueta}</Text>
    </View>
  );
}

const BLANCO = "#FFFFFF";

const estilos = StyleSheet.create({
  lista: { paddingHorizontal: spacing.lg, paddingBottom: spacing.lg },
  cabecera: { marginBottom: spacing.md, marginHorizontal: -spacing.lg },
  secciones: { gap: spacing.md, paddingHorizontal: spacing.lg },
  saludo: { color: BLANCO, fontSize: fontSize.body, opacity: 0.9, fontWeight: "600" },
  nombreRuta: { color: BLANCO, fontSize: fontSize.display, fontWeight: "800", marginTop: 2 },
  codigo: { color: BLANCO, fontSize: fontSize.body, marginTop: 2, opacity: 0.9, textTransform: "lowercase" },
  contadores: { flexDirection: "row", justifyContent: "space-around", marginTop: spacing.xl },
  contador: { alignItems: "center" },
  contadorValor: { color: BLANCO, fontSize: fontSize.title, fontWeight: "800" },
  contadorEtiqueta: { color: BLANCO, fontSize: fontSize.caption, opacity: 0.9 },
  seccion: { fontSize: fontSize.subtitle, fontWeight: "700", marginTop: spacing.sm },
  pie: { marginTop: spacing.lg, gap: spacing.md },
  cierreTitulo: { fontSize: fontSize.subtitle, fontWeight: "800", marginBottom: spacing.xs },
  cierreTexto: { fontSize: fontSize.body, marginBottom: spacing.md },
});
