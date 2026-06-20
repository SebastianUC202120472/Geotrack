// Layout raíz: tema + React Query + sesión, y protección de rutas (sin token no
// se entra a las pantallas internas; con token no se vuelve al login).
import { useEffect, useState } from "react";
import { AppState } from "react-native";
import { Slot, useRouter, useSegments } from "expo-router";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { StatusBar } from "expo-status-bar";
import { QueryClient, QueryClientProvider, focusManager } from "@tanstack/react-query";
import { ThemeProvider as NavThemeProvider, DefaultTheme as NavLight, DarkTheme as NavDark } from "@react-navigation/native";
import { useFonts, Inter_400Regular, Inter_500Medium, Inter_600SemiBold, Inter_700Bold, Inter_800ExtraBold } from "@expo-google-fonts/inter";
import { ThemeProvider, useTheme } from "@/theme";
import { AuthProvider, useAuth } from "@/store/auth";
import { CamionCargando } from "@/components/CamionCargando";

// Datos "frescos" por poco tiempo: así al volver a la app o a una pantalla se
// vuelven a pedir y la información se actualiza sola (sin cerrar sesión).
const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 5_000, refetchOnWindowFocus: true, refetchOnReconnect: true },
  },
});

// Barra de estado adaptada al tema. No recibe props.
function Barra() {
  const { esquema } = useTheme();
  return <StatusBar style={esquema === "dark" ? "light" : "dark"} />;
}

// Redirige según la sesión y espera a que Inter cargue. No recibe props.
function Guardia() {
  const { token, cargando } = useAuth();
  const { colors, esquema } = useTheme();
  const segmentos = useSegments();
  const router = useRouter();

  // Tema de React Navigation alineado a nuestra paleta. Sin esto, el navegador usa
  // su tema claro por defecto y en modo oscuro asoman bordes/fondos blancos.
  const baseNav = esquema === "dark" ? NavDark : NavLight;
  const temaNav = {
    ...baseNav,
    colors: {
      ...baseNav.colors,
      background: colors.canvas,
      card: colors.surface,
      border: colors.border,
      primary: colors.brand,
      text: colors.ink,
    },
  };

  // Carga las variantes de Inter; si falla (errorFuentes) la app sigue con fuente del sistema.
  const [fuentesListas, errorFuentes] = useFonts({
    Inter_400Regular, Inter_500Medium, Inter_600SemiBold, Inter_700Bold, Inter_800ExtraBold,
  });

  // El camión se muestra como splash AL INICIAR la app durante 3 s (y nada más;
  // los cambios de pantalla ya no muestran el camión).
  const [splashMin, setSplashMin] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setSplashMin(true), 3000);
    return () => clearTimeout(t);
  }, []);

  // "Listo" = sesión cargada Y fuentes resueltas (o su carga falló). Solo cuando
  // está listo se monta el <Slot/>; por eso la navegación debe esperar lo mismo:
  // navegar antes de montar el layout dispara "navigate before mounting Root Layout".
  const listo = !cargando && (fuentesListas || !!errorFuentes) && splashMin;

  useEffect(() => {
    if (!listo) return;
    const enLogin = segmentos[0] === "(auth)";
    if (!token && !enLogin) router.replace("/login");
    else if (token && enLogin) router.replace("/");
  }, [listo, token, segmentos]);

  // Mientras no esté listo, pantalla de carga con el camión (todavía sin <Slot/> montado).
  if (!listo) return <CamionCargando texto="Iniciando…" />;
  return (
    <NavThemeProvider value={temaNav}>
      <Slot />
    </NavThemeProvider>
  );
}

// Punto de entrada de la navegación.
export default function RootLayout() {
  // React Query refresca al volver la app a primer plano (foco por AppState).
  useEffect(() => {
    const sub = AppState.addEventListener("change", (estado) => {
      focusManager.setFocused(estado === "active");
    });
    return () => sub.remove();
  }, []);

  return (
    <SafeAreaProvider>
      <ThemeProvider>
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <Barra />
            <Guardia />
          </AuthProvider>
        </QueryClientProvider>
      </ThemeProvider>
    </SafeAreaProvider>
  );
}
