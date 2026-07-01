// Stack protegido con pestañas y pantallas de detalle; MotorSync sincroniza al reconectar.
import { Stack } from "expo-router";
import { useTheme } from "@/theme";
import { MotorSync } from "@/features/sync/MotorSync";

export default function AppLayout() {
  const { colors } = useTheme();
  return (
    <>
      <MotorSync />
      <Stack screenOptions={{ headerShown: false, contentStyle: { backgroundColor: colors.canvas } }}>
        <Stack.Screen name="(tabs)" />
        <Stack.Screen name="perfil" />
        <Stack.Screen name="notificaciones" />
        <Stack.Screen name="reporte/[id]" />
        <Stack.Screen name="parada/[id]" />
        <Stack.Screen name="ayuda" />
        <Stack.Screen name="feedback" />
        <Stack.Screen name="cuenta" />
        <Stack.Screen name="acerca" />
      </Stack>
    </>
  );
}
