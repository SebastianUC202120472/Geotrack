// Pantalla de recepción condicionada: el conductor ingresa cantidad y fotos de evidencia
// (solo con la cámara y con GPS, C13-01) o marca que el recojo no se pudo hacer (C12-02).
import { useState } from "react";
import { Alert, Pressable, ScrollView, StyleSheet, TextInput, View } from "react-native";
import { Image } from "expo-image";
import { Ionicons } from "@expo/vector-icons";
import { useLocalSearchParams, useRouter } from "expo-router";
import { Screen } from "@/components/Screen";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { Cabecera } from "@/components/Cabecera";
import { Cargando, Vacio } from "@/components/Estados";
import { Aparecer } from "@/components/Animations";
import { Texto } from "@/components/Texto";
import { SelectorMotivo, OTRO_MOTIVO } from "@/components/SelectorMotivo";
import { abrirNavegacion } from "@/services/navegacion";
import { useRutaActiva } from "@/features/ruta/hooks";
import { useManifiestoRecojo, useRegistrarRecepcion, useMarcarNoRealizado } from "@/features/recojo/hooks";
import { useFotoConGps, type FotoConGps } from "@/hooks/useFotoConGps";
import { mensajeDeError } from "@/api/client";
import { urlMedia } from "@/api/config";
import { useTheme, fontSize, radius, spacing } from "@/theme";
import type { ParadaRecojo } from "@/types/api";

// Motivos frecuentes por los que un recojo no se concreta.
const MOTIVOS_NO_REALIZADO = ["Tienda cerrada", "Mercadería no estaba lista", "No había quién entregue", "Dirección incorrecta", OTRO_MOTIVO];

