// Pantalla de carga con un camión que avanza por una vía. Se usa mientras la app
// arranca (o mientras carga la ruta). Respeta "reducir movimiento" del SO.
import { useEffect, useRef, useState } from "react";
import { AccessibilityInfo, Animated, Easing, StyleSheet, View } from "react-native";
import { MaterialCommunityIcons } from "@expo/vector-icons";
import { Texto } from "@/components/Texto";
import { useTheme, spacing, radius } from "@/theme";

// Recibe: { texto? } — mensaje bajo el nombre de la app.
export function CamionCargando({ texto = "Cargando tu ruta…" }: { texto?: string }) {
  const { colors } = useTheme();
  const avance = useRef(new Animated.Value(0)).current; // desplazamiento horizontal
  const salto = useRef(new Animated.Value(0)).current; // pequeño rebote vertical
  const [reducir, setReducir] = useState(false);

  // Lee la preferencia de "reducir movimiento" una vez al montar.
  useEffect(() => {
    let activo = true;
    AccessibilityInfo.isReduceMotionEnabled().then((v) => activo && setReducir(v));
    return () => {
      activo = false;
    };
  }, []);

  // Arranca los bucles de animación (camión avanzando + rebote), salvo reducir movimiento.
  useEffect(() => {
    if (reducir) return;
    const conducir = Animated.loop(
      Animated.timing(avance, { toValue: 1, duration: 1800, easing: Easing.linear, useNativeDriver: true })
    );
    const rebotar = Animated.loop(
      Animated.sequence([
        Animated.timing(salto, { toValue: 1, duration: 220, easing: Easing.inOut(Easing.quad), useNativeDriver: true }),
        Animated.timing(salto, { toValue: 0, duration: 220, easing: Easing.inOut(Easing.quad), useNativeDriver: true }),
      ])
    );
    conducir.start();
    rebotar.start();
    return () => {
      conducir.stop();
      rebotar.stop();
    };
  }, [reducir, avance, salto]);

  const translateX = avance.interpolate({ inputRange: [0, 1], outputRange: [-120, 120] });
  const translateY = salto.interpolate({ inputRange: [0, 1], outputRange: [0, -3] });

  return (
    <View style={[estilos.cont, { backgroundColor: colors.canvas }]}>
      <View style={estilos.escena}>
        <Animated.View style={{ transform: [{ translateX }, { translateY }] }}>
          <MaterialCommunityIcons name="truck-fast" size={58} color={colors.brand} />
        </Animated.View>
      </View>
      <View style={[estilos.via, { backgroundColor: colors.border }]} />
      <Texto variante="title" color={colors.ink} style={{ marginTop: spacing.xl }}>GeoTrack</Texto>
      <Texto variante="caption" color={colors.muted} style={{ marginTop: 2 }}>{texto}</Texto>
    </View>
  );
}

const estilos = StyleSheet.create({
  cont: { flex: 1, alignItems: "center", justifyContent: "center", padding: spacing.xl },
  escena: { width: 220, height: 64, alignItems: "center", justifyContent: "center", overflow: "hidden" },
  via: { width: 200, height: 4, borderRadius: radius.pill, opacity: 0.6 },
});
