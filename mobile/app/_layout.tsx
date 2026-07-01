// Layout raíz: tema, React Query, sesión y protección de rutas.
import { Component, useEffect, useState, type ReactNode } from "react";
import { AppState, View, Text, Pressable, ScrollView } from "react-native";
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

// Red de seguridad: atrapa cualquier crash de render y muestra el error en pantalla
// (en vez de dejar la app en blanco), con un botón para reintentar.
class LimiteDeError extends Component<{ children: ReactNode }, { error: Error | null }> {
  state = { error: null as Error | null };
  static getDerivedStateFromError(error: Error) {
    return { error };
  }
  componentDidCatch(error: Error) {
    console.error("Crash atrapado:", error);
  }
  render() {
    if (this.state.error) {
      return (
        <View style={{ flex: 1, padding: 24, paddingTop: 64, backgroundColor: "#ffffff" }}>
          <Text style={{ fontSize: 18, fontWeight: "700", marginBottom: 8, color: "#0f172a" }}>
            Algo falló al abrir la app
          </Text>
          <Text style={{ color: "#334155", marginBottom: 12 }}>Toma una captura y envíala a soporte:</Text>
          <ScrollView style={{ maxHeight: 320, backgroundColor: "#f1f5f9", borderRadius: 8, padding: 12 }}>
            <Text style={{ color: "#b91c1c", fontSize: 12 }}>
              {String(this.state.error?.message ?? this.state.error)}
              {"\n\n"}
              {String(this.state.error?.stack ?? "")}
            </Text>
          </ScrollView>
          <Pressable
            onPress={() => this.setState({ error: null })}
            style={{ marginTop: 16, backgroundColor: "#2563eb", padding: 14, borderRadius: 8 }}
          >
            <Text style={{ color: "#ffffff", textAlign: "center", fontWeight: "700" }}>Reintentar</Text>
          </Pressable>
        </View>
      );
    }
    return this.props.children;
  }
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
    <LimiteDeError>
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
    </LimiteDeError>
  );
}
