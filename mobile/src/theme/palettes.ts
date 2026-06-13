// Paletas de color para modo claro y oscuro, y los acentos seleccionables.
// Todas comparten las mismas claves para que los componentes no cambien.

export interface Palette {
  brand: string;
  brandPressed: string;
  brandSoft: string;
  ink: string; // texto fuerte / títulos
  text: string;
  muted: string;
  surface: string; // tarjetas
  canvas: string; // fondo
  border: string;
  success: string;
  successSoft: string;
  warning: string;
  warningSoft: string;
  danger: string;
  dangerSoft: string;
  white: string;
}

// Bases (sin el acento, que se inyecta aparte).
const claro: Omit<Palette, "brand" | "brandPressed"> = {
  brandSoft: "#EFF6FF",
  ink: "#0F172A",
  text: "#334155",
  muted: "#64748B",
  surface: "#FFFFFF",
  canvas: "#F1F5F9",
  border: "#E2E8F0",
  success: "#16A34A",
  successSoft: "#DCFCE7",
  warning: "#B45309",
  warningSoft: "#FEF3C7",
  danger: "#DC2626",
  dangerSoft: "#FEE2E2",
  white: "#FFFFFF",
};

const oscuro: Omit<Palette, "brand" | "brandPressed"> = {
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
};

export type Esquema = "light" | "dark";
export type Acento = "azul" | "verde" | "naranja";

// Color principal por acento { normal, presionado }.
const acentos: Record<Acento, { brand: string; brandPressed: string }> = {
  azul: { brand: "#2563EB", brandPressed: "#1D4ED8" },
  verde: { brand: "#16A34A", brandPressed: "#15803D" },
  naranja: { brand: "#EA580C", brandPressed: "#C2410C" },
};

// Construye la paleta final. Recibe: esquema (light/dark) y acento.
export function construirPaleta(esquema: Esquema, acento: Acento): Palette {
  const base = esquema === "dark" ? oscuro : claro;
  return { ...base, ...acentos[acento] };
}

export const ACENTOS: Acento[] = ["azul", "verde", "naranja"];
