// Estado de la cuenta del conductor: si está activa, su rol, código y correo.
import { ScrollView, StyleSheet, View } from "react-native";
import { useQuery } from "@tanstack/react-query";
import { Ionicons } from "@expo/vector-icons";
import { Screen } from "@/components/Screen";
import { Card } from "@/components/Card";
import { Cabecera } from "@/components/Cabecera";
import { Cargando } from "@/components/Estados";
import { Aparecer } from "@/components/Animations";
import { Texto } from "@/components/Texto";
import { obtenerPerfil } from "@/api/conductor";
import { useTheme, spacing, radius } from "@/theme";

export default function CuentaScreen() {
  const { colors } = useTheme();
  const perfil = useQuery({ queryKey: ["perfil"], queryFn: obtenerPerfil, refetchInterval: 10_000 });

  if (perfil.isLoading) return <Screen conPadding={false}><Cabecera titulo="Estado de la cuenta" atras /><Cargando /></Screen>;

  const p = perfil.data;

  return (
    <Screen conPadding={false}>
      <Cabecera titulo="Estado de la cuenta" atras />
      <ScrollView contentContainerStyle={estilos.cuerpo}>
        <Aparecer>
          <Card>
            <View style={[estilos.estado, { backgroundColor: colors.successSoft }]}>
              <Ionicons name="checkmark-circle" size={18} color={colors.success} />
              <Texto variante="bodyMedium" color={colors.success}>Cuenta activa</Texto>
            </View>
            <Dato etiqueta="Rol" valor="Conductor" c={colors} />
            <Dato etiqueta="Código" valor={p?.codigo || "—"} c={colors} />
            <Dato etiqueta="Correo" valor={p?.correo || "—"} c={colors} />
          </Card>
        </Aparecer>
      </ScrollView>
    </Screen>
  );
}

// Fila etiqueta/valor. Recibe: { etiqueta, valor, c (paleta) }.
function Dato({ etiqueta, valor, c }: { etiqueta: string; valor: string; c: { muted: string; ink: string } }) {
  return (
    <View style={estilos.dato}>
      <Texto variante="caption" color={c.muted}>{etiqueta}</Texto>
      <Texto variante="bodyMedium" color={c.ink}>{valor}</Texto>
    </View>
  );
}

const estilos = StyleSheet.create({
  cuerpo: { padding: spacing.lg },
  estado: { flexDirection: "row", alignItems: "center", gap: spacing.sm, alignSelf: "flex-start", paddingHorizontal: spacing.md, paddingVertical: spacing.sm, borderRadius: radius.pill, marginBottom: spacing.md },
  dato: { marginTop: spacing.md },
});
