// Recepción Condicionada en Origen (CUS-12): el conductor ingresa la cantidad total
// declarada por el cliente y captura una foto de la Guía de Remisión firmada; el lote
// se recibe a bulto cerrado (sin validación unitaria).
import { useState } from "react";
import { Alert, Pressable, ScrollView, StyleSheet, TextInput, View } from "react-native";
import { Image } from "expo-image";
import * as ImagePicker from "expo-image-picker";
import { Ionicons } from "@expo/vector-icons";
import { useLocalSearchParams, useRouter } from "expo-router";
import { Screen } from "@/components/Screen";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { Cabecera } from "@/components/Cabecera";
import { Cargando, Vacio } from "@/components/Estados";
import { Aparecer } from "@/components/Animations";
import { Texto } from "@/components/Texto";
import { abrirNavegacion } from "@/services/navegacion";
import { useRutaActiva } from "@/features/ruta/hooks";
import { useManifiestoRecojo, useRegistrarRecepcion } from "@/features/recojo/hooks";
import { mensajeDeError } from "@/api/client";
import { urlMedia } from "@/api/config";
import { useTheme, fontSize, radius, spacing } from "@/theme";
import type { ParadaRecojo } from "@/types/api";

export default function RecepcionScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const recojoId = Number(id);
  const router = useRouter();
  const { colors } = useTheme();
  const ruta = useRutaActiva();
  const manifiesto = useManifiestoRecojo();
  const registrar = useRegistrarRecepcion();

  const [foto, setFoto] = useState<string | null>(null);
  const [cantidad, setCantidad] = useState("");

  const recojo = manifiesto.data?.paradas.find((p: ParadaRecojo) => p.recojo_id === recojoId);

  // Abre la cámara y guarda la foto de la guía de remisión.
  const tomarFoto = async () => {
    const permiso = await ImagePicker.requestCameraPermissionsAsync();
    if (!permiso.granted) { Alert.alert("Cámara", "Necesitamos permiso de cámara para la guía."); return; }
    const res = await ImagePicker.launchCameraAsync({ quality: 0.6 });
    if (!res.canceled) setFoto(res.assets[0].uri);
  };

  // Abre la galería y guarda la imagen seleccionada.
  const elegirFoto = async () => {
    const res = await ImagePicker.launchImageLibraryAsync({ quality: 0.6 });
    if (!res.canceled) setFoto(res.assets[0].uri);
  };

  // Valida cantidad (entero > 0) y foto, luego envía la recepción al backend.
  const confirmar = () => {
    const n = Number(cantidad);
    if (!Number.isInteger(n) || n <= 0) { Alert.alert("Cantidad", "Ingresa la cantidad declarada (entero mayor que 0)."); return; }
    if (!foto) { Alert.alert("Guía", "Captura la foto de la Guía de Remisión."); return; }
    registrar.mutate({ recojoId, cantidad: n, uriFoto: foto }, {
      onSuccess: () => { Alert.alert("Recepción registrada", "Lote recibido a bulto cerrado."); router.back(); },
      onError: (e) => Alert.alert("Error", mensajeDeError(e)),
    });
  };

  if (manifiesto.isLoading) return <Screen conPadding={false}><Cabecera titulo="Recepción" atras /><Cargando /></Screen>;
  if (!recojo) return <Screen conPadding={false}><Cabecera titulo="Recepción" atras /><Vacio titulo="Recojo no encontrado" /></Screen>;

  const registrado = recojo.estado === "RECOGIDO";
  // CUS-30: la ruta está pausada por avería; no se permiten acciones hasta reanudarla.
  const pausada = !!ruta.data?.pausada;

  return (
    <Screen conPadding={false}>
      <Cabecera titulo="Recepción" atras />
      <ScrollView contentContainerStyle={{ padding: spacing.lg }}>
        <Aparecer style={{ gap: spacing.lg }}>
          {/* Ficha del punto de recojo */}
          <Card>
            <Texto variante="label" color={colors.muted}>{recojo.codigo ?? `Recojo ${recojo.recojo_id}`}</Texto>
            <Texto variante="title" color={colors.ink} style={{ marginTop: 2 }}>{recojo.cliente_origen}</Texto>
            <View style={[estilos.separador, { backgroundColor: colors.border }]} />
            <Dato etiqueta="Origen" valor={recojo.direccion_origen} c={colors} />
            <Dato etiqueta="Distrito" valor={recojo.distrito || "—"} c={colors} />
            <Dato etiqueta="Volumen estimado (m³)" valor={recojo.volumen_estimado_m3 != null ? String(recojo.volumen_estimado_m3) : "—"} c={colors} />
            {recojo.latitud != null && recojo.longitud != null && (
              <Pressable
                onPress={() => abrirNavegacion(recojo.latitud as number, recojo.longitud as number, recojo.direccion_origen)}
                accessibilityRole="button"
                accessibilityLabel="Navegar al punto de recojo"
                style={[estilos.navegar, { backgroundColor: colors.brand }]}
              >
                <Ionicons name="navigate" size={18} color={colors.white} />
                <Texto variante="body" color={colors.white} style={{ marginLeft: spacing.sm }}>Navegar con Google Maps</Texto>
              </Pressable>
            )}
          </Card>

          {registrado ? (
            /* Estado RECOGIDO: muestra la guía guardada desde el backend. */
            <Card style={{ backgroundColor: colors.successSoft }}>
              <Texto variante="subtitle" color={colors.success} style={{ textAlign: "center" }}>Recepción registrada</Texto>
              <Texto variante="body" color={colors.success} style={{ textAlign: "center", marginTop: 2 }}>
                Cantidad declarada: {recojo.cantidad_declarada ?? "—"}
              </Texto>
              {/* CUS-12: la guía se lee del backend (persistida en BD), no de un caché temporal. */}
              {urlMedia(recojo.url_guia) && (
                <Image
                  source={{ uri: urlMedia(recojo.url_guia) }}
                  style={estilos.guiaGuardada}
                  contentFit="cover"
                  transition={200}
                />
              )}
            </Card>
          ) : pausada ? (
            /* CUS-30: ruta pausada — bloquea el registro de recepción. */
            <Card style={{ backgroundColor: colors.dangerSoft }}>
              <Texto variante="bodyMedium" color={colors.danger} style={{ textAlign: "center" }}>
                🛠️ Ruta pausada por avería. Reanúdala desde Mi Ruta para continuar.
              </Texto>
            </Card>
          ) : (
            /* Formulario de recepción condicionada (cantidad + foto de la guía). */
            <Card>
              <Texto variante="subtitle" color={colors.ink} style={{ marginBottom: spacing.md }}>
                Recepción condicionada (a bulto cerrado)
              </Texto>
              <Texto variante="caption" color={colors.muted}>Cantidad total declarada por el cliente</Texto>
              <TextInput
                value={cantidad}
                onChangeText={setCantidad}
                keyboardType="number-pad"
                placeholder="0"
                placeholderTextColor={colors.muted}
                style={[estilos.input, { borderColor: colors.border, color: colors.ink, backgroundColor: colors.surface }]}
              />
              <Texto variante="caption" color={colors.muted} style={{ marginTop: spacing.md }}>
                Foto de la Guía de Remisión firmada
              </Texto>
              {foto ? (
                <Image source={{ uri: foto }} style={estilos.preview} contentFit="cover" />
              ) : (
                <View style={[estilos.placeholder, { borderColor: colors.border }]}>
                  <Texto variante="body" color={colors.muted}>Captura la guía firmada (prueba de custodia)</Texto>
                </View>
              )}
              <View style={estilos.botonesFoto}>
                <View style={{ flex: 1 }}><Button titulo="Tomar foto" variante="secondary" onPress={tomarFoto} /></View>
                <View style={{ flex: 1 }}><Button titulo="Galería" variante="secondary" onPress={elegirFoto} /></View>
              </View>
              <View style={{ marginTop: spacing.lg }}>
                <Button
                  titulo={registrar.isPending ? "Registrando…" : "Registrar recepción"}
                  onPress={confirmar}
                  cargando={registrar.isPending}
                  deshabilitado={!foto || !cantidad}
                />
              </View>
            </Card>
          )}
        </Aparecer>
      </ScrollView>
    </Screen>
  );
}

