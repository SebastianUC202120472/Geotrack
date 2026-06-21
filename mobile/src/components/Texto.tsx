// Texto tematizado: aplica la tipografía Inter por variante y el color del tema.
// Recibe: { variante?, color?, ...props de Text }.
import { Text, type TextProps } from "react-native";
import { useTheme } from "@/theme";
import { tipografia, type VarianteTexto } from "@/theme/tipografia";

interface Props extends TextProps {
  variante?: VarianteTexto;
  color?: string;
}

export function Texto({ variante = "body", color, style, ...props }: Props) {
  const { colors } = useTheme();
  return <Text style={[tipografia[variante], { color: color ?? colors.text }, style]} {...props} />;
}
