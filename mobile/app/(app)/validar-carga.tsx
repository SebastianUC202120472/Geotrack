// CUS-22: validación de carga por QR. El conductor escanea cada caja al subirla y la
// app le avisa si el paquete NO pertenece a su ruta de hoy. Lleva una lista local de
// los validados (no se persiste: es una ayuda de carga).
import { useRef, useState } from "react";
import { StyleSheet, View } from "react-native";
import { CameraView, useCameraPermissions } from "expo-camera";
import { Ionicons } from "@expo/vector-icons";
import { Screen } from "@/components/Screen";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { Cabecera } from "@/components/Cabecera";
import { Texto } from "@/components/Texto";
import { useRutaActiva } from "@/features/ruta/hooks";
import { validarCarga } from "@/api/conductor";
import { mensajeDeError } from "@/api/client";
import { useTheme, radius, spacing } from "@/theme";

export default function ValidarCargaScreen() {
  const { colors } = useTheme();
  const ruta = useRutaActiva();
  const [permiso, pedirPermiso] = useCameraPermissions();

  const [validados, setValidados] = useState<string[]>([]);
  const [resultado, setResultado] = useState<{ ok: boolean; texto: string } | null>(null);
  // Candado para no procesar el mismo código muchas veces seguidas (la cámara dispara
  // el evento de forma continua mientras ve el QR).
  const procesando = useRef(false);

  const total = ruta.data?.total_paradas ?? 0;

  // Al leer un código: valida contra la ruta activa y muestra el resultado.
  const alEscanear = async (codigo: string) => {
    if (procesando.current) return;
    if (validados.includes(codigo)) {
      setResultado({ ok: true, texto: `${codigo} ya estaba validado.` });
      return;
    }
    procesando.current = true;
    try {
      const r = await validarCarga(codigo);
      setResultado({ ok: r.pertenece, texto: r.mensaje });
      if (r.pertenece) setValidados((v) => [...v, codigo]);
    } catch (e) {
      setResultado({ ok: false, texto: mensajeDeError(e) });
    } finally {
      // Pequeña pausa antes de aceptar el siguiente escaneo (evita repeticiones).
      setTimeout(() => { procesando.current = false; }, 1200);
    }
  };

  // Sin permiso de cámara todavía: lo pedimos.
  if (!permiso) {
    return <Screen conPadding={false}><Cabecera titulo="Validar carga" atras /></Screen>;
  }
  if (!permiso.granted) {
    return (
      <Screen conPadding={false}>
        <Cabecera titulo="Validar carga" atras />
        <View style={estilos.centro}>
          <Ionicons name="camera-outline" size={48} color={colors.muted} />
          <Texto variante="body" color={colors.muted} style={{ textAlign: "center", marginVertical: spacing.md }}>
            Necesitamos la cámara para escanear los códigos QR de las cajas.
          </Texto>
          <Button titulo="Permitir cámara" onPress={pedirPermiso} />
        </View>
      </Screen>
    );
  }

  return (
    <Screen conPadding={false}>
      <Cabecera titulo="Validar carga" atras />
      <View style={estilos.contenido}>
        <View style={[estilos.camara, { borderColor: colors.border }]}>
          <CameraView
            style={StyleSheet.absoluteFill}
            facing="back"
            barcodeScannerSettings={{ barcodeTypes: ["qr", "code128", "code39", "ean13", "ean8"] }}
            onBarcodeScanned={({ data }) => alEscanear(data)}
          />
        </View>

        {resultado && (
          <Card style={{ backgroundColor: resultado.ok ? colors.successSoft : colors.dangerSoft, marginTop: spacing.md }}>
            <View style={estilos.fila}>
              <Ionicons name={resultado.ok ? "checkmark-circle" : "close-circle"} size={22}
                color={resultado.ok ? colors.success : colors.danger} />
              <Texto variante="bodyMedium" color={resultado.ok ? colors.success : colors.danger} style={{ flex: 1 }}>
                {resultado.texto}
              </Texto>
            </View>
          </Card>
        )}

        <Card style={{ marginTop: spacing.md }}>
          <Texto variante="subtitle" color={colors.ink}>Validados: {validados.length}{total ? ` de ${total}` : ""}</Texto>
          <Texto variante="caption" color={colors.muted} style={{ marginTop: 2 }}>
            Apunta la cámara al QR de cada caja. Si no pertenece a tu ruta, te avisamos.
          </Texto>
        </Card>
      </View>
    </Screen>
  );
}

const estilos = StyleSheet.create({
  contenido: { flex: 1, padding: spacing.lg },
  camara: { height: 320, borderRadius: radius.lg, overflow: "hidden", borderWidth: 1 },
  fila: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  centro: { flex: 1, alignItems: "center", justifyContent: "center", padding: spacing.xl },
});
