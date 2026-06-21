// Información de la app: nombre, versión y una breve descripción.
import { ScrollView, StyleSheet, View } from "react-native";
import Constants from "expo-constants";
import { Screen } from "@/components/Screen";
import { Card } from "@/components/Card";
import { Cabecera } from "@/components/Cabecera";
import { Aparecer } from "@/components/Animations";
import { Texto } from "@/components/Texto";
import { useTheme, spacing, radius } from "@/theme";

export default function AcercaScreen() {
  const { colors } = useTheme();
  const version = Constants.expoConfig?.version ?? "1.0.0";

  return (
    <Screen conPadding={false}>
      <Cabecera titulo="Información de la app" atras />
      <ScrollView contentContainerStyle={estilos.cuerpo}>
        <Aparecer>
          <Card>
            <View style={estilos.marca}>
              <View style={[estilos.logo, { backgroundColor: colors.brand }]}>
                <Texto variante="display" color={colors.white}>G</Texto>
              </View>
              <Texto variante="title" color={colors.ink} style={{ marginTop: spacing.md }}>GeoTrack</Texto>
              <Texto variante="caption" color={colors.muted}>App del conductor · v{version}</Texto>
            </View>
            <Texto variante="body" color={colors.text} style={estilos.desc}>
              Gestiona tu ruta de reparto: revisa tus pedidos, navega a cada parada y registra tus entregas con evidencia.
            </Texto>
          </Card>
        </Aparecer>
      </ScrollView>
    </Screen>
  );
}

const estilos = StyleSheet.create({
  cuerpo: { padding: spacing.lg },
  marca: { alignItems: "center" },
  logo: { width: 64, height: 64, borderRadius: radius.xl, alignItems: "center", justifyContent: "center" },
  desc: { marginTop: spacing.lg, textAlign: "center" },
});
