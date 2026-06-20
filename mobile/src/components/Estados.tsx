// Vistas reutilizables de carga, error y vacío (estados de una pantalla).
import { ActivityIndicator, StyleSheet, View } from "react-native";
import { useTheme, spacing } from "@/theme";
import { Texto } from "@/components/Texto";
import { Button } from "./Button";

// Indicador de carga centrado. Recibe: texto opcional.
export function Cargando({ texto = "Cargando…" }: { texto?: string }) {
  const { colors } = useTheme();
  return (
    <View style={estilos.centro}>
      <ActivityIndicator size="large" color={colors.brand} />
      <Texto variante="body" color={colors.muted}>{texto}</Texto>
    </View>
  );
}

// Vista de error con opción de reintentar. Recibe: mensaje (string), onReintentar?().
export function ErrorVista({ mensaje, onReintentar }: { mensaje: string; onReintentar?: () => void }) {
  const { colors } = useTheme();
  return (
    <View style={estilos.centro}>
      <Texto variante="subtitle" color={colors.ink}>Algo salió mal</Texto>
      <Texto variante="body" color={colors.muted}>{mensaje}</Texto>
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
      <Texto variante="subtitle" color={colors.ink}>{titulo}</Texto>
      {detalle && <Texto variante="body" color={colors.muted}>{detalle}</Texto>}
    </View>
  );
}

const estilos = StyleSheet.create({
  centro: { flex: 1, alignItems: "center", justifyContent: "center", padding: spacing.xl, gap: spacing.sm },
  accion: { marginTop: spacing.md, alignSelf: "stretch" },
});
