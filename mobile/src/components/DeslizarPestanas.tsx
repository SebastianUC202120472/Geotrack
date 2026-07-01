// Envoltorio flex:1 para pantallas de pestañas; la navegación es solo por toque.
import { StyleSheet, View, type ViewProps } from "react-native";

export function DeslizarPestanas({ children, style, ...props }: ViewProps) {
  return (
    <View style={[estilos.cont, style]} {...props}>
      {children}
    </View>
  );
}

const estilos = StyleSheet.create({
  cont: { flex: 1 },
});
