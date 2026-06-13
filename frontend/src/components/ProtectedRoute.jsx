import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

// Protege las rutas del panel: si no hay sesión, redirige al login y recuerda
// a dónde quería ir el usuario para volver ahí tras autenticarse.
export default function ProtectedRoute({ children }) {
  const { autenticado } = useAuth();
  const location = useLocation();

  if (!autenticado) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return children;
}
