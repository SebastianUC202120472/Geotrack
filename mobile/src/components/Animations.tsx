// Envoltorios de animación reutilizables con el API Animated nativo. Animan la
// entrada (fade + leve desplazamiento). Respetan "reducir movimiento" del SO.
import { useEffect, useRef, useState } from "react";
import { AccessibilityInfo, Animated, StyleSheet, View, type ViewProps } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Texto } from "./Texto";
import { useTheme, radius, type VarianteTexto } from "@/theme";

function useReducirMovimiento(): boolean {
  const [reducir, setReducir] = useState(false);
  useEffect(() => {
    let activo = true;
    AccessibilityInfo.isReduceMotionEnabled().then((v) => activo && setReducir(v));
    const sub = AccessibilityInfo.addEventListener("reduceMotionChanged", setReducir);
    return () => {
      activo = false;
      sub.remove();
    };
  }, []);
  return reducir;
}

interface AparecerProps extends ViewProps {
  delay?: number;
  desplazamiento?: number;
}

// Aparece con fade + translateY al montar. Entrada: { delay?, desplazamiento?, ...View }.
export function Aparecer({ delay = 0, desplazamiento = 12, style, children, ...props }: AparecerProps) {
  const reducir = useReducirMovimiento();
  const opacidad = useRef(new Animated.Value(0)).current;
  const desliz = useRef(new Animated.Value(desplazamiento)).current;

  useEffect(() => {
    if (reducir) {
      opacidad.setValue(1);
      desliz.setValue(0);
      return;
    }
    Animated.parallel([
      Animated.timing(opacidad, { toValue: 1, duration: 320, delay, useNativeDriver: true }),
      Animated.timing(desliz, { toValue: 0, duration: 320, delay, useNativeDriver: true }),
    ]).start();
  }, [reducir, delay, opacidad, desliz]);

  return (
    <Animated.View style={[{ opacity: opacidad, transform: [{ translateY: desliz }] }, style]} {...props}>
      {children}
    </Animated.View>
  );
}

// Igual que Aparecer pero con retardo en cascada por índice (listas).
export function ItemLista({ index = 0, ...props }: AparecerProps & { index?: number }) {
  return <Aparecer delay={Math.min(index, 8) * 50} {...props} />;
}

// Barra que anima su ancho según valor/total. Entrada: { valor, total, color?, fondo? }.
export function BarraProgreso({ valor, total, color, fondo }: { valor: number; total: number; color?: string; fondo?: string }) {
  const { colors } = useTheme();
  const reducir = useReducirMovimiento();
  const pct = total > 0 ? Math.min(1, valor / total) : 0;
  const anim = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    if (reducir) { anim.setValue(pct); return; }
    Animated.timing(anim, { toValue: pct, duration: 600, useNativeDriver: false }).start();
  }, [pct, reducir, anim]);
  const ancho = anim.interpolate({ inputRange: [0, 1], outputRange: ["0%", "100%"] });
  return (
    <View style={[estilosAnim.pista, { backgroundColor: fondo ?? colors.overlay }]}>
      <Animated.View style={[estilosAnim.relleno, { width: ancho, backgroundColor: color ?? colors.white }]} />
    </View>
  );
}

// Número que "cuenta" hasta su valor al montar/cambiar. Entrada: { valor, variante?, color? }.
export function Contador({ valor, variante = "title", color }: { valor: number; variante?: VarianteTexto; color?: string }) {
  const reducir = useReducirMovimiento();
  const anim = useRef(new Animated.Value(0)).current;
  const [mostrado, setMostrado] = useState(0);
  useEffect(() => {
    if (reducir) { setMostrado(valor); return; }
    const id = anim.addListener(({ value }) => setMostrado(Math.round(value)));
    Animated.timing(anim, { toValue: valor, duration: 700, useNativeDriver: false }).start();
    return () => anim.removeListener(id);
  }, [valor, reducir, anim]);
  return <Texto variante={variante} color={color}>{String(mostrado)}</Texto>;
}

// Punto que pulsa + etiqueta "En vivo". Entrada: { activo, color? }.
export function IndicadorEnVivo({ activo, color = "#FFFFFF" }: { activo: boolean; color?: string }) {
  const reducir = useReducirMovimiento();
  const anim = useRef(new Animated.Value(1)).current;
  useEffect(() => {
    if (!activo || reducir) return;
    const loop = Animated.loop(Animated.sequence([
      Animated.timing(anim, { toValue: 0.3, duration: 700, useNativeDriver: true }),
      Animated.timing(anim, { toValue: 1, duration: 700, useNativeDriver: true }),
    ]));
    loop.start();
    return () => loop.stop();
  }, [activo, reducir, anim]);
  if (!activo) return null;
  return (
    <View style={estilosAnim.enVivo}>
      <Animated.View style={[estilosAnim.punto, { backgroundColor: color, opacity: reducir ? 1 : anim }]} />
      <Texto variante="caption" color={color}>En vivo</Texto>
    </View>
  );
}

// Check que aparece con escala+resorte al confirmar. Entrada: { color, tamano? }.
export function CheckEntrega({ color, tamano = 64 }: { color: string; tamano?: number }) {
  const reducir = useReducirMovimiento();
  const escala = useRef(new Animated.Value(reducir ? 1 : 0)).current;
  useEffect(() => {
    if (reducir) { escala.setValue(1); return; }
    Animated.spring(escala, { toValue: 1, useNativeDriver: true, friction: 5, tension: 80 }).start();
  }, [reducir, escala]);
  return (
    <Animated.View style={{ transform: [{ scale: escala }], alignItems: "center" }}>
      <Ionicons name="checkmark-circle" size={tamano} color={color} />
    </Animated.View>
  );
}

const estilosAnim = StyleSheet.create({
  pista: { height: 8, borderRadius: radius.pill, overflow: "hidden" },
  relleno: { height: "100%", borderRadius: radius.pill },
  enVivo: { flexDirection: "row", alignItems: "center", gap: 6 },
  punto: { width: 8, height: 8, borderRadius: radius.pill },
});
