// Punto único del sistema de diseño: tokens estáticos (espaciado, radios,
// tipografía, tamaños de toque) + el tema dinámico (colores claro/oscuro).
// Los colores se obtienen con useTheme()/useEstilos(); los tokens son fijos.

export { ThemeProvider, useTheme, useEstilos } from "./ThemeProvider";
export type { Modo } from "./ThemeProvider";
export { ACENTOS, construirPaleta } from "./palettes";
export type { Palette, Acento, Esquema } from "./palettes";

// Espaciados base (múltiplos de 4).
export const spacing = { xs: 4, sm: 8, md: 12, lg: 16, xl: 24, xxl: 32 } as const;

export const radius = { sm: 8, md: 12, lg: 16, pill: 999 } as const;

// Tamaños de tipografía amplios y legibles.
export const fontSize = {
  caption: 13,
  body: 16,
  subtitle: 18,
  title: 22,
  display: 28,
} as const;

// Alto mínimo de elementos táctiles (accesibilidad: >= 48).
export const touch = { minTarget: 48, primaryButton: 56 } as const;
