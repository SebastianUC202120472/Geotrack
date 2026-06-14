// Detalle de una parada: muestra los datos del pedido y permite (a) marcar
// ENTREGADO adjuntando una foto (POD) o (b) reportar un problema (falla), que
// el administrador verá en su panel de reportes.
import { useState } from "react";
import { Alert, Linking, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from "react-native";
import { Image } from "expo-image";
import * as ImagePicker from "expo-image-picker";
import { Ionicons } from "@expo/vector-icons";
import { useLocalSearchParams, useRouter } from "expo-router";
import { Screen } from "@/components/Screen";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { EstadoBadge } from "@/components/EstadoBadge";
import { Cargando, Vacio } from "@/components/Estados";
import { Aparecer } from "@/components/Animations";
import { useManifiesto } from "@/features/ruta/hooks";
import { useEntregarConEvidencia, useReportarFalla } from "@/features/entrega/hooks";
import { mensajeDeError } from "@/api/client";
import { useTheme, fontSize, radius, spacing } from "@/theme";
import type { ParadaManifiesto } from "@/types/api";

const MOTIVOS = ["Cliente ausente", "Dirección incorrecta", "Pedido rechazado", "Zona inaccesible", "Otro"];

export default function ParadaScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const pedidoId = Number(id);
  const router = useRouter();
  const { colors } = useTheme();
  const manifiesto = useManifiesto();
  const entregar = useEntregarConEvidencia();
  const reportar = useReportarFalla();

  const [foto, setFoto] = useState<string | null>(null);
  const [modoReporte, setModoReporte] = useState(false);
  const [motivo, setMotivo] = useState(MOTIVOS[0]);
  const [descripcion, setDescripcion] = useState("");

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
          Alert.alert("Entrega registrada", "Se guardó la entrega con su evidencia.");
          router.back();
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

  if (manifiesto.isLoading) return <Screen><Cargando /></Screen>;
  if (!parada) return <Screen><Vacio titulo="Pedido no encontrado" /></Screen>;

  const gestionada = parada.estado_entrega !== "PENDIENTE";

  return (
    <Screen conPadding={false}>
      <ScrollView contentContainerStyle={estilos.contenido}>
        <Aparecer style={estilos.grupo}>
          <Card>
            <View style={estilos.encabezado}>
              <Text style={[estilos.codigo, { color: colors.muted }]}>{parada.codigo ?? `Pedido ${parada.pedido_id}`}</Text>
              <EstadoBadge estado={parada.estado_entrega} />
            </View>

            {/* Destacar a quién y de quién es el pedido */}
            <Text style={[estilos.rol, { color: colors.muted }]}>Para</Text>
            <Text style={[estilos.destacado, { color: colors.ink }]}>{parada.nombre_destinatario || "—"}</Text>

            <Text style={[estilos.rol, { color: colors.muted, marginTop: spacing.md }]}>De</Text>
            <Text style={[estilos.empresa, { color: colors.text }]}>{parada.cliente_origen}</Text>

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
                  <Text style={[estilos.llamarTexto, { color: colors.brand }]}>Llamar</Text>
                </Pressable>
              </>
            ) : null}
          </Card>

          {gestionada ? (
            <Card style={{ backgroundColor: parada.estado_entrega === "ENTREGADO" ? colors.successSoft : colors.dangerSoft }}>
              <Text style={{ color: parada.estado_entrega === "ENTREGADO" ? colors.success : colors.danger, fontSize: fontSize.subtitle, fontWeight: "700", textAlign: "center" }}>
                {parada.estado_entrega === "ENTREGADO" ? "Esta parada ya fue entregada." : "Esta parada fue reportada como fallida."}
              </Text>
            </Card>
          ) : modoReporte ? (
            <Card>
              <Text style={[estilos.titulo, { color: colors.ink }]}>Reportar problema</Text>
              <Text style={[estilos.sub, { color: colors.muted }]}>Motivo de la falla</Text>
              <View style={estilos.motivos}>
                {MOTIVOS.map((m) => {
                  const activo = motivo === m;
                  return (
                    <Pressable key={m} onPress={() => setMotivo(m)} accessibilityRole="button" accessibilityLabel={m}
                      style={[estilos.motivoChip, { borderColor: activo ? colors.brand : colors.border, backgroundColor: activo ? colors.brandSoft : colors.surface }]}>
                      <Text style={{ color: activo ? colors.brand : colors.text, fontWeight: "600" }}>{m}</Text>
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
                <Text style={[estilos.titulo, { color: colors.ink }]}>Evidencia de entrega (foto)</Text>
                {foto ? (
                  <Image source={{ uri: foto }} style={estilos.preview} contentFit="cover" />
                ) : (
                  <View style={[estilos.placeholder, { borderColor: colors.border }]}>
                    <Text style={{ color: colors.muted, fontSize: fontSize.body }}>Adjunta una foto como prueba de entrega</Text>
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
      <Text style={[estilos.datoEtiqueta, { color: c.muted }]}>{etiqueta}</Text>
      <Text style={[estilos.datoValor, { color: c.text }]}>{valor}</Text>
    </View>
  );
}

const estilos = StyleSheet.create({
  contenido: { padding: spacing.lg },
  grupo: { gap: spacing.lg },
  encabezado: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: spacing.md },
  codigo: { fontSize: fontSize.body, fontWeight: "700" },
  rol: { fontSize: fontSize.caption, fontWeight: "600", textTransform: "uppercase", letterSpacing: 0.5 },
  destacado: { fontSize: fontSize.title, fontWeight: "800", marginTop: 2 },
  empresa: { fontSize: fontSize.subtitle, fontWeight: "600", marginTop: 2 },
  separador: { height: 1, marginVertical: spacing.md },
  llamar: { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: spacing.sm, marginTop: spacing.md, paddingVertical: spacing.sm, borderRadius: radius.md },
  llamarTexto: { fontSize: fontSize.body, fontWeight: "700" },
  dato: { marginTop: spacing.md },
  datoEtiqueta: { fontSize: fontSize.caption },
  datoValor: { fontSize: fontSize.body, fontWeight: "600" },
  titulo: { fontSize: fontSize.subtitle, fontWeight: "700", marginBottom: spacing.md },
  sub: { fontSize: fontSize.caption, marginBottom: spacing.xs },
  preview: { width: "100%", height: 220, borderRadius: radius.md },
  placeholder: { height: 160, borderRadius: radius.md, borderWidth: 2, borderStyle: "dashed", alignItems: "center", justifyContent: "center" },
  botonesFoto: { flexDirection: "row", gap: spacing.md, marginTop: spacing.md },
  motivos: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  motivoChip: { paddingVertical: spacing.sm, paddingHorizontal: spacing.md, borderRadius: radius.md, borderWidth: 1 },
  area: { minHeight: 80, borderWidth: 1, borderRadius: radius.md, padding: spacing.md, marginTop: spacing.md, fontSize: fontSize.body, textAlignVertical: "top" },
});
