import { createContext } from "react";

// Contexto de sesión del admin (lo provee AuthProvider y lo lee useAuth).
export const AuthContext = createContext(null);
