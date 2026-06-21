// Detalle de una parada: muestra los datos del pedido y permite (a) marcar
// ENTREGADO adjuntando una foto (POD) o (b) reportar un problema (falla), que
// el administrador verá en su panel de reportes.
import { useState } from "react";
import { Alert, Linking, Pressable, ScrollView, StyleSheet, TextInput, View } from "react-native";
import { Image } from "expo-image";
import * as ImagePicker from "expo-image-picker";
import { Ionicons } from "@expo/vector-icons";
import { useQuery } from "@tanstack/react-query";
import { useLocalSearchParams, useRouter } from "expo-router";
import { Screen } from "@/components/Screen";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { Cabecera } from "@/components/Cabecera";
import { EstadoBadge } from "@/components/EstadoBadge";
import { Cargando, Vacio } from "@/components/Estados";
import { Aparecer, CheckEntrega } from "@/components/Animations";
import { Texto } from "@/components/Texto";
import { abrirNavegacion } from "@/services/navegacion";
import { useManifiesto } from "@/features/ruta/hooks";
import { useEntregarConEvidencia, useReportarFalla } from "@/features/entrega/hooks";
import { obtenerMotivos } from "@/api/conductor";
import { mensajeDeError } from "@/api/client";
import { urlMedia } from "@/api/config";
import { useTheme, fontSize, radius, spacing } from "@/theme";
import type { ParadaManifiesto } from "@/types/api";

// Lista por defecto si aún no llegan los motivos del backend (CUS-06).
const MOTIVOS_DEFECTO = ["Cliente ausente", "Dirección incorrecta", "Pedido rechazado", "Zona inaccesible", "Otro"];

