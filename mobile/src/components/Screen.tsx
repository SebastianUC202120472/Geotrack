// Contenedor base de pantalla: fondo del tema y respeto del área segura.
import { StyleSheet, View, type ViewProps } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useTheme, spacing } from "@/theme";

interface Props extends ViewProps {
  conPadding?: boolean; // agrega padding interno (por defecto true)
}

// Recibe: children, conPadding?, y props de View.
export function Screen({ children, conPadding = true, style, ...props }: Props) {
  const { colors } = useTheme();
  return (
    <SafeAreaView style={[estilos.safe, { backgroundColor: colors.canvas }]} edges={["top", "bottom"]}>
      <View style={[estilos.cuerpo, conPadding && estilos.padding, style]} {...props}>
        {children}
      </View>
    </SafeAreaView>
  );
}

const estilos = StyleSheet.create({
  safe: { flex: 1 },
  cuerpo: { flex: 1 },
  padding: { padding: spacing.lg },
});
