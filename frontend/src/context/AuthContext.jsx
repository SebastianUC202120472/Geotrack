import { useState } from "react";
import { AuthContext } from "./authContexto";
import { getToken, guardarToken, borrarToken, leerRol } from "../services/api";

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

  const rol = token ? leerRol(token) : null;
  const valor = {
    token,
    autenticado: Boolean(token),
    rol,
    iniciarSesion,
    cerrarSesion,
  };

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>;
}

