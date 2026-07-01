// Pantalla de ayuda: muestra contacto de coordinación para llamar o escribir por WhatsApp.
import { Linking, ScrollView, StyleSheet, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Screen } from "@/components/Screen";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { Cabecera } from "@/components/Cabecera";
import { Aparecer } from "@/components/Animations";
import { Texto } from "@/components/Texto";
import { useTheme, spacing, radius } from "@/theme";

const TELEFONO_COORDINACION = process.env.EXPO_PUBLIC_COORDINACION_TEL ?? "+51999888777";

export default function AyudaScreen() {
  const { colors } = useTheme();
  const llamar = () => Linking.openURL(`tel:${TELEFONO_COORDINACION.replace(/\s/g, "")}`);
  const whatsapp = () => Linking.openURL(`https://wa.me/${TELEFONO_COORDINACION.replace(/[^\d]/g, "")}`);

  return (
    <Screen conPadding={false}>
      <Cabecera titulo="Ayuda" atras />
      <ScrollView contentContainerStyle={estilos.cuerpo}>
        <Aparecer>
          <Card>
            <View style={[estilos.icono, { backgroundColor: colors.brandSoft }]}>
              <Ionicons name="help-buoy-outline" size={28} color={colors.brand} />
            </View>
            <Texto variante="subtitle" color={colors.ink} style={{ marginTop: spacing.md }}>¿Necesitas ayuda?</Texto>
            <Texto variante="body" color={colors.muted} style={{ marginTop: spacing.xs }}>
              Si tienes un problema con tu ruta, un pedido o la app, comunícate con coordinación. Te ayudaremos lo antes posible.
            </Texto>
          </Card>
        </Aparecer>

        <Aparecer delay={60}>
          <View style={estilos.botones}>
            <View style={{ flex: 1 }}><Button titulo="Llamar" variante="secondary" onPress={llamar} /></View>
            <View style={{ flex: 1 }}><Button titulo="WhatsApp" variante="secondary" onPress={whatsapp} /></View>
          </View>
        </Aparecer>
      </ScrollView>
    </Screen>
  );
}

const estilos = StyleSheet.create({
  cuerpo: { padding: spacing.lg, gap: spacing.lg },
  icono: { width: 56, height: 56, borderRadius: radius.lg, alignItems: "center", justifyContent: "center" },
  botones: { flexDirection: "row", gap: spacing.sm },
});