// Fila etiqueta/valor del detalle. Recibe: { etiqueta, valor, c (paleta) }.
function Dato({ etiqueta, valor, c }: { etiqueta: string; valor: string; c: { muted: string; text: string } }) {
  return (
    <View style={{ marginTop: spacing.md }}>
      <Texto variante="caption" color={c.muted}>{etiqueta}</Texto>
      <Texto variante="bodyMedium" color={c.text}>{valor}</Texto>
    </View>
  );
}

const estilos = StyleSheet.create({
  separador: { height: 1, marginVertical: spacing.md },
  navegar: { flexDirection: "row", alignItems: "center", justifyContent: "center", marginTop: spacing.md, paddingVertical: spacing.md, borderRadius: radius.md },
  input: { borderWidth: 1, borderRadius: radius.md, padding: spacing.md, marginTop: spacing.xs, fontSize: fontSize.title },
  preview: { width: "100%", height: 220, borderRadius: radius.md, marginTop: spacing.xs },
  guiaGuardada: { width: "100%", height: 200, borderRadius: radius.md, marginTop: spacing.md },
  placeholder: { height: 160, borderRadius: radius.md, borderWidth: 2, borderStyle: "dashed", alignItems: "center", justifyContent: "center", marginTop: spacing.xs },
  botonesFoto: { flexDirection: "row", gap: spacing.md, marginTop: spacing.md },
});