export default function RecepcionScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const recojoId = Number(id);
  const router = useRouter();
  const { colors } = useTheme();
  const ruta = useRutaActiva();
  const manifiesto = useManifiestoRecojo();
  const registrar = useRegistrarRecepcion();
  const noRealizado = useMarcarNoRealizado();
  const camara = useFotoConGps();

  const [fotos, setFotos] = useState<FotoConGps[]>([]);
  const [cantidad, setCantidad] = useState("");
  const [reportando, setReportando] = useState(false);
  const [motivo, setMotivo] = useState(MOTIVOS_NO_REALIZADO[0]);
  const [detalleMotivo, setDetalleMotivo] = useState("");

  const recojo = manifiesto.data?.paradas.find((p: ParadaRecojo) => p.recojo_id === recojoId);

  const quitarFoto = (uri: string) => setFotos((prev) => prev.filter((f) => f.uri !== uri));

  // Abre la cámara y agrega la foto con la ubicación donde se tomó.
  const tomarFoto = async () => {
    const foto = await camara.tomar();
    if (foto) setFotos((prev) => [...prev, foto]);
    else if (camara.error) Alert.alert("Cámara", camara.error);
  };

  // Valida cantidad y fotos antes de enviar la recepción al backend (con el GPS de la última foto ubicada).
  const confirmar = () => {
    const n = Number(cantidad);
    if (!Number.isInteger(n) || n <= 0) { Alert.alert("Cantidad", "Ingresa la cantidad declarada (entero mayor que 0)."); return; }
    if (fotos.length === 0) { Alert.alert("Evidencia", "Toma al menos una foto (boleta, guía o bultos)."); return; }
    const coords = [...fotos].reverse().find((f) => f.coords)?.coords ?? null;
    registrar.mutate({ recojoId, cantidad: n, uris: fotos.map((f) => f.uri), coords }, {
      onSuccess: () => { Alert.alert("Recepción registrada", "Lote recibido a bulto cerrado."); router.back(); },
      onError: (e) => Alert.alert("Error", mensajeDeError(e)),
    });
  };

  // Marca el recojo como no realizado tras confirmarlo (C12-02).
  const confirmarNoRealizado = () => {
    const texto = motivo === OTRO_MOTIVO ? detalleMotivo.trim() : motivo;
    if (texto.length < 3) { Alert.alert("Motivo", "Cuéntanos brevemente qué pasó."); return; }
    Alert.alert("¿No se pudo recoger?", `Se registrará: «${texto}». Al cerrar tu ruta, la solicitud volverá a la lista para reprogramarla.`, [
      { text: "Cancelar", style: "cancel" },
      {
        text: "Confirmar", style: "destructive", onPress: () => noRealizado.mutate({ recojoId, motivo: texto }, {
          onSuccess: (r) => { Alert.alert("Registrado", r.mensaje); router.back(); },
          onError: (e) => Alert.alert("Error", mensajeDeError(e)),
        }),
      },
    ]);
  };

  const puedeRegistrar = fotos.length > 0 && Number(cantidad) > 0;
  const conGps = fotos.filter((f) => f.coords).length;

  if (manifiesto.isLoading) return <Screen conPadding={false}><Cabecera titulo="Recepción" atras /><Cargando /></Screen>;
  if (!recojo) return <Screen conPadding={false}><Cabecera titulo="Recepción" atras /><Vacio titulo="Recojo no encontrado" /></Screen>;

  const registrado = recojo.estado === "RECOGIDO" || recojo.estado === "INGRESADO";
  const sinExito = recojo.estado === "NO_REALIZADO";
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
            {!!recojo.contacto_origen && <Dato etiqueta="Contacto en origen" valor={recojo.contacto_origen} c={colors} />}
            <Dato etiqueta="Pedidos a recoger" valor={String(recojo.num_pedidos ?? "—")} c={colors} />
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
                <Image source={{ uri: urlMedia(recojo.url_guia) }} style={estilos.guiaGuardada} contentFit="cover" transition={200} />
              )}
            </Card>
          ) : pausada ? (
            <Card style={{ backgroundColor: colors.dangerSoft }}>
              <Texto variante="bodyMedium" color={colors.danger} style={{ textAlign: "center" }}>
                🛠️ Ruta pausada por avería. Reanúdala desde Mi Ruta para continuar.
              </Texto>
            </Card>
          ) : (
            <>
              {sinExito && (
                <Card style={{ backgroundColor: colors.warningSoft }}>
                  <Texto variante="bodyMedium" color={colors.warning}>Marcado como no realizado</Texto>
                  <Texto variante="caption" color={colors.warning} style={{ marginTop: 2 }}>
                    {recojo.motivo_no_realizado || "Sin motivo"}. Si el cliente ya puede entregar, registra la recepción abajo.
                  </Texto>
                </Card>
              )}
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
                  <Texto variante="caption" color={colors.muted}>Fotos de evidencia (boleta, guía o bultos)</Texto>
                  {fotos.length > 0 && (
                    <Texto variante="caption" color={colors.brand}>{fotos.length} foto(s) · {conGps} con GPS</Texto>
                  )}
                </View>
                {fotos.length > 0 ? (
                  <View style={estilos.galeria}>
                    {fotos.map((f) => (
                      <View key={f.uri} style={estilos.miniatura}>
                        <Image source={{ uri: f.uri }} style={estilos.miniaturaImg} contentFit="cover" />
                        <View style={[estilos.gps, { backgroundColor: f.coords ? colors.success : colors.muted }]}>
                          <Ionicons name={f.coords ? "location" : "location-outline"} size={11} color={colors.white} />
                        </View>
                        <Pressable
                          onPress={() => quitarFoto(f.uri)}
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
                    <Ionicons name="camera-outline" size={28} color={colors.muted} />
                    <Texto variante="body" color={colors.muted} style={{ marginTop: spacing.xs, textAlign: "center" }}>
                      Fotografía la boleta/guía firmada y los bultos en el punto de recojo
                    </Texto>
                  </View>
                )}
                <View style={{ marginTop: spacing.md }}>
                  <Button titulo={camara.tomando ? "Leyendo GPS…" : "Tomar foto"} variante="secondary" onPress={tomarFoto} cargando={camara.tomando} />
                </View>
                <Texto variante="caption" color={colors.muted} style={{ marginTop: spacing.xs, textAlign: "center" }}>
                  Las fotos se toman con la cámara y guardan la ubicación.
                </Texto>
                <View style={{ marginTop: spacing.lg }}>
                  <Button
                    titulo={registrar.isPending ? "Registrando…" : "Registrar recepción"}
                    onPress={confirmar}
                    cargando={registrar.isPending}
                    deshabilitado={!puedeRegistrar}
                  />
                </View>
              </Card>

              {!sinExito && (
                <Card>
                  {reportando ? (
                    <>
                      <Texto variante="subtitle" color={colors.ink} style={{ marginBottom: spacing.sm }}>¿Por qué no se pudo recoger?</Texto>
                      <SelectorMotivo
                        motivos={MOTIVOS_NO_REALIZADO}
                        valor={motivo}
                        onCambiar={setMotivo}
                        detalle={detalleMotivo}
                        onDetalle={setDetalleMotivo}
                      />
                      <View style={estilos.botonesFila}>
                        <View style={{ flex: 1 }}><Button titulo="Cancelar" variante="secondary" onPress={() => setReportando(false)} /></View>
                        <View style={{ flex: 1 }}><Button titulo="Confirmar" variante="danger" onPress={confirmarNoRealizado} cargando={noRealizado.isPending} /></View>
                      </View>
                    </>
                  ) : (
                    <Button titulo="No se pudo recoger" variante="danger" onPress={() => setReportando(true)} />
                  )}
                </Card>
              )}
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
  gps: { position: "absolute", left: 4, bottom: 4, width: 20, height: 20, borderRadius: 10, alignItems: "center", justifyContent: "center" },
  quitar: { position: "absolute", top: -6, right: -6, width: 24, height: 24, borderRadius: 12, alignItems: "center", justifyContent: "center" },
  botonesFila: { flexDirection: "row", gap: spacing.md, marginTop: spacing.md },
});
