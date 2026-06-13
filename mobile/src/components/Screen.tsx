// Contenedor base de pantalla: fondo "canvas" y respeto del área segura.
import { StyleSheet, View, type ViewProps } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { colors, spacing } from "@/theme";

interface Props extends ViewProps {
  // Si true, agrega padding interno (por defecto true).
  conPadding?: boolean;
}

// Recibe: children, conPadding?, y props de View.
export function Screen({ children, conPadding = true, style, ...props }: Props) {
  return (
    <SafeAreaView style={estilos.safe} edges={["top", "bottom"]}>
      <View style={[estilos.cuerpo, conPadding && estilos.padding, style]} {...props}>
        {children}
      </View>
    </SafeAreaView>
  );
}

const estilos = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.canvas },
  cuerpo: { flex: 1 },
  padding: { padding: spacing.lg },
});
