// Pantalla principal del conductor: su ruta activa con la secuencia de paradas,
// el mapa del recorrido y los botones para iniciar (desde su ubicación) y
// finalizar la ruta.
import { useCallback } from "react";
import { Alert, FlatList, RefreshControl, StyleSheet, View } from "react-native";
import { useRouter, useFocusEffect } from "expo-router";
import { useQueryClient } from "@tanstack/react-query";
import { Screen } from "@/components/Screen";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { MapaWeb } from "@/components/MapaWeb";
import { ParadaItem } from "@/components/ParadaItem";
import { ErrorVista, Vacio } from "@/components/Estados";
import { GradientHeader } from "@/components/GradientHeader";
import { Cabecera } from "@/components/Cabecera";
import { CamionCargando } from "@/components/CamionCargando";
import { Aparecer, ItemLista, BarraProgreso, Contador, IndicadorEnVivo } from "@/components/Animations";
import { Texto } from "@/components/Texto";
import { useRutaActiva, useManifiesto, useNavegacion, useIniciarRuta, useFinalizarRuta, claves } from "@/features/ruta/hooks";
import { useUbicacionActual } from "@/hooks/useUbicacionActual";
import { useEnviarUbicacion } from "@/hooks/useEnviarUbicacion";
import { mensajeDeError } from "@/api/client";
import { useTheme, spacing } from "@/theme";

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

  // Encabezado de la lista: degradado con resumen, mapa montado y acciones.
  const Encabezado = (
    <View style={estilos.cabecera}>
      {ruta.data && (
        <GradientHeader>
          <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
            <Texto variante="body" color={colors.white} style={{ opacity: 0.9 }}>Hola 👋</Texto>
            <IndicadorEnVivo activo={ruta.isFetching || manifiesto.isFetching} />
          </View>
          <Texto variante="display" color={colors.white}>{ruta.data.nombre}</Texto>
          <Texto variante="body" color={colors.white} style={{ opacity: 0.9, textTransform: "lowercase" }}>
            {(ruta.data.codigo ?? "—")} · {ruta.data.estado.replace("_", " ").toLowerCase()}
          </Texto>

          <View style={{ marginTop: spacing.lg }}>
            <BarraProgreso valor={ruta.data.entregadas} total={ruta.data.total_paradas} />
          </View>

          <View style={estilos.contadores}>
            <ContadorEtiqueta valor={ruta.data.pendientes} etiqueta="Pendientes" />
            <ContadorEtiqueta valor={ruta.data.entregadas} etiqueta="Entregadas" />
            <ContadorEtiqueta valor={ruta.data.fallidas} etiqueta="Fallidas" />
          </View>
        </GradientHeader>
      )}

      <Aparecer style={estilos.secciones}>
        <Card style={{ marginTop: -spacing.xl, padding: spacing.sm }}>
          <MapaWeb paradas={manifiesto.data?.paradas ?? []} />
        </Card>

        <Button titulo="Iniciar ruta desde mi ubicación" onPress={iniciarRuta} cargando={ubicacion.cargando || iniciar.isPending} />

        <Texto variante="subtitle" color={colors.ink} style={estilos.seccion}>Paradas ({paradas.length})</Texto>
      </Aparecer>
    </View>
  );

  // Pie de la lista: cierre del día. El botón solo aparece cuando ya no hay
  // paradas pendientes; mientras tanto, muestra el progreso que falta.
  const Pie = ruta.data ? (
    <Aparecer style={{ ...estilos.pie, paddingHorizontal: spacing.lg }}>
      <Card>
        <Texto variante="subtitle" color={colors.ink} style={estilos.cierreTitulo}>Cierre del día</Texto>
        {puedeCerrar ? (
          <>
            <Texto variante="body" color={colors.muted} style={estilos.cierreTexto}>
              Todas las paradas están gestionadas. Ya puedes cerrar el día.
            </Texto>
            <Button titulo="Cerrar el día" onPress={finalizarRuta} cargando={finalizar.isPending} />
          </>
        ) : (
          <>
            <View style={{ marginBottom: spacing.sm }}>
              <BarraProgreso valor={ruta.data.entregadas} total={totalParadas} color={colors.brand} fondo={colors.border} />
            </View>
            <Texto variante="body" color={colors.muted} style={estilos.cierreTexto}>
              Entrega o reporta todas las paradas para cerrar el día. Faltan {pendientes} de {totalParadas}.
            </Texto>
          </>
        )}
      </Card>
    </Aparecer>
  ) : null;

  if (ruta.isLoading || manifiesto.isLoading) {
    return (
      <Screen conPadding={false}>
        <Cabecera titulo="Ruta" />
        <CamionCargando texto="Cargando tu ruta…" />
      </Screen>
    );
  }

  if (sinRuta) {
    return (
      <Screen conPadding={false}>
        <Cabecera titulo="Ruta" />
        <Vacio titulo="No tienes una ruta asignada" detalle="Cuando el administrador te asigne pedidos, aparecerán aquí." />
      </Screen>
    );
  }

  if (ruta.isError) {
    return (
      <Screen conPadding={false}>
        <Cabecera titulo="Ruta" />
        <ErrorVista mensaje={mensajeDeError(ruta.error)} onReintentar={refrescar} />
      </Screen>
    );
  }

  return (
    <Screen conPadding={false}>
      <Cabecera titulo="Ruta" />
      <FlatList
        data={paradas}
        keyExtractor={(p) => String(p.pedido_id)}
        ListHeaderComponent={Encabezado}
        ListFooterComponent={Pie}
        renderItem={({ item, index }) => (
          <View style={{ paddingHorizontal: spacing.lg }}>
            <ItemLista index={index}>
              <ParadaItem parada={item} onPress={() => router.push(`/parada/${item.pedido_id}`)} />
            </ItemLista>
          </View>
        )}
        contentContainerStyle={estilos.lista}
        ItemSeparatorComponent={() => <View style={{ height: spacing.md }} />}
        refreshControl={<RefreshControl refreshing={manifiesto.isFetching} onRefresh={refrescar} />}
      />
    </Screen>
  );
}

// Cifra animada con su etiqueta (texto blanco sobre el degradado). Recibe: { valor, etiqueta }.
function ContadorEtiqueta({ valor, etiqueta }: { valor: number; etiqueta: string }) {
  const { colors } = useTheme();
  return (
    <View style={estilos.contador}>
      <Contador valor={valor} variante="title" color={colors.white} />
      <Texto variante="caption" color={colors.white} style={{ opacity: 0.9 }}>{etiqueta}</Texto>
    </View>
  );
}

const estilos = StyleSheet.create({
  lista: { paddingBottom: spacing.lg },
  cabecera: { marginBottom: spacing.md },
  secciones: { gap: spacing.md, paddingHorizontal: spacing.lg },
  contadores: { flexDirection: "row", justifyContent: "space-around", marginTop: spacing.xl },
  contador: { alignItems: "center" },
  seccion: { marginTop: spacing.sm },
  pie: { marginTop: spacing.lg, gap: spacing.md },
  cierreTitulo: { marginBottom: spacing.xs },
  cierreTexto: { marginBottom: spacing.md },
});
