import { useCallback, useState } from "react";
import { Alert, FlatList, RefreshControl, StyleSheet, View } from "react-native";
import { useRouter, useFocusEffect } from "expo-router";
import { useQueryClient } from "@tanstack/react-query";
import { Screen } from "@/components/Screen";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { Mapa } from "@/components/Mapa";
import { ParadaItem } from "@/components/ParadaItem";
import { Cargando, ErrorVista, Vacio } from "@/components/Estados";
import { GradientHeader } from "@/components/GradientHeader";
import { Cabecera } from "@/components/Cabecera";
import { DeslizarPestanas } from "@/components/DeslizarPestanas";
import { Aparecer, ItemLista, BarraProgreso, Contador, IndicadorEnVivo } from "@/components/Animations";
import { Texto } from "@/components/Texto";
import { RutaRecojoView } from "@/features/recojo/RutaRecojoView";
import { abrirNavegacionRuta } from "@/services/navegacion";
import { useRutaActiva, useManifiesto, useNavegacion, useIniciarRuta, useFinalizarRuta, claves } from "@/features/ruta/hooks";
import { useUbicacionActual } from "@/hooks/useUbicacionActual";
import { useRastreoUbicacion } from "@/hooks/useRastreoUbicacion";
import { useEnviarUbicacion } from "@/hooks/useEnviarUbicacion";
import { useReanudarRuta } from "@/features/incidencia/hooks";
import { usePendientesPorPedido } from "@/features/sync/hooks";
import { mensajeDeError } from "@/api/client";
import { BannerSync } from "@/components/BannerSync";
import { useTheme, spacing } from "@/theme";

// Muestra el flujo de entregas o de recojo según el tipo de ruta activa.
export default function RutaScreen() {
  const rutaActiva = useRutaActiva();
  if (rutaActiva.data?.tipo === "RECOJO") return <RutaRecojoView />;
  return <RutaEntregaView />;
}

