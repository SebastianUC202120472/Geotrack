// Navegación interna (protegida). Stack con cabecera de marca y accesos a
// Historial y cierre de sesión.
import { Stack, useRouter } from "expo-router";
import { Pressable, Text, StyleSheet } from "react-native";
import { useAuth } from "@/store/auth";
import { colors, fontSize, spacing } from "@/theme";

// Botón de texto para la cabecera. Recibe: { titulo, onPress }.
function BotonCabecera({ titulo, onPress }: { titulo: string; onPress: () => void }) {
  return (
    <Pressable onPress={onPress} accessibilityRole="button" accessibilityLabel={titulo} hitSlop={8}>
      <Text style={estilos.boton}>{titulo}</Text>
    </Pressable>
  );
}

export default function AppLayout() {
  const router = useRouter();
  const { cerrarSesion } = useAuth();

  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: colors.ink },
        headerTintColor: colors.white,
        headerTitleStyle: { fontWeight: "700" },
        contentStyle: { backgroundColor: colors.canvas },
      }}
    >
      <Stack.Screen
        name="index"
        options={{
          title: "Mi ruta",
          headerRight: () => (
            <BotonCabecera titulo="Historial" onPress={() => router.push("/historial")} />
          ),
          headerLeft: () => <BotonCabecera titulo="Salir" onPress={cerrarSesion} />,
        }}
      />
      <Stack.Screen name="parada/[id]" options={{ title: "Entrega" }} />
      <Stack.Screen name="historial" options={{ title: "Entregados" }} />
    </Stack>
  );
}

const estilos = StyleSheet.create({
  boton: { color: colors.white, fontSize: fontSize.body, fontWeight: "700", paddingHorizontal: spacing.sm },
});
