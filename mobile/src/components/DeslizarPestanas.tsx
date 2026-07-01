// Contenedor de las pantallas de pestañas. Antes permitía cambiar de pestaña
// deslizando el dedo, pero ese gesto se retiró a pedido: ahora SOLO se navega
// tocando el tab en la barra inferior. Se conserva como envoltorio (flex:1) para
// no alterar el layout de las pantallas que lo usan.
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
