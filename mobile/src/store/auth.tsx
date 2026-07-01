// Estado de sesion del conductor: token persistido, iniciar/cerrar sesion, cierre ante 401.
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { login as loginRequest } from "@/api/auth";
import { guardarToken, borrarToken, leerToken } from "@/api/tokenStorage";
import { registrarCierrePorSesionExpirada } from "@/api/client";
import { limpiar as limpiarCola } from "@/store/colaSync";

interface ContextoAuth {
  token: string | null;
  cargando: boolean; // true mientras se lee el token guardado al arrancar
  iniciarSesion: (correo: string, contrasena: string) => Promise<void>;
  cerrarSesion: () => Promise<void>;
}

const AuthContext = createContext<ContextoAuth | null>(null);

// Provee el estado de sesión a toda la app. Recibe: children (ReactNode).
export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(null);
  const [cargando, setCargando] = useState(true);

  // Al montar: recupera el token del almacenamiento seguro.
  useEffect(() => {
    leerToken()
      .then(setToken)
      .finally(() => setCargando(false));
  }, []);

  // Si el backend devuelve 401, limpiamos la sesión automáticamente.
  useEffect(() => {
    registrarCierrePorSesionExpirada(() => {
      borrarToken();
      setToken(null);
    });
  }, []);

  // Inicia sesión: pide el token, lo guarda y actualiza el estado.
  const iniciarSesion = async (correo: string, contrasena: string) => {
    const { access_token } = await loginRequest(correo, contrasena);
    await guardarToken(access_token);
    setToken(access_token);
  };

  // Cierra sesion: borra el token, limpia estado y vacia la cola de sincronizacion.
  const cerrarSesion = async () => {
    limpiarCola().catch(() => {});
    await borrarToken();
    setToken(null);
  };

  return (
    <AuthContext.Provider value={{ token, cargando, iniciarSesion, cerrarSesion }}>
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
