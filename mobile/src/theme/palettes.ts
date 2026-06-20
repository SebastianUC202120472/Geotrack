// Paletas de color para modo claro y oscuro. Acento azul de marca fijo
// (coherente con el panel web). Mismas claves en ambas para no romper componentes.
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
  warning: "#D97706",
  warningSoft: "#FFFBEB",
  danger: "#DC2626",
  dangerSoft: "#FEE2E2",
  white: "#FFFFFF",
  brandInk: "#1E3A8A",
  shadow: "#0F172A",
  overlay: "rgba(255,255,255,0.16)",
};

const oscuro: Palette = {
  brand: "#3B82F6",
  brandPressed: "#2563EB",
  brandSoft: "#1E293B",
  ink: "#F1F5F9",
  text: "#CBD5E1",
  muted: "#94A3B8",
  surface: "#1E293B",
  canvas: "#0F172A",
  border: "#334155",
  success: "#4ADE80",
  successSoft: "#14321F",
  warning: "#FBBF24",
  warningSoft: "#3B2F12",
  danger: "#F87171",
  dangerSoft: "#3B1D1D",
  white: "#FFFFFF",
  brandInk: "#BFDBFE",
  shadow: "#000000",
  overlay: "rgba(255,255,255,0.12)",
};

export type Esquema = "light" | "dark";

// Construye la paleta final. Recibe: esquema (light/dark).
export function construirPaleta(esquema: Esquema): Palette {
  return esquema === "dark" ? oscuro : claro;
}
