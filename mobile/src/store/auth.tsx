// Estado de sesion del conductor: token persistido, iniciar/cerrar sesion, cierre ante 401.
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { login as loginRequest } from "@/api/auth";
import { guardarToken, borrarToken, leerToken } from "@/api/tokenStorage";
import { registrarCierrePorSesionExpirada } from "@/api/client";
import { limpiar as limpiarCola } from "@/store/colaSync";

interface ContextoAuth {
  token: string | null;
  cargando: boolean; // true mientras se lee el token guardado al arrancar
  sesionExpirada: boolean; // true si la última sesión expiró por 401
  iniciarSesion: (correo: string, contrasena: string) => Promise<void>;
  cerrarSesion: () => Promise<void>;
  limpiarAvisoExpirado: () => void;
}

const AuthContext = createContext<ContextoAuth | null>(null);

// Decodifica el payload de un token JWT para extraer el rol del usuario (C02-01 / CUS-02).
export function decodificarRol(token: string): string | null {
  try {
    const partes = token.split(".");
    if (partes.length < 2) return null;
    const base64Url = partes[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");

    let jsonStr = "";
    if (typeof atob === "function") {
      jsonStr = atob(base64);
    } else {
      const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";
      let buffer = 0;
      let bits = 0;
      for (let i = 0; i < base64.length; i++) {
        const char = base64.charAt(i);
        if (char === "=") break;
        const val = chars.indexOf(char);
        if (val === -1) continue;
        buffer = (buffer << 6) | val;
        bits += 6;
        if (bits >= 8) {
          bits -= 8;
          jsonStr += String.fromCharCode((buffer >> bits) & 0xff);
        }
      }
    }

    const payload = JSON.parse(jsonStr);
    return payload.rol || null;
  } catch (e) {
    console.error("[AUTH STORE] Error al decodificar rol del token:", e);
    return null;
  }
}

// Provee el estado de sesión a toda la app. Recibe: children (ReactNode).
export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [cargando, setCargando] = useState(true);
  const [sesionExpirada, setSesionExpirada] = useState(false);

  // Al montar: recupera el token del almacenamiento seguro y valida que sea de Conductor.
  useEffect(() => {
    leerToken()
      .then((savedToken) => {
        if (savedToken) {
          const rol = decodificarRol(savedToken);
          if (rol && rol.toUpperCase() !== "CONDUCTOR") {
            borrarToken();
            setToken(null);
            return;
          }
        }
        setToken(savedToken);
      })
      .finally(() => setCargando(false));
  }, []);

  // Si el backend devuelve 401, limpiamos la sesión y marcamos expiración (C02-01).
  useEffect(() => {
    registrarCierrePorSesionExpirada(() => {
      borrarToken();
      setToken(null);
      setSesionExpirada(true);
    });
  }, []);

  // Inicia sesión: pide el token, verifica que sea CONDUCTOR, lo guarda y actualiza el estado.
  const iniciarSesion = async (correo: string, contrasena: string) => {
    setSesionExpirada(false);
    const { access_token } = await loginRequest(correo, contrasena);

    // C02-01: Validar que el usuario autenticado sea de rol CONDUCTOR
    const rol = decodificarRol(access_token);

    if (rol && rol.toUpperCase() !== "CONDUCTOR") {
      throw new Error(`Acceso denegado: Esta aplicación es de uso exclusivo para conductores (tu rol es: ${rol}).`);
    }

    await guardarToken(access_token);
    setToken(access_token);
  };

  // Cierra sesion: borra el token, limpia estado y vacia la cola de sincronizacion.
  const cerrarSesion = async () => {
    setSesionExpirada(false);
    limpiarCola().catch(() => {});
    await borrarToken();
    setToken(null);
  };

  const limpiarAvisoExpirado = () => {
    setSesionExpirada(false);
  };

  return (
    <AuthContext.Provider value={{ token, cargando, sesionExpirada, iniciarSesion, cerrarSesion, limpiarAvisoExpirado }}>
      {children}
    </AuthContext.Provider>
  );
}

// Hook para usar la sesión. Devuelve: el contexto de autenticación.
export function useAuth(): ContextoAuth {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de <AuthProvider>");
  return ctx;
}
