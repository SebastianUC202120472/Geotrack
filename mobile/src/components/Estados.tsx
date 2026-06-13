// Vistas reutilizables de carga, error y vacío (estados de una pantalla).
import { ActivityIndicator, StyleSheet, Text, View } from "react-native";
import { useTheme, fontSize, spacing } from "@/theme";
import { Button } from "./Button";

// Indicador de carga centrado. Recibe: texto opcional.
export function Cargando({ texto = "Cargando…" }: { texto?: string }) {
  const { colors } = useTheme();
  return (
    <View style={estilos.centro}>
      <ActivityIndicator size="large" color={colors.brand} />
      <Text style={[estilos.texto, { color: colors.muted }]}>{texto}</Text>
    </View>
  );
}

// Vista de error con opción de reintentar. Recibe: mensaje (string), onReintentar?().
export function ErrorVista({ mensaje, onReintentar }: { mensaje: string; onReintentar?: () => void }) {
  const { colors } = useTheme();
  return (
    <View style={estilos.centro}>
      <Text style={[estilos.titulo, { color: colors.ink }]}>Algo salió mal</Text>
      <Text style={[estilos.texto, { color: colors.muted }]}>{mensaje}</Text>
      {onReintentar && (
        <View style={estilos.accion}>
          <Button titulo="Reintentar" variante="secondary" onPress={onReintentar} />
        </View>
      )}
    </View>
  );
}

// Vista de estado vacío. Recibe: titulo (string), detalle? (string).
export function Vacio({ titulo, detalle }: { titulo: string; detalle?: string }) {
  const { colors } = useTheme();
  return (
    <View style={estilos.centro}>
      <Text style={[estilos.titulo, { color: colors.ink }]}>{titulo}</Text>
      {detalle && <Text style={[estilos.texto, { color: colors.muted }]}>{detalle}</Text>}
    </View>
  );
}

const estilos = StyleSheet.create({
  centro: { flex: 1, alignItems: "center", justifyContent: "center", padding: spacing.xl, gap: spacing.sm },
  titulo: { fontSize: fontSize.subtitle, fontWeight: "700", textAlign: "center" },
  texto: { fontSize: fontSize.body, textAlign: "center" },
  accion: { marginTop: spacing.md, alignSelf: "stretch" },
});
