// Pantalla de detalle de parada: permite marcar entregado (foto con GPS + quién recibe) o reportar falla.
import { useState } from "react";
import { Alert, Linking, Pressable, ScrollView, StyleSheet, Switch, TextInput, View } from "react-native";
import { Image } from "expo-image";
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
import { Field } from "@/components/Field";
import { useFotoConGps, type FotoConGps } from "@/hooks/useFotoConGps";
import { abrirNavegacion } from "@/services/navegacion";
import { useRutaActiva, useManifiesto } from "@/features/ruta/hooks";
import { useEntregarConEvidencia, useReportarFalla } from "@/features/entrega/hooks";
import { usePendientesPorPedido } from "@/features/sync/hooks";
import { obtenerMotivos } from "@/api/conductor";
import { mensajeDeError } from "@/api/client";
import { urlMedia } from "@/api/config";
import { BannerSync } from "@/components/BannerSync";
import { useTheme, fontSize, radius, spacing } from "@/theme";
import type { ParadaManifiesto } from "@/types/api";

// Motivos de falla por defecto si el backend no los devuelve.
const MOTIVOS_DEFECTO = ["Cliente ausente", "Dirección incorrecta", "Pedido rechazado", "Zona inaccesible", "Otro"];

// DNI (8 dígitos) o carné de extranjería: de 8 a 12 letras o números, igual que valida el servidor.
const DOCUMENTO_VALIDO = /^[A-Za-z0-9]{8,12}$/;

