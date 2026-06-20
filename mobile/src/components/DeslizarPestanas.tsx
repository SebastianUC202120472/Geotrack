// Permite cambiar de pestaña deslizando el dedo en horizontal (además de tocar el
// ícono). Usa PanResponder nativo (sin dependencias extra): solo captura gestos
// claramente horizontales, dejando pasar el scroll vertical de las listas.
// Orden de pestañas: Pedidos · Ruta (/) · Ajustes — debe coincidir con _layout.
import { useRef } from "react";
import { PanResponder, StyleSheet, View, type ViewProps } from "react-native";
import { usePathname, useRouter, type Href } from "expo-router";

const ORDEN: Href[] = ["/pedidos", "/", "/ajustes"];

export function DeslizarPestanas({ children, style, ...props }: ViewProps) {
  const router = useRouter();
  const pathname = usePathname();
  // El índice actual se guarda en un ref para que el PanResponder (creado una vez)
  // siempre lea el valor vigente y no uno "congelado".
  const idxRef = useRef(0);
  idxRef.current = ORDEN.indexOf(pathname as Href);

  const responder = useRef(
    PanResponder.create({
      // Solo toma el gesto si es claramente horizontal (no roba el scroll vertical).
      onMoveShouldSetPanResponder: (_e, g) => Math.abs(g.dx) > 24 && Math.abs(g.dx) > Math.abs(g.dy) * 1.5,
      onPanResponderRelease: (_e, g) => {
        const i = idxRef.current;
        if (i < 0) return;
        if (g.dx <= -60 && i < ORDEN.length - 1) router.navigate(ORDEN[i + 1]);
        else if (g.dx >= 60 && i > 0) router.navigate(ORDEN[i - 1]);
      },
    })
  ).current;

  return (
    <View style={[estilos.cont, style]} {...responder.panHandlers} {...props}>
      {children}
    </View>
  );
}

const estilos = StyleSheet.create({
  cont: { flex: 1 },
});