function RutaEntregaView() {
  const router = useRouter();
  const { colors } = useTheme();
  const ruta = useRutaActiva();
  const manifiesto = useManifiesto();
  const navegacion = useNavegacion();
  const ubicacion = useUbicacionActual();
  const iniciar = useIniciarRuta();
  const finalizar = useFinalizarRuta();
  const reanudar = useReanudarRuta();
  const pausada = !!ruta.data?.pausada;
  const qc = useQueryClient();
  // Paradas con acción en cola offline aún sin subir.
  const pendientesPorPedido = usePendientesPorPedido();

  // Rastrea y envía la posición mientras la ruta esté en curso.
  const rutaEnCurso = !!ruta.data && ruta.data.estado !== "FINALIZADA";
  useRastreoUbicacion(rutaEnCurso);
  useEnviarUbicacion(rutaEnCurso);

  useFocusEffect(
    useCallback(() => {
      qc.invalidateQueries({ queryKey: claves.rutaActiva });
      qc.invalidateQueries({ queryKey: claves.manifiesto });
      qc.invalidateQueries({ queryKey: claves.navegacion });
    }, [qc])
  );

  const paradasPendientes = [...(manifiesto.data?.paradas ?? [])]
    .filter((p) => p.estado_entrega === "PENDIENTE" && !pendientesPorPedido.has(p.pedido_id))
    .sort((a, b) => a.secuencia - b.secuencia);
  const proximas = paradasPendientes.slice(0, 5);
  const sinRuta = (ruta.error as { response?: { status?: number } } | null)?.response?.status === 404;

  const puntosNavegar = paradasPendientes
    .filter((p) => p.latitud != null && p.longitud != null)
    .map((p) => ({ lat: p.latitud, lng: p.longitud }));

  const [refrescando, setRefrescando] = useState(false);

  // Refresca las tres consultas a la vez. Recibe: llamada por pull-to-refresh.
  const refrescar = async () => {
    setRefrescando(true);
    try {
      await Promise.all([ruta.refetch(), manifiesto.refetch(), navegacion.refetch()]);
    } finally {
      setRefrescando(false);
    }
  };

  // Inicia la ruta desde la ubicación actual y solicita optimización al backend.
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

  // Cierra el día con confirmación. Solo disponible sin paradas pendientes.
  const finalizarRuta = () => {
    Alert.alert("Cerrar el día", "¿Cerrar la ruta de hoy? Ya gestionaste todas las paradas.", [
      { text: "Cancelar", style: "cancel" },
      {
        text: "Cerrar",
        style: "destructive",
        onPress: () =>
          finalizar.mutate(undefined, {
            // CUS-28: el backend devuelve la duración; la mostramos como horas trabajadas.
            onSuccess: (r) => {
              const dur = formatDuracion(r.duracion_minutos);
              Alert.alert("Día cerrado", dur ? `${r.mensaje}\nTrabajaste ${dur}.` : r.mensaje);
            },
            onError: (e) => Alert.alert("No se pudo cerrar", mensajeDeError(e)),
          }),
      },
    ]);
  };

  // Reanuda la ruta cerrando la incidencia abierta.
  const reanudarRutaActiva = () => {
    if (!ruta.data?.incidencia_id) return;
    reanudar.mutate(
      { incidenciaId: ruta.data.incidencia_id },
      { onError: (e) => Alert.alert("No se pudo reanudar", mensajeDeError(e)) }
    );
  };

  const totalParadas = ruta.data?.total_paradas ?? 0;
  const pendientes = ruta.data?.pendientes ?? 0;
  const puedeCerrar = !!ruta.data && totalParadas > 0 && pendientes === 0 && !pausada;

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
          {horaLocal(ruta.data.fecha_salida) && (
            <Texto variante="caption" color={colors.white} style={{ opacity: 0.9, marginTop: 2 }}>
              🕑 Salida {horaLocal(ruta.data.fecha_salida)}
            </Texto>
          )}

          <View style={{ marginTop: spacing.lg }}>
            <BarraProgreso valor={ruta.data.entregadas} total={ruta.data.total_paradas} porEstado />
          </View>

          <View style={estilos.contadores}>
            <ContadorEtiqueta valor={ruta.data.pendientes} etiqueta="Pendientes" />
            <ContadorEtiqueta valor={ruta.data.entregadas} etiqueta="Entregadas" />
            <ContadorEtiqueta valor={ruta.data.fallidas} etiqueta="Fallidas" />
          </View>
        </GradientHeader>
      )}

      <Aparecer style={estilos.secciones}>
        <BannerSync />
        <Card style={{ marginTop: spacing.md, padding: spacing.sm }}>
          <Mapa paradas={manifiesto.data?.paradas ?? []} />
        </Card>

        <Button titulo="Iniciar ruta desde mi ubicación" onPress={iniciarRuta} cargando={ubicacion.cargando || iniciar.isPending} />

        {puntosNavegar.length > 0 && (
          <Button titulo="Navegar en Google Maps" variante="secondary" onPress={() => abrirNavegacionRuta(puntosNavegar)} />
        )}

        {pausada ? (
          <Card style={{ backgroundColor: colors.dangerSoft }}>
            <Texto variante="bodyMedium" color={colors.danger}>🛠️ Ruta pausada por avería</Texto>
            <Texto variante="caption" color={colors.danger} style={{ marginTop: 2, marginBottom: spacing.sm }}>
              Reanúdala cuando el vehículo esté listo para seguir entregando.
            </Texto>
            {ruta.data?.ayuda_enviada_en && (
              <Card style={{ backgroundColor: colors.brandSoft, marginBottom: spacing.sm }}>
                <Texto variante="bodyMedium" color={colors.brand}>🚐 Ayuda en camino</Texto>
                {ruta.data.ayuda_detalle && (
                  <Texto variante="caption" color={colors.brandInk} style={{ marginTop: 2 }}>
                    {ruta.data.ayuda_detalle}
                  </Texto>
                )}
              </Card>
            )}
            <Button titulo="Reanudar ruta" onPress={reanudarRutaActiva} cargando={reanudar.isPending} />
          </Card>
        ) : (
          <Button titulo="Auxilio mecánico" variante="danger" onPress={() => router.push("/auxilio")} />
        )}

        <View style={estilos.seccion}>
          <Texto variante="subtitle" color={colors.ink}>Próximas paradas</Texto>
          <Texto variante="caption" color={colors.muted}>
            {proximas.length > 0
              ? `${proximas.length} de ${paradasPendientes.length} pendientes · todas en Pedidos`
              : "No quedan paradas pendientes"}
          </Texto>
        </View>
      </Aparecer>
    </View>
  );

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
              <BarraProgreso valor={ruta.data.entregadas} total={totalParadas} fondo={colors.border} porEstado />
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
        <Cargando />
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
      <DeslizarPestanas>
      <FlatList
        data={proximas}
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
        refreshControl={<RefreshControl refreshing={refrescando} onRefresh={refrescar} />}
      />
      </DeslizarPestanas>
    </Screen>
  );
}

// Convierte fecha ISO a "HH:MM" local. Recibe: string ISO o null.
function horaLocal(iso?: string | null): string | null {
  if (!iso) return null;
  const tieneZona = /[zZ]|[+-]\d\d:?\d\d$/.test(iso);
  const fecha = new Date(tieneZona ? iso : `${iso}Z`);
  return fecha.toLocaleTimeString("es-PE", { hour: "2-digit", minute: "2-digit" });
}

// Formatea minutos como "Xh Ymin". Recibe: minutos o null.
function formatDuracion(min?: number | null): string | null {
  if (min == null) return null;
  const horas = Math.floor(min / 60);
  const minutos = min % 60;
  if (horas && minutos) return `${horas}h ${minutos}min`;
  if (horas) return `${horas}h`;
  return `${minutos}min`;
}

// Cifra animada con etiqueta en blanco. Recibe: { valor, etiqueta }.
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
