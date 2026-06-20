// Paleta de color (solo modo claro). Azul de marca sobrio (no chillón), blanco
// humo en superficies y fondo algo más gris para dar profundidad por capas.
export interface Palette {
  brand: string;
  brandPressed: string;
  brandSoft: string;
  ink: string;
  text: string;
  muted: string;
  surface: string;
  canvas: string;
  border: string;
  success: string;
  successSoft: string;
  warning: string;
  warningSoft: string;
  danger: string;
  dangerSoft: string;
  white: string;
  brandInk: string;
  shadow: string;
  overlay: string;
}

const claro: Palette = {
  brand: "#1D4ED8",        // azul más oscuro/sobrio (antes #2563EB, muy chillón)
  brandPressed: "#1E3A8A",
  brandSoft: "#E7EEFB",
  ink: "#0F172A",
  text: "#334155",
  muted: "#64748B",
  surface: "#F7F8FA",      // blanco humo (tarjetas)
  canvas: "#E7ECF2",       // fondo algo más gris (da profundidad bajo las tarjetas)
  border: "#D8DEE7",
  success: "#16A34A",
  successSoft: "#DCFCE7",
  warning: "#D97706",
  warningSoft: "#FFFBEB",
  danger: "#DC2626",
  dangerSoft: "#FEE2E2",
  white: "#FFFFFF",        // blanco puro: solo para texto/iconos sobre el degradado
  brandInk: "#1E3A8A",
  shadow: "#0F172A",
  overlay: "rgba(255,255,255,0.16)",
};

export type Esquema = "light" | "dark";

// Construye la paleta final. La app es SOLO modo claro: siempre devuelve `claro`.
export function construirPaleta(_esquema: Esquema): Palette {
  return claro;
}
