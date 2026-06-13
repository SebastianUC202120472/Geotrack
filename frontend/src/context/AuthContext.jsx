import { createContext, useContext, useState } from "react";
import { getToken, guardarToken, borrarToken } from "../services/api";

// Maneja el estado de sesión del admin en toda la app.
// El token vive en localStorage (a través de los helpers de api.js) y aquí lo
// mantenemos también en memoria para que React re-renderice al entrar o salir.
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => getToken());

  const iniciarSesion = (nuevoToken) => {
    guardarToken(nuevoToken);
    setToken(nuevoToken);
  };

  const cerrarSesion = () => {
    borrarToken();
    setToken(null);
  };

  const valor = {
    token,
    autenticado: Boolean(token),
    iniciarSesion,
    cerrarSesion,
  };

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
