// Punto único del sistema de diseño: tokens estáticos + tema dinámico (claro/oscuro).
export { ThemeProvider, useTheme, useEstilos } from "./ThemeProvider";
export type { Modo } from "./ThemeProvider";
export { construirPaleta } from "./palettes";
export type { Palette, Esquema } from "./palettes";

export const spacing = { xs: 4, sm: 8, md: 12, lg: 16, xl: 24, xxl: 32 } as const;
export const radius = { sm: 8, md: 12, lg: 16, pill: 999 } as const;
export const fontSize = { caption: 13, body: 16, subtitle: 18, title: 22, display: 28 } as const;
export const touch = { minTarget: 48, primaryButton: 56 } as const;

export { fuentes, tipografia } from "./tipografia";
export type { VarianteTexto } from "./tipografia";
