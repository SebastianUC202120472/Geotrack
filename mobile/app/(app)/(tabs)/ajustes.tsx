// Ajustes del conductor (pestaña ⚙): lista de opciones (notificaciones, reportar
// un error, estado de la cuenta, información de la app, ayuda) + cerrar sesión.
import { useEffect, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Switch, View } from "react-native";
import { useRouter } from "expo-router";
import * as SecureStore from "expo-secure-store";
import { Ionicons } from "@expo/vector-icons";
import { Screen } from "@/components/Screen";
import { Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { Cabecera } from "@/components/Cabecera";
import { DeslizarPestanas } from "@/components/DeslizarPestanas";
import { Aparecer } from "@/components/Animations";
import { Texto } from "@/components/Texto";
import { useAuth } from "@/store/auth";
import { useTheme, spacing, radius, type Palette } from "@/theme";

const CLAVE_NOTIF = "notif_pedidos"; // preferencia local de avisos de nuevos pedidos

export default function AjustesScreen() {
  const { colors } = useTheme();
  const router = useRouter();
  const { cerrarSesion } = useAuth();

  const [notif, setNotif] = useState(true);
  // Carga la preferencia guardada al montar.
  useEffect(() => {
    SecureStore.getItemAsync(CLAVE_NOTIF).then((v) => {
      if (v != null) setNotif(v === "1");
    });
  }, []);
  // Cambia y persiste la preferencia de notificaciones.
  const cambiarNotif = (v: boolean) => {
    setNotif(v);
    SecureStore.setItemAsync(CLAVE_NOTIF, v ? "1" : "0");
  };

  return (
    <Screen conPadding={false}>
      <Cabecera titulo="Ajustes" />
      <DeslizarPestanas>
        <ScrollView contentContainerStyle={estilos.cuerpo}>
          {/* Notificaciones (interruptor) */}
          <Aparecer>
            <Card style={estilos.grupo}>
              <View style={estilos.fila}>
                <View style={[estilos.icono, { backgroundColor: colors.brandSoft }]}>
                  <Ionicons name="notifications-outline" size={18} color={colors.brand} />
                </View>
                <View style={{ flex: 1 }}>
                  <Texto variante="bodyMedium" color={colors.ink}>Notificaciones</Texto>
                  <Texto variante="caption" color={colors.muted}>Avisarme de nuevos pedidos</Texto>
                </View>
                <Switch value={notif} onValueChange={cambiarNotif} trackColor={{ true: colors.brand, false: colors.border }} />
              </View>
            </Card>
          </Aparecer>

          {/* Opciones (cada fila abre su pantalla) */}
          <Aparecer delay={60}>
            <Card style={estilos.grupo}>
              <FilaNav icono="bug-outline" titulo="Reportar un error" onPress={() => router.push("/feedback")} c={colors} />
              <Separador c={colors} />
              <FilaNav icono="shield-checkmark-outline" titulo="Estado de la cuenta" onPress={() => router.push("/cuenta")} c={colors} />
              <Separador c={colors} />
              <FilaNav icono="information-circle-outline" titulo="Información de la app" onPress={() => router.push("/acerca")} c={colors} />
              <Separador c={colors} />
              <FilaNav icono="help-circle-outline" titulo="Ayuda" onPress={() => router.push("/ayuda")} c={colors} />
            </Card>
          </Aparecer>

          <Aparecer delay={120}>
            <Button titulo="Cerrar sesión" variante="danger" onPress={cerrarSesion} />
          </Aparecer>
        </ScrollView>
      </DeslizarPestanas>
    </Screen>
  );
}

// Fila de ajuste navegable: ícono + título + flecha. Recibe: { icono, titulo, onPress, c }.
function FilaNav({ icono, titulo, onPress, c }: { icono: keyof typeof Ionicons.glyphMap; titulo: string; onPress: () => void; c: Palette }) {
  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      accessibilityLabel={titulo}
      style={({ pressed }) => [estilos.fila, pressed && { opacity: 0.6 }]}
    >
      <View style={[estilos.icono, { backgroundColor: c.brandSoft }]}>
        <Ionicons name={icono} size={18} color={c.brand} />
      </View>
      <Texto variante="bodyMedium" color={c.ink} style={{ flex: 1 }}>{titulo}</Texto>
      <Ionicons name="chevron-forward" size={18} color={c.muted} />
    </Pressable>
  );
}

// Línea separadora entre filas.
function Separador({ c }: { c: Palette }) {
  return <View style={[estilos.separador, { backgroundColor: c.border }]} />;
}

const estilos = StyleSheet.create({
  cuerpo: { padding: spacing.lg, gap: spacing.lg, paddingBottom: spacing.xl },
  grupo: { paddingVertical: spacing.xs },
  fila: { flexDirection: "row", alignItems: "center", gap: spacing.md, paddingVertical: spacing.sm },
  icono: { width: 38, height: 38, borderRadius: radius.md, alignItems: "center", justifyContent: "center" },
  separador: { height: 1, marginVertical: spacing.xs, marginLeft: 38 + spacing.md },
});
