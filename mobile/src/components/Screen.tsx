// Contenedor base de pantalla: fondo del tema y respeto del área segura.
import { StyleSheet, View, type ViewProps } from "react-native";
import { SafeAreaView, type Edge } from "react-native-safe-area-context";
import { useTheme, spacing } from "@/theme";

interface Props extends ViewProps {
  conPadding?: boolean; // agrega padding interno (por defecto true)
  topInset?: boolean; // true solo en pantallas sin cabecera de navegacion (ej. login)
}

export function Screen({ children, conPadding = true, topInset = false, style, ...props }: Props) {
  const { colors } = useTheme();
  const edges: Edge[] = topInset ? ["top", "bottom"] : ["bottom"];
  return (
    <SafeAreaView style={[estilos.safe, { backgroundColor: colors.canvas }]} edges={edges}>
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
