// Layout raíz: tema + React Query + sesión, y protección de rutas (sin token no
// se entra a las pantallas internas; con token no se vuelve al login).
import { useEffect } from "react";
import { Slot, useRouter, useSegments } from "expo-router";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { StatusBar } from "expo-status-bar";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider, useTheme } from "@/theme";
import { AuthProvider, useAuth } from "@/store/auth";
import { Cargando } from "@/components/Estados";

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, refetchOnWindowFocus: false } },
});

// Barra de estado adaptada al tema. No recibe props.
function Barra() {
  const { esquema } = useTheme();
  return <StatusBar style={esquema === "dark" ? "light" : "dark"} />;
}

// Redirige según la sesión. No recibe props; usa el contexto de auth.
function Guardia() {
  const { token, cargando } = useAuth();
  const segmentos = useSegments();
  const router = useRouter();

  useEffect(() => {
    if (cargando) return;
    const enLogin = segmentos[0] === "(auth)";
    if (!token && !enLogin) router.replace("/login");
    else if (token && enLogin) router.replace("/");
  }, [token, cargando, segmentos]);

  if (cargando) return <Cargando texto="Iniciando…" />;
  return <Slot />;
}

// Punto de entrada de la navegación.
export default function RootLayout() {
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
