// Navegador de pestañas: Pedidos · Ruta · Reportes · Ajustes (⚙). Abre en "Ruta".
// Las pantallas de detalle (perfil, ayuda, etc.) NO viven aquí: están en el Stack
// padre (app)/_layout, para que el botón "atrás" vuelva a la pantalla anterior.
import { Tabs } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { useTheme, fuentes } from "@/theme";

export default function TabsLayout() {
  const { colors } = useTheme();

  return (
    <Tabs
      initialRouteName="index"
      screenOptions={{
        headerShown: false, // cada pestaña usa su propia <Cabecera>
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
      <Tabs.Screen
        name="pedidos"
        options={{ title: "Pedidos", tabBarLabel: "Pedidos", tabBarIcon: ({ color, size }) => <Ionicons name="cube" color={color} size={size} /> }}
      />
      <Tabs.Screen
        name="index"
        options={{ title: "Ruta", tabBarLabel: "Ruta", tabBarIcon: ({ color, size }) => <Ionicons name="map" color={color} size={size} /> }}
      />
      <Tabs.Screen
        name="reportes"
        options={{ title: "Reportes", tabBarLabel: "Reportes", tabBarIcon: ({ color, size }) => <Ionicons name="alert-circle-outline" color={color} size={size} /> }}
      />
      <Tabs.Screen
        name="ajustes"
        options={{ title: "Ajustes", tabBarLabel: "Ajustes", tabBarIcon: ({ color, size }) => <Ionicons name="settings-outline" color={color} size={size} /> }}
      />
    </Tabs>
  );
}
