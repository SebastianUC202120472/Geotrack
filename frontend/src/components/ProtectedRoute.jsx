import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

// Protege rutas: redirige al login sin sesión; almacen solo accede a /almacen.
export default function ProtectedRoute({ children }) {
  const { autenticado, rol } = useAuth();
  const location = useLocation();

  if (!autenticado) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  if (rol === "almacen" && !location.pathname.startsWith("/almacen")) {
    return <Navigate to="/almacen" replace />;
  }
  return children;
}
