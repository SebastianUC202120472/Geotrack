// Define los colores de marca de la app.
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
  brand: "#1D4ED8",
  brandPressed: "#1E3A8A",
  brandSoft: "#E7EEFB",
  ink: "#0F172A",
  text: "#334155",
  muted: "#64748B",
  surface: "#F7F8FA",
  canvas: "#E7ECF2",
  border: "#D8DEE7",
  success: "#16A34A",
  successSoft: "#DCFCE7",
  warning: "#D97706",
  warningSoft: "#FFFBEB",
  danger: "#DC2626",
  dangerSoft: "#FEE2E2",
  white: "#FFFFFF",
  brandInk: "#1E3A8A",
  shadow: "#0F172A",
  overlay: "rgba(255,255,255,0.16)",
};

export type Esquema = "light" | "dark";

// Construye la paleta final. La app es SOLO modo claro: siempre devuelve `claro`.
export function construirPaleta(_esquema: Esquema): Palette {
  return claro;
}
