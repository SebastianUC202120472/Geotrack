// Provee el tema a toda la app. La app es SOLO modo claro (se eliminó el modo
// oscuro y el selector de apariencia).
import { createContext, useContext, useMemo, type ReactNode } from "react";
import { construirPaleta, type Esquema, type Palette } from "./palettes";

// Se conserva el tipo por compatibilidad de exports, aunque ya no se use el selector.
export type Modo = "system" | "light" | "dark";

interface ContextoTema {
  colors: Palette;
  esquema: Esquema; // siempre "light"
}

const ThemeContext = createContext<ContextoTema | null>(null);

// Envuelve la app y entrega el tema (claro). Recibe: children (ReactNode).
export function ThemeProvider({ children }: { children: ReactNode }) {
  const colors = useMemo(() => construirPaleta("light"), []);
  return (
    <ThemeContext.Provider value={{ colors, esquema: "light" }}>
      {children}
    </ThemeContext.Provider>
  );
}

// Hook para leer el tema. Devuelve: el contexto del tema.
export function useTheme(): ContextoTema {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme debe usarse dentro de <ThemeProvider>");
  return ctx;
}

// Crea estilos dependientes del tema. Recibe: una función (colors) => estilos.
export function useEstilos<T>(factory: (c: Palette) => T): T {
  const { colors } = useTheme();
  return useMemo(() => factory(colors), [colors, factory]);
}
