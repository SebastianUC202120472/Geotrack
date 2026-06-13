// Tokens de diseño centralizados (colores, espaciados, radios, tipografía,
// tamaños de toque). Pensados para alto contraste y uso bajo el sol.

// Paleta: negro / azul de marca / blanco / gris humo.
export const colors = {
  brand: "#2563EB",
  brandPressed: "#1D4ED8",
  brandSoft: "#EFF6FF",
  ink: "#0F172A",
  text: "#334155",
  muted: "#64748B",
  surface: "#FFFFFF",
  canvas: "#F1F5F9",
  border: "#E2E8F0",
  success: "#16A34A",
  successSoft: "#DCFCE7",
  warning: "#F59E0B",
  warningSoft: "#FEF3C7",
  danger: "#DC2626",
  dangerSoft: "#FEE2E2",
  white: "#FFFFFF",
} as const;

// Espaciados base (múltiplos de 4) para un ritmo visual consistente.
export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
} as const;

export const radius = { sm: 8, md: 12, lg: 16, pill: 999 } as const;

// Tamaños de tipografía amplios y legibles.
export const fontSize = {
  caption: 13,
  body: 16,
  subtitle: 18,
  title: 22,
  display: 28,
} as const;

// Altura mínima de los elementos táctiles (accesibilidad: >= 48).
export const touch = { minTarget: 48, primaryButton: 56 } as const;
