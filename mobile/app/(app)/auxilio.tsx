// CUS-30: el conductor reporta un auxilio mecánico (avería). Al enviarlo, su ruta queda
// pausada (no puede gestionar paradas ni cerrar el día) hasta que la reanude.
import { useState } from "react";
import { Alert, Image, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import * as ImagePicker from "expo-image-picker";
import { Ionicons } from "@expo/vector-icons";
import { Screen } from "@/components/Screen";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { Field } from "@/components/Field";
import { Cabecera } from "@/components/Cabecera";
import { Texto } from "@/components/Texto";
import { useReportarAuxilio } from "@/features/incidencia/hooks";
import { useUbicacionActual } from "@/hooks/useUbicacionActual";
import { mensajeDeError } from "@/api/client";
import { useTheme, radius, spacing } from "@/theme";

export default function AuxilioScreen() {
  const router = useRouter();
  const { colors } = useTheme();
  const reportar = useReportarAuxilio();
  const ubicacion = useUbicacionActual();
  const [descripcion, setDescripcion] = useState("");
  const [foto, setFoto] = useState<string | null>(null);

  // Toma una foto de la avería con la cámara (opcional).
  const tomarFoto = async () => {
    const permiso = await ImagePicker.requestCameraPermissionsAsync();
    if (!permiso.granted) { Alert.alert("Cámara", "Necesitamos permiso de cámara para la foto."); return; }
    const r = await ImagePicker.launchCameraAsync({ quality: 0.6 });
    if (!r.canceled && r.assets?.[0]?.uri) setFoto(r.assets[0].uri);
  };

  // Envía el auxilio: adjunta coords (best-effort) y foto (si hay), y vuelve a Mi Ruta.
  const enviar = async () => {
    const coords = (await ubicacion.obtener()) ?? undefined;
    reportar.mutate(
      { descripcion: descripcion.trim() || undefined, coords, uriFoto: foto ?? undefined },
      {
        onSuccess: () => {
          Alert.alert("Auxilio enviado", "Tu ruta quedó pausada y se avisó al almacén.");
          router.back();
        },
        onError: (e) => Alert.alert("No se pudo enviar", mensajeDeError(e)),
      }
    );
  };

  return (
    <Screen conPadding={false}>
      <Cabecera titulo="Auxilio mecánico" atras />
      <View style={estilos.contenido}>
        <Card style={{ backgroundColor: colors.dangerSoft }}>
          <View style={estilos.fila}>
            <Ionicons name="warning" size={22} color={colors.danger} />
            <Texto variante="bodyMedium" color={colors.danger} style={{ flex: 1 }}>
              Reportar una avería pausará tu ruta hasta que la reanudes.
            </Texto>
          </View>
        </Card>

        <Field
          label="¿Qué pasó? (opcional)"
          value={descripcion}
          onChangeText={setDescripcion}
          placeholder="Ej. Llanta pinchada en Av. La Marina"
          multiline
          numberOfLines={3}
          style={{ marginTop: spacing.md }}
        />

        {foto && <Image source={{ uri: foto }} style={estilos.foto} />}
        <Button titulo={foto ? "Cambiar foto" : "Tomar foto (opcional)"} variante="secondary" onPress={tomarFoto} />
        <Button titulo="Enviar auxilio" variante="danger" onPress={enviar} cargando={reportar.isPending || ubicacion.cargando} />
      </View>
    </Screen>
  );
}

const estilos = StyleSheet.create({
  contenido: { flex: 1, padding: spacing.lg, gap: spacing.md },
  fila: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  foto: { width: "100%", height: 180, borderRadius: radius.lg },
});