export default function ParadaScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const pedidoId = Number(id);
  const router = useRouter();
  const { colors } = useTheme();
  const ruta = useRutaActiva();
  const manifiesto = useManifiesto();
  const entregar = useEntregarConEvidencia();
  const reportar = useReportarFalla();
  const pendientesPorPedido = usePendientesPorPedido();

  const motivosQuery = useQuery({ queryKey: ["motivos"], queryFn: obtenerMotivos, staleTime: 60_000 });
  const motivos = motivosQuery.data && motivosQuery.data.length ? motivosQuery.data : MOTIVOS_DEFECTO;

  const camara = useFotoConGps();
  const [foto, setFoto] = useState<FotoConGps | null>(null);
  const [fotoFalla, setFotoFalla] = useState<FotoConGps | null>(null);
  const [esDestinatario, setEsDestinatario] = useState(true);
  const [receptorNombre, setReceptorNombre] = useState("");
  const [receptorDoc, setReceptorDoc] = useState("");
  const [modoReporte, setModoReporte] = useState(false);
  const [motivo, setMotivo] = useState(MOTIVOS_DEFECTO[0]);
  const [descripcion, setDescripcion] = useState("");
  const [exito, setExito] = useState(false);

  const parada = manifiesto.data?.paradas.find((p: ParadaManifiesto) => p.pedido_id === pedidoId);

  // Nombre de quien recibe: el del destinatario si él mismo lo recibe, o el que se escribió.
  const nombreFinal = (esDestinatario ? parada?.nombre_destinatario ?? "" : receptorNombre).trim();
  const documentoFinal = receptorDoc.trim().toUpperCase();
  const receptorValido = nombreFinal.length >= 3 && DOCUMENTO_VALIDO.test(documentoFinal);

  // Abre la cámara (sin galería: la evidencia se toma en el lugar) y guarda la foto con su GPS (C26-01).
  // Recibe la función que guarda la foto (entrega o falla).
  const tomarFoto = async (guardar: (f: FotoConGps) => void) => {
    const resultado = await camara.tomar();
    if (resultado) guardar(resultado);
  };

  // Envía la foto y quién recibe al backend y marca la parada como ENTREGADO. No recibe parámetros.
  const confirmarEntrega = () => {
    if (!foto || !receptorValido) return;
    entregar.mutate(
      { pedidoId, foto, receptor: { nombre: nombreFinal, documento: documentoFinal } },
      {
        onSuccess: (res) => {
          if (res?.encolado) {
            Alert.alert("Guardado sin conexión", "La entrega se subirá automáticamente al recuperar internet.");
            router.back();
          } else {
            setExito(true);
            setTimeout(() => router.back(), 900);
          }
        },
        onError: (e) => Alert.alert("Error", mensajeDeError(e)),
      }
    );
  };

  // Envía el reporte de falla al backend y marca la parada como FALLIDO. No recibe parámetros.
  const enviarReporte = () => {
    reportar.mutate(
      { pedidoId, motivo, descripcion: descripcion.trim() || undefined, foto: fotoFalla },
      {
        onSuccess: (res) => {
          Alert.alert(
            res?.encolado ? "Guardado sin conexión" : "Reporte enviado",
            res?.encolado ? "El reporte se enviará al recuperar internet." : "El administrador lo verá en sus reportes."
          );
          router.back();
        },
        onError: (e) => Alert.alert("Error", mensajeDeError(e)),
      }
    );
  };

  if (manifiesto.isLoading) return <Screen conPadding={false}><Cabecera titulo="Entrega" atras /><Cargando /></Screen>;
  if (!parada) return <Screen conPadding={false}><Cabecera titulo="Entrega" atras /><Vacio titulo="Pedido no encontrado" /></Screen>;

  const gestionada = parada.estado_entrega !== "PENDIENTE";
  // Bloquea el formulario si hay una acción offline pendiente de subir (evita duplicados).
  const enCola = !gestionada && pendientesPorPedido.has(parada.pedido_id);
  const pausada = !!ruta.data?.pausada;

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
          <BannerSync />
          <Card>
            <View style={estilos.encabezado}>
              <Texto variante="label" color={colors.muted} style={estilos.codigo}>{parada.codigo ?? `Pedido ${parada.pedido_id}`}</Texto>
              <EstadoBadge estado={parada.estado_entrega} />
            </View>

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
              {parada.estado_entrega === "ENTREGADO" && urlMedia(parada.url_evidencia) && (
                <Image
                  source={{ uri: urlMedia(parada.url_evidencia) }}
                  style={estilos.evidenciaGuardada}
                  contentFit="cover"
                  transition={200}
                />
              )}
            </Card>
          ) : enCola ? (
            <Card style={{ backgroundColor: colors.brandSoft }}>
              <Texto variante="subtitle" color={colors.brand} style={{ textAlign: "center" }}>
                {pendientesPorPedido.get(parada.pedido_id) === "FALLIDO"
                  ? "Falla guardada sin conexión."
                  : "Entrega guardada sin conexión."}
              </Texto>
              <Texto variante="caption" color={colors.brand} style={{ textAlign: "center", marginTop: spacing.xs }}>
                Se subirá automáticamente al recuperar internet.
              </Texto>
            </Card>
          ) : pausada ? (
            <Card style={{ backgroundColor: colors.dangerSoft }}>
              <Texto variante="bodyMedium" color={colors.danger} style={{ textAlign: "center" }}>
                🛠️ Ruta pausada por avería. Reanúdala desde Mi Ruta para continuar.
              </Texto>
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
              {fotoFalla && <Image source={{ uri: fotoFalla.uri }} style={estilos.fotoFalla} contentFit="cover" />}
              <View style={{ marginTop: spacing.md }}>
                <Button
                  titulo={camara.tomando ? "Leyendo GPS…" : fotoFalla ? "Cambiar foto" : "Tomar foto (opcional)"}
                  variante="secondary"
                  onPress={() => tomarFoto(setFotoFalla)}
                  cargando={camara.tomando}
                />
              </View>
              <Texto variante="caption" color={colors.muted} style={{ marginTop: spacing.xs }}>
                Ej. la puerta cerrada o la numeración de la calle: respalda el reporte.
              </Texto>
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
                  <Image source={{ uri: foto.uri }} style={estilos.preview} contentFit="cover" />
                ) : (
                  <View style={[estilos.placeholder, { borderColor: colors.border }]}>
                    <Ionicons name="camera-outline" size={28} color={colors.muted} />
                    <Texto variante="body" color={colors.muted} style={{ marginTop: spacing.xs }}>Toma una foto del paquete entregado</Texto>
                  </View>
                )}
                {foto && (
                  <Texto variante="caption" color={foto.coords ? colors.success : colors.warning} style={{ marginTop: spacing.xs }}>
                    {foto.coords ? "📍 Ubicación de la foto registrada" : "⚠️ Sin GPS: la foto se guardará sin ubicación"}
                  </Texto>
                )}
                <View style={estilos.botonesFoto}>
                  <View style={{ flex: 1 }}>
                    <Button
                      titulo={camara.tomando ? "Leyendo GPS…" : foto ? "Repetir foto" : "Tomar foto"}
                      variante="secondary"
                      onPress={() => tomarFoto(setFoto)}
                      cargando={camara.tomando}
                    />
                  </View>
                </View>
                {camara.error && !camara.tomando && (
                  <Texto variante="caption" color={colors.danger} style={{ marginTop: spacing.xs }}>{camara.error}</Texto>
                )}
              </Card>

              <Card>
                <Texto variante="subtitle" color={colors.ink} style={estilos.titulo}>¿Quién recibe?</Texto>
                {parada.nombre_destinatario ? (
                  <View style={estilos.toggle}>
                    <View style={{ flex: 1 }}>
                      <Texto variante="bodyMedium" color={colors.ink}>Lo recibe el destinatario</Texto>
                      <Texto variante="caption" color={colors.muted} style={{ marginTop: 2 }}>
                        {esDestinatario ? parada.nombre_destinatario : "Otra persona (familiar, portería…)"}
                      </Texto>
                    </View>
                    <Switch
                      value={esDestinatario}
                      onValueChange={setEsDestinatario}
                      trackColor={{ false: colors.border, true: colors.brandSoft }}
                      thumbColor={esDestinatario ? colors.brand : colors.surface}
                      ios_backgroundColor={colors.border}
                    />
                  </View>
                ) : null}
                {(!esDestinatario || !parada.nombre_destinatario) && (
                  <Field
                    label="Nombre de quien recibe"
                    value={receptorNombre}
                    onChangeText={setReceptorNombre}
                    placeholder="Nombres y apellidos"
                    autoCapitalize="words"
                    maxLength={120}
                  />
                )}
                <Field
                  label="DNI o carné de extranjería"
                  value={receptorDoc}
                  onChangeText={(t) => setReceptorDoc(t.replace(/[^A-Za-z0-9]/g, ""))}
                  placeholder="Ej. 45678912"
                  autoCapitalize="characters"
                  maxLength={12}
                />
                <View style={{ marginTop: spacing.lg }}>
                  <Button
                    titulo={entregar.isPending ? "Registrando…" : "Marcar como entregado"}
                    onPress={confirmarEntrega}
                    cargando={entregar.isPending}
                    deshabilitado={!foto || !receptorValido || camara.tomando}
                  />
                </View>
                {foto && !receptorValido && (
                  <Texto variante="caption" color={colors.muted} style={{ marginTop: spacing.xs, textAlign: "center" }}>
                    Completa el nombre y el documento de quien recibe.
                  </Texto>
                )}
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
  fotoFalla: { width: "100%", height: 160, borderRadius: radius.md, marginTop: spacing.md },
  toggle: { flexDirection: "row", alignItems: "center", gap: spacing.md, marginBottom: spacing.sm },
  botonesFoto: { flexDirection: "row", gap: spacing.md, marginTop: spacing.md },
  motivos: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  motivoChip: { paddingVertical: spacing.sm, paddingHorizontal: spacing.md, borderRadius: radius.md, borderWidth: 1 },
  area: { minHeight: 80, borderWidth: 1, borderRadius: radius.md, padding: spacing.md, marginTop: spacing.md, fontSize: fontSize.body, textAlignVertical: "top" },
});
