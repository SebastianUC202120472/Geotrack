// Pantalla de recepción condicionada: el conductor ingresa cantidad y fotos de evidencia.
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

  const [fotos, setFotos] = useState<string[]>([]);
  const [cantidad, setCantidad] = useState("");

  const recojo = manifiesto.data?.paradas.find((p: ParadaRecojo) => p.recojo_id === recojoId);

  // Acumula uris sin duplicados.
  const agregarFotos = (uris: string[]) =>
    setFotos((prev) => [...prev, ...uris.filter((u) => !prev.includes(u))]);

  const quitarFoto = (uri: string) => setFotos((prev) => prev.filter((u) => u !== uri));

  // Solicita permiso de cámara y agrega la foto capturada.
  const tomarFoto = async () => {
    const permiso = await ImagePicker.requestCameraPermissionsAsync();
    if (!permiso.granted) { Alert.alert("Cámara", "Necesitamos permiso de cámara para la evidencia."); return; }
    const res = await ImagePicker.launchCameraAsync({ quality: 0.6 });
    if (!res.canceled) agregarFotos(res.assets.map((a) => a.uri));
  };

  const elegirFotos = async () => {
    const res = await ImagePicker.launchImageLibraryAsync({ quality: 0.6, allowsMultipleSelection: true });
    if (!res.canceled) agregarFotos(res.assets.map((a) => a.uri));
  };

  // Valida cantidad y fotos antes de enviar la recepción al backend.
  const confirmar = () => {
    const n = Number(cantidad);
    if (!Number.isInteger(n) || n <= 0) { Alert.alert("Cantidad", "Ingresa la cantidad declarada (entero mayor que 0)."); return; }
    if (fotos.length === 0) { Alert.alert("Evidencia", "Agrega al menos una foto (boleta, guía o bultos)."); return; }
    registrar.mutate({ recojoId, cantidad: n, uris: fotos }, {
      onSuccess: () => { Alert.alert("Recepción registrada", "Lote recibido a bulto cerrado."); router.back(); },
      onError: (e) => Alert.alert("Error", mensajeDeError(e)),
    });
  };

  const puedeRegistrar = fotos.length > 0 && Number(cantidad) > 0;

  if (manifiesto.isLoading) return <Screen conPadding={false}><Cabecera titulo="Recepción" atras /><Cargando /></Screen>;
  if (!recojo) return <Screen conPadding={false}><Cabecera titulo="Recepción" atras /><Vacio titulo="Recojo no encontrado" /></Screen>;

  const registrado = recojo.estado === "RECOGIDO";
  const pausada = !!ruta.data?.pausada;

  return (
    <Screen conPadding={false}>
      <Cabecera titulo="Recepción" atras />
      <ScrollView contentContainerStyle={{ padding: spacing.lg }}>
        <Aparecer style={{ gap: spacing.lg }}>
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
            <Card style={{ backgroundColor: colors.successSoft }}>
              <Texto variante="subtitle" color={colors.success} style={{ textAlign: "center" }}>Recepción registrada</Texto>
              <Texto variante="body" color={colors.success} style={{ textAlign: "center", marginTop: 2 }}>
                Cantidad declarada: {recojo.cantidad_declarada ?? "—"}
              </Texto>
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
            <Card style={{ backgroundColor: colors.dangerSoft }}>
              <Texto variante="bodyMedium" color={colors.danger} style={{ textAlign: "center" }}>
                🛠️ Ruta pausada por avería. Reanúdala desde Mi Ruta para continuar.
              </Texto>
            </Card>
          ) : (
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
              <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginTop: spacing.md }}>
                <Texto variante="caption" color={colors.muted}>
                  Fotos de evidencia (boleta, guía o bultos)
                </Texto>
                {fotos.length > 0 && (
                  <Texto variante="caption" color={colors.brand}>{fotos.length} foto(s)</Texto>
                )}
              </View>
              {fotos.length > 0 ? (
                <View style={estilos.galeria}>
                  {fotos.map((uri) => (
                    <View key={uri} style={estilos.miniatura}>
                      <Image source={{ uri }} style={estilos.miniaturaImg} contentFit="cover" />
                      <Pressable
                        onPress={() => quitarFoto(uri)}
                        accessibilityRole="button"
                        accessibilityLabel="Quitar foto"
                        hitSlop={8}
                        style={[estilos.quitar, { backgroundColor: colors.danger }]}
                      >
                        <Ionicons name="close" size={14} color={colors.white} />
                      </Pressable>
                    </View>
                  ))}
                </View>
              ) : (
                <View style={[estilos.placeholder, { borderColor: colors.border }]}>
                  <Ionicons name="images-outline" size={28} color={colors.muted} />
                  <Texto variante="body" color={colors.muted} style={{ marginTop: spacing.xs, textAlign: "center" }}>
                    Agrega la boleta/guía firmada y los bultos (prueba de custodia)
                  </Texto>
                </View>
              )}
              <View style={estilos.botonesFoto}>
                <View style={{ flex: 1 }}><Button titulo="Tomar foto" variante="secondary" onPress={tomarFoto} /></View>
                <View style={{ flex: 1 }}><Button titulo="Galería" variante="secondary" onPress={elegirFotos} /></View>
              </View>
              <View style={{ marginTop: spacing.lg }}>
                <Button
                  titulo={registrar.isPending ? "Registrando…" : "Registrar recepción"}
                  onPress={confirmar}
                  cargando={registrar.isPending}
                  deshabilitado={!puedeRegistrar}
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
  guiaGuardada: { width: "100%", height: 200, borderRadius: radius.md, marginTop: spacing.md },
  placeholder: { minHeight: 140, borderRadius: radius.md, borderWidth: 2, borderStyle: "dashed", alignItems: "center", justifyContent: "center", marginTop: spacing.xs, padding: spacing.md },
  galeria: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm, marginTop: spacing.xs },
  miniatura: { width: 96, height: 96 },
  miniaturaImg: { width: "100%", height: "100%", borderRadius: radius.md },
  quitar: { position: "absolute", top: -6, right: -6, width: 24, height: 24, borderRadius: 12, alignItems: "center", justifyContent: "center" },
  botonesFoto: { flexDirection: "row", gap: spacing.md, marginTop: spacing.md },
});
