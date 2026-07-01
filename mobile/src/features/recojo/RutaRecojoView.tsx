// Vista de ruta de recojo: resumen, mapa, lista de paradas y cierre del día.
import { useCallback, useState } from "react";
import { Alert, FlatList, RefreshControl, StyleSheet, View } from "react-native";
import { useRouter, useFocusEffect } from "expo-router";
import { useQueryClient } from "@tanstack/react-query";
import { Screen } from "@/components/Screen";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { Mapa } from "@/components/Mapa";
import { Cargando, ErrorVista, Vacio } from "@/components/Estados";
import { GradientHeader } from "@/components/GradientHeader";
import { Cabecera } from "@/components/Cabecera";
import { Aparecer, ItemLista, BarraProgreso, Contador, IndicadorEnVivo } from "@/components/Animations";
import { Texto } from "@/components/Texto";
import { useRutaActiva, useFinalizarRuta, claves } from "@/features/ruta/hooks";
import { useManifiestoRecojo, useIniciarRecojo, clavesRecojo } from "@/features/recojo/hooks";
import { useReanudarRuta } from "@/features/incidencia/hooks";
import { useUbicacionActual } from "@/hooks/useUbicacionActual";
import { useRastreoUbicacion } from "@/hooks/useRastreoUbicacion";
import { useEnviarUbicacion } from "@/hooks/useEnviarUbicacion";
import { mensajeDeError } from "@/api/client";
import { abrirNavegacionRuta } from "@/services/navegacion";
import { useTheme, spacing } from "@/theme";
import type { ParadaManifiesto, ParadaRecojo } from "@/types/api";

