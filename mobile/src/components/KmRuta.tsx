import { Texto } from "@/components/Texto";
import { useTheme } from "@/theme";

interface Props {
  kmEstimado?: number | null;
  kmAhorrado?: number | null;
}

// Línea de la cabecera con el recorrido calculado al optimizar y el ahorro (C20-01).
// Recibe kmEstimado y kmAhorrado; no muestra nada si la ruta aún no se optimizó.
export function KmRuta({ kmEstimado, kmAhorrado }: Props) {
  const { colors } = useTheme();
  if (kmEstimado == null) return null;
  const ahorro = kmAhorrado && kmAhorrado > 0 ? ` · ahorras ${kmAhorrado.toFixed(1)} km` : "";
  return (
    <Texto variante="caption" color={colors.white} style={{ opacity: 0.9, marginTop: 2 }}>
      🛣️ {kmEstimado.toFixed(1)} km estimados{ahorro}
    </Texto>
  );
}
