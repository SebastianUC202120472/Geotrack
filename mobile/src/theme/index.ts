// Punto único del sistema de diseño: tokens estáticos + tema dinámico (claro/oscuro).
import type { Palette } from "./palettes";

export { ThemeProvider, useTheme, useEstilos } from "./ThemeProvider";
export type { Modo } from "./ThemeProvider";
export { construirPaleta } from "./palettes";
export type { Palette, Esquema } from "./palettes";

export const spacing = { xs: 4, sm: 8, md: 12, lg: 16, xl: 24, xxl: 32 } as const;
export const radius = { sm: 8, md: 12, lg: 16, xl: 20, pill: 999 } as const;
export const fontSize = { caption: 13, body: 16, subtitle: 18, title: 22, display: 28 } as const;
export const touch = { minTarget: 48, primaryButton: 56 } as const;

// Estilo de sombra coherente con el tema (más marcada = más profundidad).
// Recibe: la paleta activa.
export function sombra(colors: Palette) {
  return {
    shadowColor: colors.shadow,
    shadowOpacity: 0.12,
    shadowRadius: 16,
    shadowOffset: { width: 0, height: 6 },
    elevation: 5,
  } as const;
}

export { fuentes, tipografia } from "./tipografia";
export type { VarianteTexto } from "./tipografia";