export default function ParadaScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const pedidoId = Number(id);
  const router = useRouter();
  const { colors } = useTheme();
  const manifiesto = useManifiesto();
  const entregar = useEntregarConEvidencia();
  const reportar = useReportarFalla();

  // CUS-06: los motivos vienen del catálogo del backend (con respaldo por defecto).
  const motivosQuery = useQuery({ queryKey: ["motivos"], queryFn: obtenerMotivos, staleTime: 60_000 });
  const motivos = motivosQuery.data && motivosQuery.data.length ? motivosQuery.data : MOTIVOS_DEFECTO;

  const [foto, setFoto] = useState<string | null>(null);
  const [modoReporte, setModoReporte] = useState(false);
  const [motivo, setMotivo] = useState(MOTIVOS_DEFECTO[0]);
  const [descripcion, setDescripcion] = useState("");
  // Estado para mostrar el check animado tras confirmar entrega.
  const [exito, setExito] = useState(false);

  const parada = manifiesto.data?.paradas.find((p: ParadaManifiesto) => p.pedido_id === pedidoId);

  // Abre la cámara y guarda la foto elegida.
  const tomarFoto = async () => {
    const permiso = await ImagePicker.requestCameraPermissionsAsync();
    if (!permiso.granted) {
      Alert.alert("Cámara", "Necesitamos permiso de cámara para la evidencia.");
      return;
    }
    const res = await ImagePicker.launchCameraAsync({ quality: 0.6 });
    if (!res.canceled) setFoto(res.assets[0].uri);
  };

  // Abre la galería y guarda la imagen elegida.
  const elegirFoto = async () => {
    const res = await ImagePicker.launchImageLibraryAsync({ quality: 0.6 });
    if (!res.canceled) setFoto(res.assets[0].uri);
  };

  // Confirma la entrega: marca ENTREGADO y sube la evidencia.
  const confirmarEntrega = () => {
    if (!foto) return;
    entregar.mutate(
      { pedidoId, uriFoto: foto },
      {
        onSuccess: () => {
          // Muestra el check animado y vuelve atrás tras 900 ms.
          setExito(true);
          setTimeout(() => router.back(), 900);
        },
        onError: (e) => Alert.alert("Error", mensajeDeError(e)),
      }
    );
  };

  // Envía el reporte de falla: marca FALLIDO y crea el reporte para el admin.
  const enviarReporte = () => {
    reportar.mutate(
      { pedidoId, motivo, descripcion: descripcion.trim() || undefined },
      {
        onSuccess: () => {
          Alert.alert("Reporte enviado", "El administrador lo verá en sus reportes.");
          router.back();
        },
        onError: (e) => Alert.alert("Error", mensajeDeError(e)),
      }
    );
  };

  if (manifiesto.isLoading) return <Screen conPadding={false}><Cabecera titulo="Entrega" atras /><Cargando /></Screen>;
  if (!parada) return <Screen conPadding={false}><Cabecera titulo="Entrega" atras /><Vacio titulo="Pedido no encontrado" /></Screen>;

  const gestionada = parada.estado_entrega !== "PENDIENTE";

  // Capa de éxito: muestra el check animado mientras el componente navega atrás.
  if (exito) {
    return (
      <Screen>
        <View style={{ flex: 1, alignItems: "center", justifyContent: "center", gap: spacing.md }}>
          <CheckEntrega color={colors.success} />
          <Texto variante="subtitle" color={colors.ink}>¡Entrega registrada!</Texto>
        </View>
      </Screen>
    );
  }

  return (
    <Screen conPadding={false}>
      <Cabecera titulo="Entrega" atras />
      <ScrollView contentContainerStyle={estilos.contenido}>
        <Aparecer style={estilos.grupo}>
          <Card>
            <View style={estilos.encabezado}>
              <Texto variante="label" color={colors.muted} style={estilos.codigo}>{parada.codigo ?? `Pedido ${parada.pedido_id}`}</Texto>
              <EstadoBadge estado={parada.estado_entrega} />
            </View>

            {/* Destacar a quién y de quién es el pedido */}
            <Texto variante="caption" color={colors.muted} style={estilos.rol}>Para</Texto>
            <Texto variante="title" color={colors.ink} style={estilos.destacado}>{parada.nombre_destinatario || "—"}</Texto>

            <Texto variante="caption" color={colors.muted} style={[estilos.rol, { marginTop: spacing.md }]}>De</Texto>
            <Texto variante="subtitle" color={colors.text} style={estilos.empresa}>{parada.cliente_origen}</Texto>

            <View style={[estilos.separador, { backgroundColor: colors.border }]} />

            <Dato etiqueta="Dirección" valor={parada.direccion_destino} c={colors} />
            <Dato etiqueta="Distrito" valor={parada.distrito || "—"} c={colors} />
            {parada.telefono_destinatario ? (
              <>
                <Dato etiqueta="Teléfono" valor={parada.telefono_destinatario} c={colors} />
                <Pressable
                  onPress={() => Linking.openURL(`tel:${parada.telefono_destinatario}`)}
                  accessibilityRole="button"
                  accessibilityLabel="Llamar al destinatario"
                  style={[estilos.llamar, { backgroundColor: colors.brandSoft }]}
                >
                  <Ionicons name="call" size={18} color={colors.brand} />
                  <Texto variante="body" color={colors.brand} style={estilos.llamarTexto}>Llamar</Texto>
                </Pressable>
              </>
            ) : null}

            {parada.latitud != null && parada.longitud != null && (
              <Pressable
                onPress={() => abrirNavegacion(parada.latitud as number, parada.longitud as number, parada.direccion_destino)}
                accessibilityRole="button"
                accessibilityLabel="Navegar a la dirección"
                style={[estilos.navegar, { backgroundColor: colors.brand }]}
              >
                <Ionicons name="navigate" size={18} color={colors.white} />
                <Texto variante="body" color={colors.white} style={estilos.navegarTexto}>Navegar con Google Maps</Texto>
              </Pressable>
            )}
          </Card>

          {gestionada ? (
            <Card style={{ backgroundColor: parada.estado_entrega === "ENTREGADO" ? colors.successSoft : colors.dangerSoft }}>
              <Texto variante="subtitle" color={parada.estado_entrega === "ENTREGADO" ? colors.success : colors.danger} style={{ textAlign: "center" }}>
                {parada.estado_entrega === "ENTREGADO" ? "Esta parada ya fue entregada." : "Esta parada fue reportada como fallida."}
              </Texto>
              {/* CUS-26: la foto POD se lee del backend (persistida en BD), no de un caché temporal. */}
              {parada.estado_entrega === "ENTREGADO" && urlMedia(parada.url_evidencia) && (
                <Image
                  source={{ uri: urlMedia(parada.url_evidencia) }}
                  style={estilos.evidenciaGuardada}
                  contentFit="cover"
                  transition={200}
                />
              )}
            </Card>
          ) : modoReporte ? (
            <Card>
              <Texto variante="subtitle" color={colors.ink} style={estilos.titulo}>Reportar problema</Texto>
              <Texto variante="caption" color={colors.muted} style={estilos.sub}>Motivo de la falla</Texto>
              <View style={estilos.motivos}>
                {motivos.map((m: string) => {
                  const activo = motivo === m;
                  return (
                    <Pressable key={m} onPress={() => setMotivo(m)} accessibilityRole="button" accessibilityLabel={m}
                      style={[estilos.motivoChip, { borderColor: activo ? colors.brand : colors.border, backgroundColor: activo ? colors.brandSoft : colors.surface }]}>
                      <Texto variante="bodyMedium" color={activo ? colors.brand : colors.text}>{m}</Texto>
                    </Pressable>
                  );
                })}
              </View>
              <TextInput
                value={descripcion}
                onChangeText={setDescripcion}
                placeholder="Detalle (opcional)"
                placeholderTextColor={colors.muted}
                multiline
                style={[estilos.area, { borderColor: colors.border, color: colors.ink, backgroundColor: colors.surface }]}
              />
              <View style={{ gap: spacing.sm, marginTop: spacing.md }}>
                <Button titulo={reportar.isPending ? "Enviando…" : "Enviar reporte"} variante="danger" onPress={enviarReporte} cargando={reportar.isPending} />
                <Button titulo="Cancelar" variante="secondary" onPress={() => setModoReporte(false)} />
              </View>
            </Card>
          ) : (
            <>
              <Card>
                <Texto variante="subtitle" color={colors.ink} style={estilos.titulo}>Evidencia de entrega (foto)</Texto>
                {foto ? (
                  <Image source={{ uri: foto }} style={estilos.preview} contentFit="cover" />
                ) : (
                  <View style={[estilos.placeholder, { borderColor: colors.border }]}>
                    <Texto variante="body" color={colors.muted}>Adjunta una foto como prueba de entrega</Texto>
                  </View>
                )}
                <View style={estilos.botonesFoto}>
                  <View style={{ flex: 1 }}><Button titulo="Tomar foto" variante="secondary" onPress={tomarFoto} /></View>
                  <View style={{ flex: 1 }}><Button titulo="Galería" variante="secondary" onPress={elegirFoto} /></View>
                </View>
                <View style={{ marginTop: spacing.lg }}>
                  <Button titulo={entregar.isPending ? "Registrando…" : "Marcar como entregado"} onPress={confirmarEntrega} cargando={entregar.isPending} deshabilitado={!foto} />
                </View>
              </Card>

              <Button titulo="Reportar un problema" variante="danger" onPress={() => setModoReporte(true)} />
            </>
          )}
        </Aparecer>
      </ScrollView>
    </Screen>
  );
}

