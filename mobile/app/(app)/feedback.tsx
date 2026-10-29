// Pantalla para reportar un error: envia el mensaje a coordinacion por WhatsApp.
import { useState } from "react";
import { Linking, ScrollView, StyleSheet, TextInput, View } from "react-native";
import { Screen } from "@/components/Screen";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { Cabecera } from "@/components/Cabecera";
import { Aparecer } from "@/components/Animations";
import { Texto } from "@/components/Texto";
import { useTelefonoCoordinacion } from "@/hooks/useTelefonoCoordinacion";
import { useTheme, spacing, radius, fuentes } from "@/theme";

export default function FeedbackScreen() {
  const { colors } = useTheme();
  const { telefono } = useTelefonoCoordinacion();
  const [texto, setTexto] = useState("");

  // Abre WhatsApp de coordinación con el reporte escrito.
  const enviar = () => {
    if (!telefono) return;
    const msg = encodeURIComponent(`Reporte de error en GeoTrack:\n${texto.trim()}`);
    Linking.openURL(`https://wa.me/${telefono.replace(/[^\d]/g, "")}?text=${msg}`);
  };

  return (
    <Screen conPadding={false}>
      <Cabecera titulo="Reportar un error" atras />
      <ScrollView contentContainerStyle={estilos.cuerpo}>
        <Aparecer>
          <Card>
            <Texto variante="subtitle" color={colors.ink}>Cuéntanos qué pasó</Texto>
            <Texto variante="caption" color={colors.muted} style={{ marginTop: 2 }}>
              Describe el problema o la sugerencia. Se enviará a coordinación por WhatsApp.
            </Texto>
            <TextInput
              value={texto}
              onChangeText={setTexto}
              multiline
              placeholder="Ej. La app se cierra al abrir el mapa…"
              placeholderTextColor={colors.muted}
              style={[estilos.area, { borderColor: colors.border, color: colors.ink, backgroundColor: colors.canvas }]}
            />
            <View style={{ marginTop: spacing.md }}>
              <Button titulo="Enviar por WhatsApp" onPress={enviar} deshabilitado={!telefono || texto.trim().length === 0} />
            </View>
            {!telefono && (
              <Texto variante="caption" color={colors.muted} style={{ marginTop: spacing.sm }}>
                Coordinación aún no registró su teléfono. Pide al administrador que lo configure en el panel.
              </Texto>
            )}
          </Card>
        </Aparecer>
      </ScrollView>
    </Screen>
  );
}

const estilos = StyleSheet.create({
  cuerpo: { padding: spacing.lg },
  area: { minHeight: 120, borderWidth: 1, borderRadius: radius.md, padding: spacing.md, marginTop: spacing.md, fontFamily: fuentes.regular, fontSize: 16, textAlignVertical: "top" },
});
