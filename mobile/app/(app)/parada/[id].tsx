// Detalle de una parada y registro de la entrega: muestra los datos del pedido
// y permite marcar ENTREGADO adjuntando una foto (POD) desde cámara o galería.
import { useState } from "react";
import { Alert, ScrollView, StyleSheet, Text, View } from "react-native";
import { Image } from "expo-image";
import * as ImagePicker from "expo-image-picker";
import { useLocalSearchParams, useRouter } from "expo-router";
import { Screen } from "@/components/Screen";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { EstadoBadge } from "@/components/EstadoBadge";
import { Cargando, Vacio } from "@/components/Estados";
import { useManifiesto } from "@/features/ruta/hooks";
import { useEntregarConEvidencia } from "@/features/entrega/hooks";
import { mensajeDeError } from "@/api/client";
import { colors, fontSize, radius, spacing } from "@/theme";

export default function ParadaScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const pedidoId = Number(id);
  const router = useRouter();
  const manifiesto = useManifiesto();
  const entregar = useEntregarConEvidencia();
  const [foto, setFoto] = useState<string | null>(null);

  const parada = manifiesto.data?.paradas.find((p) => p.pedido_id === pedidoId);

  // Abre la cámara y guarda la foto elegida. Sin parámetros.
  const tomarFoto = async () => {
    const permiso = await ImagePicker.requestCameraPermissionsAsync();
    if (!permiso.granted) {
      Alert.alert("Cámara", "Necesitamos permiso de cámara para la evidencia.");
      return;
    }
    const res = await ImagePicker.launchCameraAsync({ quality: 0.6 });
    if (!res.canceled) setFoto(res.assets[0].uri);
  };

  // Abre la galería y guarda la imagen elegida. Sin parámetros.
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

  if (manifiesto.isLoading) return <Screen><Cargando /></Screen>;
  if (!parada) return <Screen><Vacio titulo="Pedido no encontrado" /></Screen>;

  const yaEntregado = parada.estado_entrega === "ENTREGADO";

  return (
    <Screen conPadding={false}>
      <ScrollView contentContainerStyle={estilos.contenido}>
        <Card>
          <View style={estilos.encabezado}>
            <Text style={estilos.codigo}>{parada.codigo ?? `Pedido ${parada.pedido_id}`}</Text>
            <EstadoBadge estado={parada.estado_entrega} />
          </View>
          <Dato etiqueta="Destinatario" valor={parada.nombre_destinatario || "—"} />
          <Dato etiqueta="Cliente" valor={parada.cliente_origen} />
          <Dato etiqueta="Dirección" valor={parada.direccion_destino} />
          <Dato etiqueta="Distrito" valor={parada.distrito || "—"} />
          {parada.telefono_destinatario ? <Dato etiqueta="Teléfono" valor={parada.telefono_destinatario} /> : null}
        </Card>

        {yaEntregado ? (
          <Card style={estilos.entregado}>
            <Text style={estilos.entregadoTexto}>Esta parada ya fue entregada.</Text>
          </Card>
        ) : (
          <Card>
            <Text style={estilos.tituloSeccion}>Evidencia de entrega (foto)</Text>
            {foto ? (
              <Image source={{ uri: foto }} style={estilos.preview} contentFit="cover" />
            ) : (
              <View style={estilos.placeholder}>
                <Text style={estilos.placeholderTexto}>Adjunta una foto como prueba de entrega</Text>
              </View>
            )}
            <View style={estilos.botonesFoto}>
              <View style={estilos.botonFlex}>
                <Button titulo="Tomar foto" variante="secondary" onPress={tomarFoto} />
              </View>
              <View style={estilos.botonFlex}>
                <Button titulo="Galería" variante="secondary" onPress={elegirFoto} />
              </View>
            </View>

            <View style={estilos.confirmar}>
              <Button
                titulo={entregar.isPending ? "Registrando entrega…" : "Marcar como entregado"}
                onPress={confirmarEntrega}
                cargando={entregar.isPending}
                deshabilitado={!foto}
              />
            </View>
          </Card>
        )}
      </ScrollView>
    </Screen>
  );
}

// Fila etiqueta/valor del detalle. Recibe: { etiqueta, valor }.
function Dato({ etiqueta, valor }: { etiqueta: string; valor: string }) {
  return (
    <View style={estilos.dato}>
      <Text style={estilos.datoEtiqueta}>{etiqueta}</Text>
      <Text style={estilos.datoValor}>{valor}</Text>
    </View>
  );
}

const estilos = StyleSheet.create({
  contenido: { padding: spacing.lg, gap: spacing.lg },
  encabezado: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: spacing.md },
  codigo: { fontSize: fontSize.title, fontWeight: "800", color: colors.ink },
  dato: { marginTop: spacing.md },
  datoEtiqueta: { fontSize: fontSize.caption, color: colors.muted },
  datoValor: { fontSize: fontSize.body, color: colors.text, fontWeight: "600" },
  tituloSeccion: { fontSize: fontSize.subtitle, fontWeight: "700", color: colors.ink, marginBottom: spacing.md },
  preview: { width: "100%", height: 220, borderRadius: radius.md },
  placeholder: {
    height: 160,
    borderRadius: radius.md,
    borderWidth: 2,
    borderColor: colors.border,
    borderStyle: "dashed",
    alignItems: "center",
    justifyContent: "center",
  },
  placeholderTexto: { color: colors.muted, fontSize: fontSize.body },
  botonesFoto: { flexDirection: "row", gap: spacing.md, marginTop: spacing.md },
  botonFlex: { flex: 1 },
  confirmar: { marginTop: spacing.lg },
  entregado: { backgroundColor: colors.successSoft, borderColor: colors.success },
  entregadoTexto: { color: colors.success, fontSize: fontSize.subtitle, fontWeight: "700", textAlign: "center" },
});
