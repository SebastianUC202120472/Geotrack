// Bloque "esqueleto" pulsante para estados de carga. Entrada: { ancho?, alto?, radio? }.
import { useEffect, useRef } from "react";
import { Animated, type DimensionValue } from "react-native";
import { useTheme, radius as r } from "@/theme";

export function Skeleton({ ancho = "100%", alto = 16, radio = r.sm }: { ancho?: DimensionValue; alto?: number; radio?: number }) {
  const { colors } = useTheme();
  const v = useRef(new Animated.Value(0.4)).current;
  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(v, { toValue: 1, duration: 700, useNativeDriver: true }),
        Animated.timing(v, { toValue: 0.4, duration: 700, useNativeDriver: true }),
      ])
    );
    loop.start();
    return () => loop.stop();
  }, [v]);
  return <Animated.View style={{ width: ancho, height: alto, borderRadius: radio, backgroundColor: colors.border, opacity: v }} />;
}