// Fila etiqueta/valor del detalle. Recibe: { etiqueta, valor, c (paleta) }.
function Dato({ etiqueta, valor, c }: { etiqueta: string; valor: string; c: { muted: string; text: string } }) {
  return (
    <View style={estilos.dato}>
      <Texto variante="caption" color={c.muted} style={estilos.datoEtiqueta}>{etiqueta}</Texto>
      <Texto variante="bodyMedium" color={c.text} style={estilos.datoValor}>{valor}</Texto>
    </View>
  );
}

const estilos = StyleSheet.create({
  contenido: { padding: spacing.lg },
  grupo: { gap: spacing.lg },
  encabezado: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: spacing.md },
  codigo: {},
  rol: { textTransform: "uppercase", letterSpacing: 0.5 },
  destacado: { marginTop: 2 },
  empresa: { marginTop: 2 },
  separador: { height: 1, marginVertical: spacing.md },
  llamar: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: spacing.sm, marginTop: spacing.md, paddingVertical: spacing.sm, borderRadius: radius.md },
  llamarTexto: {},
  navegar: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: spacing.sm, marginTop: spacing.md, paddingVertical: spacing.md, borderRadius: radius.md },
  navegarTexto: {},
  dato: { marginTop: spacing.md },
  datoEtiqueta: {},
  datoValor: {},
  titulo: { marginBottom: spacing.md },
  sub: { marginBottom: spacing.xs },
  preview: { width: "100%", height: 220, borderRadius: radius.md },
  evidenciaGuardada: { width: "100%", height: 200, borderRadius: radius.md, marginTop: spacing.md },
  placeholder: { height: 160, borderRadius: radius.md, borderWidth: 2, borderStyle: "dashed", alignItems: "center", justifyContent: "center" },
  botonesFoto: { flexDirection: "row", gap: spacing.md, marginTop: spacing.md },
  motivos: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  motivoChip: { paddingVertical: spacing.sm, paddingHorizontal: spacing.md, borderRadius: radius.md, borderWidth: 1 },
  area: { minHeight: 80, borderWidth: 1, borderRadius: radius.md, padding: spacing.md, marginTop: spacing.md, fontSize: fontSize.body, textAlignVertical: "top" },
});
