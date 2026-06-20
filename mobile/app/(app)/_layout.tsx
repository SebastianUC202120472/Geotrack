// Navegación interna (protegida) por pestañas: Ruta, Entregados y Perfil.
// El detalle de parada (parada/[id]) es navegable pero no aparece como pestaña.
import { Tabs } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { useTheme, fuentes } from "@/theme";

export default function AppLayout() {
  const { colors } = useTheme();

  return (
    <Tabs
      screenOptions={{
        headerStyle: { backgroundColor: colors.ink },
        headerTintColor: colors.white,
        headerTitleStyle: { fontFamily: fuentes.bold },
        tabBarActiveTintColor: colors.brand,
        tabBarInactiveTintColor: colors.muted,
        tabBarLabelStyle: { fontSize: 11, fontFamily: fuentes.semibold },
        tabBarStyle: {
          backgroundColor: colors.surface,
          borderTopColor: colors.border,
          borderTopLeftRadius: 16,
          borderTopRightRadius: 16,
          height: 64,
          paddingBottom: 8,
          paddingTop: 8,
          shadowColor: "#0F172A",
          shadowOpacity: 0.06,
          shadowRadius: 12,
          shadowOffset: { width: 0, height: -3 },
          elevation: 8,
        },
        sceneStyle: { backgroundColor: colors.canvas },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: "Mi ruta",
          tabBarLabel: "Ruta",
          tabBarIcon: ({ color, size }) => <Ionicons name="map" color={color} size={size} />,
        }}
      />
      <Tabs.Screen
        name="historial"
        options={{
          title: "Entregados",
          tabBarLabel: "Historial",
          tabBarIcon: ({ color, size }) => <Ionicons name="checkmark-done" color={color} size={size} />,
        }}
      />
      <Tabs.Screen
        name="perfil"
        options={{
          title: "Mi perfil",
          tabBarLabel: "Perfil",
          tabBarIcon: ({ color, size }) => <Ionicons name="person" color={color} size={size} />,
        }}
      />
      {/* Detalle de parada: navegable por push, oculto del tab bar. */}
      <Tabs.Screen name="parada/[id]" options={{ href: null, title: "Entrega" }} />
    </Tabs>
  );
}
