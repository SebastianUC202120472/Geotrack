// Envoltorios de animación reutilizables con el API Animated nativo. Animan la
// entrada (fade + leve desplazamiento). Respetan "reducir movimiento" del SO.
import { useEffect, useRef, useState } from "react";
import { AccessibilityInfo, Animated, type ViewProps } from "react-native";

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
