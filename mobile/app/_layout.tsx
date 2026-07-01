// Layout raíz: tema, React Query, sesión y protección de rutas.
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
// Registra la tarea de ubicación en segundo plano al arrancar la app.
import "@/tasks/ubicacionBackground";

// Cliente de React Query con staleTime corto para auto-refresh al volver a la app.
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

  // Carga fuentes Inter; si falla, la app usa la fuente del sistema.
  const [fuentesListas, errorFuentes] = useFonts({
    Inter_400Regular, Inter_500Medium, Inter_600SemiBold, Inter_700Bold, Inter_800ExtraBold,
  });

  // Splash mínimo de 3 s al iniciar la app.
  const [splashMin, setSplashMin] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setSplashMin(true), 3000);
    return () => clearTimeout(t);
  }, []);

  // Listo cuando la sesión y las fuentes resolvieron y pasó el splash mínimo.
  const listo = !cargando && (fuentesListas || !!errorFuentes) && splashMin;

  useEffect(() => {
    if (!listo) return;
    const enLogin = segmentos[0] === "(auth)";
    if (!token && !enLogin) router.replace("/login");
    else if (token && enLogin) router.replace("/");
  }, [listo, token, segmentos]);

  if (!listo) return <CamionCargando texto="Iniciando…" />;
  return (
    <NavThemeProvider value={temaNav}>
      <Slot />
    </NavThemeProvider>
  );
}

// Punto de entrada de la navegación. Registra el foco de AppState para React Query.
export default function RootLayout() {
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
