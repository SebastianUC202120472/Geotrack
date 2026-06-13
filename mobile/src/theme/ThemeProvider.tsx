// Provee el tema activo (claro/oscuro/sistema + acento de color) a toda la app,
// y persiste la preferencia del usuario.
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { useColorScheme } from "react-native";
import * as SecureStore from "expo-secure-store";
import { construirPaleta, type Acento, type Esquema, type Palette } from "./palettes";

export type Modo = "system" | "light" | "dark";

interface ContextoTema {
  colors: Palette;
  esquema: Esquema; // claro/oscuro ya resuelto
  modo: Modo;
  acento: Acento;
  setModo: (m: Modo) => void;
  setAcento: (a: Acento) => void;
}

const ThemeContext = createContext<ContextoTema | null>(null);
const CLAVE_MODO = "tema_modo";
const CLAVE_ACENTO = "tema_acento";

// Envuelve la app y entrega el tema. Recibe: children (ReactNode).
export function ThemeProvider({ children }: { children: ReactNode }) {
  const esquemaSistema = useColorScheme(); // "light" | "dark" | null
  const [modo, setModoState] = useState<Modo>("system");
  const [acento, setAcentoState] = useState<Acento>("azul");

  // Carga la preferencia guardada al iniciar.
  useEffect(() => {
    (async () => {
      const m = (await SecureStore.getItemAsync(CLAVE_MODO)) as Modo | null;
      const a = (await SecureStore.getItemAsync(CLAVE_ACENTO)) as Acento | null;
      if (m) setModoState(m);
      if (a) setAcentoState(a);
    })();
  }, []);

  const setModo = (m: Modo) => {
    setModoState(m);
    SecureStore.setItemAsync(CLAVE_MODO, m);
  };
  const setAcento = (a: Acento) => {
    setAcentoState(a);
    SecureStore.setItemAsync(CLAVE_ACENTO, a);
  };

  const esquema: Esquema = modo === "system" ? (esquemaSistema === "dark" ? "dark" : "light") : modo;
  const colors = useMemo(() => construirPaleta(esquema, acento), [esquema, acento]);

  return (
    <ThemeContext.Provider value={{ colors, esquema, modo, acento, setModo, setAcento }}>
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
// Devuelve: los estilos recalculados cuando cambia el tema.
export function useEstilos<T>(factory: (c: Palette) => T): T {
  const { colors } = useTheme();
  return useMemo(() => factory(colors), [colors, factory]);
}
