// Ajustes del conductor (apartado separado del perfil): tema claro/oscuro,
// contacto con coordinación y cierre de sesión. Pantalla navegable (con cabecera
// nativa y botón atrás); no es una pestaña.
import { Linking, Pressable, ScrollView, StyleSheet, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { Screen } from "@/components/Screen";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { Aparecer } from "@/components/Animations";
import { Texto } from "@/components/Texto";
import { useAuth } from "@/store/auth";
import { useTheme, spacing, radius, type Modo } from "@/theme";

// Número de coordinación para llamar/escribir. Cámbialo por el real (o usa env).
const TELEFONO_COORDINACION = process.env.EXPO_PUBLIC_COORDINACION_TEL ?? "+51999888777";
const MODOS: { valor: Modo; etiqueta: string; icono: keyof typeof Ionicons.glyphMap }[] = [
  { valor: "system", etiqueta: "Sistema", icono: "phone-portrait-outline" },
  { valor: "light", etiqueta: "Claro", icono: "sunny-outline" },
  { valor: "dark", etiqueta: "Oscuro", icono: "moon-outline" },
];

export default function AjustesScreen() {
  const { colors, modo, setModo } = useTheme();
  const { cerrarSesion } = useAuth();

  // Abre el marcador con el número de coordinación.
  const llamar = () => Linking.openURL(`tel:${TELEFONO_COORDINACION.replace(/\s/g, "")}`);
  // Abre WhatsApp con el número de coordinación.
  const whatsapp = () => Linking.openURL(`https://wa.me/${TELEFONO_COORDINACION.replace(/[^\d]/g, "")}`);

  return (
    <Screen conPadding={false}>
      <ScrollView contentContainerStyle={estilos.cuerpo}>
        {/* Tema */}
        <Aparecer delay={0}>
          <Card>
            <Texto variante="subtitle" color={colors.ink} style={estilos.titulo}>Apariencia</Texto>
            <Texto variante="caption" color={colors.muted}>Tema</Texto>
            <View style={estilos.fila}>
              {MODOS.map((m) => {
                const activo = modo === m.valor;
                return (
                  <Pressable
                    key={m.valor}
                    onPress={() => setModo(m.valor)}
                    accessibilityRole="button"
                    accessibilityLabel={`Tema ${m.etiqueta}`}
                    style={({ pressed }) => [
                      estilos.chip,
                      { borderColor: activo ? colors.brand : colors.border, backgroundColor: activo ? colors.brandSoft : colors.surface },
                      pressed && { opacity: 0.85 },
                    ]}
                  >
                    <Ionicons name={m.icono} size={20} color={activo ? colors.brand : colors.text} />
                    <Texto variante="label" color={activo ? colors.brand : colors.text}>{m.etiqueta}</Texto>
                  </Pressable>
                );
              })}
            </View>
          </Card>
        </Aparecer>

        {/* Contacto con coordinación */}
        <Aparecer delay={60}>
          <Card>
            <Texto variante="subtitle" color={colors.ink} style={estilos.titulo}>¿Algún problema?</Texto>
            <Texto variante="caption" color={colors.muted}>Contacta a coordinación o repórtalo desde el pedido.</Texto>
            <View style={[estilos.fila, { marginTop: spacing.md }]}>
              <View style={{ flex: 1 }}><Button titulo="Llamar" variante="secondary" onPress={llamar} /></View>
              <View style={{ flex: 1 }}><Button titulo="WhatsApp" variante="secondary" onPress={whatsapp} /></View>
            </View>
          </Card>
        </Aparecer>

        <Aparecer delay={120}>
          <Button titulo="Cerrar sesión" variante="danger" onPress={cerrarSesion} />
        </Aparecer>
      </ScrollView>
    </Screen>
  );
}

const estilos = StyleSheet.create({
  cuerpo: { padding: spacing.lg, gap: spacing.lg, paddingBottom: spacing.xl },
  titulo: { marginBottom: spacing.xs },
  fila: { flexDirection: "row", gap: spacing.sm, marginTop: spacing.xs },
  chip: { flex: 1, alignItems: "center", gap: spacing.xs, paddingVertical: spacing.md, borderRadius: radius.md, borderWidth: 1 },
});