// Componente principal de la ruta de recojo. Sin params.
export function RutaRecojoView() {
  const router = useRouter();
  const { colors } = useTheme();
  const ruta = useRutaActiva();
  const manifiesto = useManifiestoRecojo();
  const ubicacion = useUbicacionActual();
  const iniciar = useIniciarRecojo();
  const finalizar = useFinalizarRuta();
  const reanudar = useReanudarRuta();
  const pausada = !!ruta.data?.pausada;
  const qc = useQueryClient();
  const [refrescando, setRefrescando] = useState(false);

  // Rastrea y envía la ubicación mientras la ruta esté activa.
  const rutaEnCurso = !!ruta.data && ruta.data.estado !== "FINALIZADA";
  useRastreoUbicacion(rutaEnCurso);
  useEnviarUbicacion(rutaEnCurso);

  // Invalida consultas al enfocar la pantalla.
  useFocusEffect(useCallback(() => {
    qc.invalidateQueries({ queryKey: claves.rutaActiva });
    qc.invalidateQueries({ queryKey: clavesRecojo.manifiesto });
  }, [qc]));

  const paradas: ParadaRecojo[] = manifiesto.data?.paradas ?? [];
  // RECOGIDO e INGRESADO cuentan como recogido: si almacén ya ingresó el recojo, para el conductor sigue recogido.
  const RECOGIDOS = ["RECOGIDO", "INGRESADO"];
  const pendientes = paradas.filter((p) => !RECOGIDOS.includes(p.estado)).sort((a, b) => a.secuencia - b.secuencia);

  const puntosNavegar = pendientes
    .filter((p) => p.latitud != null && p.longitud != null)
    .map((p) => ({ lat: p.latitud, lng: p.longitud }));

  const paradasMapa = paradas.map((p) => ({
    secuencia: p.secuencia, detalle_id: p.recojo_id, pedido_id: p.recojo_id, codigo: p.codigo,
    cliente_origen: p.cliente_origen, nombre_destinatario: p.cliente_origen, telefono_destinatario: null,
    direccion_destino: p.direccion_origen, distrito: p.distrito, latitud: p.latitud, longitud: p.longitud,
    peso_kg: null, estado_entrega: RECOGIDOS.includes(p.estado) ? "ENTREGADO" : "PENDIENTE", url_evidencia: p.url_guia,
  })) as ParadaManifiesto[];

  // Refresca ruta y manifiesto juntos. Pull-to-refresh.
  const refrescar = async () => {
    setRefrescando(true);
    try { await Promise.all([ruta.refetch(), manifiesto.refetch()]); } finally { setRefrescando(false); }
  };

  // Inicia y optimiza la ruta desde la ubicación actual.
  const iniciarRuta = async () => {
    if (!ruta.data) return;
    const coords = await ubicacion.obtener();
    if (!coords) { if (ubicacion.error) Alert.alert("Ubicación", ubicacion.error); return; }
    iniciar.mutate({ rutaId: ruta.data.ruta_id, coords }, {
      onSuccess: (r) => Alert.alert("Ruta lista", `Se ordenaron ${r.total_paradas} puntos de recojo desde tu ubicación.`),
      onError: (e) => Alert.alert("Error", mensajeDeError(e)),
    });
  };

  // Cierra el día de recojo tras confirmación.
  const cerrarDia = () => {
    Alert.alert("Cerrar el día", "¿Cerrar la ruta de recojo de hoy?", [
      { text: "Cancelar", style: "cancel" },
      { text: "Cerrar", style: "destructive", onPress: () => finalizar.mutate(undefined, {
        onSuccess: (r) => Alert.alert("Día cerrado", r.mensaje),
        onError: (e) => Alert.alert("No se pudo cerrar", mensajeDeError(e)),
      }) },
    ]);
  };

  // Reanuda la ruta cerrando la incidencia abierta.
  const reanudarRutaActiva = () => {
    if (!ruta.data?.incidencia_id) return;
    reanudar.mutate({ incidenciaId: ruta.data.incidencia_id }, { onError: (e) => Alert.alert("No se pudo reanudar", mensajeDeError(e)) });
  };

  const total = ruta.data?.total_paradas ?? 0;
  const recogidas = ruta.data?.entregadas ?? 0;
  const puedeCerrar = !!ruta.data && total > 0 && (ruta.data.pendientes ?? 0) === 0 && !pausada;

  const Encabezado = (
    <View style={{ marginBottom: spacing.md }}>
      {ruta.data && (
        <GradientHeader>
          <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
            <Texto variante="body" color={colors.white} style={{ opacity: 0.9 }}>Ruta de recojo 📦</Texto>
            <IndicadorEnVivo activo={ruta.isFetching || manifiesto.isFetching} />
          </View>
          <Texto variante="display" color={colors.white}>{ruta.data.nombre}</Texto>
          <Texto variante="body" color={colors.white} style={{ opacity: 0.9, textTransform: "lowercase" }}>
            {(ruta.data.codigo ?? "—")} · {ruta.data.estado.replace("_", " ").toLowerCase()}
          </Texto>
          <View style={{ marginTop: spacing.lg }}>
            <BarraProgreso valor={recogidas} total={total} porEstado />
          </View>
          <View style={estilos.contadores}>
            <ContadorEtiqueta valor={ruta.data.pendientes ?? 0} etiqueta="Pendientes" />
            <ContadorEtiqueta valor={recogidas} etiqueta="Recogidos" />
          </View>
        </GradientHeader>
      )}

      <Aparecer style={{ gap: spacing.md, paddingHorizontal: spacing.lg }}>
        <Card style={{ marginTop: spacing.md, padding: spacing.sm }}>
          <Mapa paradas={paradasMapa} />
        </Card>
        <Button titulo="Iniciar ruta desde mi ubicación" onPress={iniciarRuta} cargando={ubicacion.cargando || iniciar.isPending} />
        {puntosNavegar.length > 0 && (
          <Button titulo="Navegar en Google Maps" variante="secondary" onPress={() => abrirNavegacionRuta(puntosNavegar)} />
        )}
        {pausada ? (
          <Card style={{ backgroundColor: colors.dangerSoft }}>
            <Texto variante="bodyMedium" color={colors.danger}>🛠️ Ruta pausada por avería</Texto>
            <Texto variante="caption" color={colors.danger} style={{ marginTop: 2, marginBottom: spacing.sm }}>Reanúdala para seguir recogiendo.</Texto>
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
        <View style={{ marginTop: spacing.sm }}>
          <Texto variante="subtitle" color={colors.ink}>Puntos de recojo</Texto>
          <Texto variante="caption" color={colors.muted}>{pendientes.length} pendiente(s) de {total}</Texto>
        </View>
      </Aparecer>
    </View>
  );

  const Pie = ruta.data ? (
    <Aparecer style={{ marginTop: spacing.lg, gap: spacing.md, paddingHorizontal: spacing.lg }}>
      <Card>
        <Texto variante="subtitle" color={colors.ink} style={{ marginBottom: spacing.xs }}>Cierre del día</Texto>
        {puedeCerrar ? (
          <>
            <Texto variante="body" color={colors.muted} style={{ marginBottom: spacing.md }}>Todos los recojos están registrados. Ya puedes cerrar el día.</Texto>
            <Button titulo="Cerrar el día" onPress={cerrarDia} cargando={finalizar.isPending} />
          </>
        ) : (
          <Texto variante="body" color={colors.muted}>Registra todos los recojos para cerrar el día. Faltan {ruta.data.pendientes ?? 0} de {total}.</Texto>
        )}
      </Card>
    </Aparecer>
  ) : null;

  if (ruta.isLoading || manifiesto.isLoading) return <Screen conPadding={false}><Cabecera titulo="Ruta" /><Cargando /></Screen>;
  if (manifiesto.isError) return <Screen conPadding={false}><Cabecera titulo="Ruta" /><ErrorVista mensaje={mensajeDeError(manifiesto.error)} onReintentar={refrescar} /></Screen>;

  return (
    <Screen conPadding={false}>
      <Cabecera titulo="Ruta" />
      <FlatList
        data={pendientes}
        keyExtractor={(p) => String(p.recojo_id)}
        ListHeaderComponent={Encabezado}
        ListFooterComponent={Pie}
        renderItem={({ item, index }) => (
          <View style={{ paddingHorizontal: spacing.lg }}>
            <ItemLista index={index}>
              <Card onPress={() => router.push(`/recojo/${item.recojo_id}`)}>
                <Texto variante="label" color={colors.muted}>{item.codigo ?? `Recojo ${item.recojo_id}`}</Texto>
                <Texto variante="subtitle" color={colors.ink}>{item.cliente_origen}</Texto>
                <Texto variante="body" color={colors.text}>{item.direccion_origen}</Texto>
                <Texto variante="caption" color={colors.muted}>{item.distrito || "—"}{item.volumen_estimado_m3 != null ? ` · ${item.volumen_estimado_m3} m³` : ""}</Texto>
              </Card>
            </ItemLista>
          </View>
        )}
        contentContainerStyle={{ paddingBottom: spacing.lg }}
        ItemSeparatorComponent={() => <View style={{ height: spacing.md }} />}
        ListEmptyComponent={<View style={{ paddingHorizontal: spacing.lg }}><Vacio titulo="No quedan recojos pendientes" detalle="Cierra el día desde el botón de abajo." /></View>}
        refreshControl={<RefreshControl refreshing={refrescando} onRefresh={refrescar} />}
      />
    </Screen>
  );
}

// Cifra animada con etiqueta. Recibe: { valor, etiqueta }.
function ContadorEtiqueta({ valor, etiqueta }: { valor: number; etiqueta: string }) {
  const { colors } = useTheme();
  return (
    <View style={{ alignItems: "center" }}>
      <Contador valor={valor} variante="title" color={colors.white} />
      <Texto variante="caption" color={colors.white} style={{ opacity: 0.9 }}>{etiqueta}</Texto>
    </View>
  );
}

const estilos = StyleSheet.create({
  contadores: { flexDirection: "row", justifyContent: "space-around", marginTop: spacing.xl },
});
