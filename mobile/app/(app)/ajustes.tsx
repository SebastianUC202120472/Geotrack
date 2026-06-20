// Ajustes del conductor (pestaña ⚙). Versión base; el detalle (notificaciones,
// reportar errores/feedback, información de la app, estado de cuenta y Ayuda) se
// añade en el siguiente hito.
import { Linking, ScrollView, StyleSheet, View } from "react-native";
import { Screen } from "@/components/Screen";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { Cabecera } from "@/components/Cabecera";
import { DeslizarPestanas } from "@/components/DeslizarPestanas";
import { Aparecer } from "@/components/Animations";
import { Texto } from "@/components/Texto";
import { useAuth } from "@/store/auth";
import { useTheme, spacing } from "@/theme";

// Número de coordinación para llamar/escribir. Cámbialo por el real (o usa env).
const TELEFONO_COORDINACION = process.env.EXPO_PUBLIC_COORDINACION_TEL ?? "+51999888777";

export default function AjustesScreen() {
  const { colors } = useTheme();
  const { cerrarSesion } = useAuth();

  const llamar = () => Linking.openURL(`tel:${TELEFONO_COORDINACION.replace(/\s/g, "")}`);
  const whatsapp = () => Linking.openURL(`https://wa.me/${TELEFONO_COORDINACION.replace(/[^\d]/g, "")}`);

  return (
    <Screen conPadding={false}>
      <Cabecera titulo="Ajustes" />
      <DeslizarPestanas>
        <ScrollView contentContainerStyle={estilos.cuerpo}>
          <Aparecer delay={0}>
            <Card>
              <Texto variante="subtitle" color={colors.ink} style={estilos.titulo}>¿Algún problema?</Texto>
              <Texto variante="caption" color={colors.muted}>Contacta a coordinación.</Texto>
              <View style={[estilos.fila, { marginTop: spacing.md }]}>
                <View style={{ flex: 1 }}><Button titulo="Llamar" variante="secondary" onPress={llamar} /></View>
                <View style={{ flex: 1 }}><Button titulo="WhatsApp" variante="secondary" onPress={whatsapp} /></View>
              </View>
            </Card>
          </Aparecer>

          <Aparecer delay={60}>
            <Button titulo="Cerrar sesión" variante="danger" onPress={cerrarSesion} />
          </Aparecer>
        </ScrollView>
      </DeslizarPestanas>
    </Screen>
  );
}

const estilos = StyleSheet.create({
  cuerpo: { padding: spacing.lg, gap: spacing.lg, paddingBottom: spacing.xl },
  titulo: { marginBottom: spacing.xs },
  fila: { flexDirection: "row", gap: spacing.sm },
});
