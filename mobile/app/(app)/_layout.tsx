// Navegación interna (protegida) por pestañas: Pedidos · Ruta (centro) · Historial.
// La app abre en "Ruta" (initialRouteName). Las pestañas usan cabecera propia
// (Cabecera), por eso ocultan la nativa. Perfil, Ajustes, Notificaciones y el
// detalle de parada son navegables (con cabecera nativa y botón atrás), no pestañas.
import { Tabs } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { useTheme, fuentes } from "@/theme";

export default function AppLayout() {
  const { colors } = useTheme();

  return (
    <Tabs
      initialRouteName="index"
      screenOptions={{
        headerShown: false, // las pestañas usan <Cabecera>; los detalles activan la nativa
        // El header nativo (Perfil/Ajustes/Notificaciones/detalle) usa surface+ink
        // para verse bien en claro Y oscuro (ink es texto, no fondo).
        headerStyle: { backgroundColor: colors.surface },
        headerTintColor: colors.ink,
        headerTitleStyle: { fontFamily: fuentes.bold, color: colors.ink },
        animation: "shift", // transición suave al cambiar de pestaña
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
          shadowColor: colors.shadow,
          shadowOpacity: 0.06,
          shadowRadius: 12,
          shadowOffset: { width: 0, height: -3 },
          elevation: 8,
        },
        sceneStyle: { backgroundColor: colors.canvas },
      }}
    >
      {/* Orden de las pestañas: Pedidos · Ruta (centro) · Historial */}
      <Tabs.Screen
        name="pedidos"
        options={{ title: "Pedidos", tabBarLabel: "Pedidos", tabBarIcon: ({ color, size }) => <Ionicons name="cube" color={color} size={size} /> }}
      />
      <Tabs.Screen
        name="index"
        options={{ title: "Ruta", tabBarLabel: "Ruta", tabBarIcon: ({ color, size }) => <Ionicons name="map" color={color} size={size} /> }}
      />
      <Tabs.Screen
        name="historial"
        options={{ title: "Historial", tabBarLabel: "Historial", tabBarIcon: ({ color, size }) => <Ionicons name="checkmark-done" color={color} size={size} /> }}
      />

      {/* Navegables (no pestañas): cabecera nativa con botón atrás. */}
      <Tabs.Screen name="perfil" options={{ href: null, headerShown: true, title: "Mi perfil" }} />
      <Tabs.Screen name="ajustes" options={{ href: null, headerShown: true, title: "Ajustes" }} />
      <Tabs.Screen name="notificaciones" options={{ href: null, headerShown: true, title: "Notificaciones" }} />
      <Tabs.Screen name="parada/[id]" options={{ href: null, headerShown: true, title: "Entrega" }} />
    </Tabs>
  );
}
