// Tokens de tipografía (Inter). En RN con fuentes custom hay que fijar fontFamily
// por peso: fontWeight NO selecciona el archivo. Cada rol define familia+tamaño.
import type { TextStyle } from "react-native";

export const fuentes = {
  regular: "Inter_400Regular",
  medium: "Inter_500Medium",
  semibold: "Inter_600SemiBold",
  bold: "Inter_700Bold",
  extrabold: "Inter_800ExtraBold",
} as const;

export type VarianteTexto =
  | "display" | "title" | "subtitle" | "body" | "bodyMedium" | "label" | "caption";

export const tipografia: Record<VarianteTexto, TextStyle> = {
  display:    { fontFamily: fuentes.extrabold, fontSize: 28, lineHeight: 34 },
  title:      { fontFamily: fuentes.extrabold, fontSize: 22, lineHeight: 28 },
  subtitle:   { fontFamily: fuentes.bold,      fontSize: 18, lineHeight: 24 },
  body:       { fontFamily: fuentes.regular,   fontSize: 16, lineHeight: 24 },
  bodyMedium: { fontFamily: fuentes.medium,    fontSize: 16, lineHeight: 24 },
  label:      { fontFamily: fuentes.semibold,  fontSize: 14, lineHeight: 20 },
  caption:    { fontFamily: fuentes.medium,    fontSize: 13, lineHeight: 18 },
};
