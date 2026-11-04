import { useContext } from "react";
import { AuthContext } from "../context/authContexto";

// Devuelve la sesión del admin { token, rol, autenticado, iniciarSesion, cerrarSesion }. Sin parámetros.
export const useAuth = () => useContext(AuthContext);
