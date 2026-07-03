import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

// Protege rutas: redirige al login sin sesión; almacen solo accede a /almacen.
export default function ProtectedRoute({ children }) {
  const { autenticado, rol } = useAuth();
  const location = useLocation();

  if (!autenticado) {
    return <Navigate to="/panel/login" replace state={{ from: location }} />;
  }
  if (rol === "almacen" && !location.pathname.startsWith("/panel/almacen")) {
    return <Navigate to="/panel/almacen" replace />;
  }
  return children;
}
