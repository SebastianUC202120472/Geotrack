// Stack interno (protegido): contiene el grupo de pestañas (tabs) y, POR ENCIMA,
// las pantallas de detalle (perfil, notificaciones, reportes, ayuda, feedback,
// cuenta, acerca, parada). Al estar en un Stack, el botón "atrás" vuelve a la
// pantalla anterior real (no a una pestaña por defecto). Todas ocultan la cabecera
// nativa: el grupo (tabs) usa <Cabecera> y las de detalle usan <Cabecera atras>.
import { Stack } from "expo-router";
import { useTheme } from "@/theme";

export default function AppLayout() {
  const { colors } = useTheme();
  return (
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
  );
}
