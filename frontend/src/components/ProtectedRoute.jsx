import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

// Protege las rutas del panel: sin sesión, manda al login. Además, el rol 'almacen'
// solo puede acceder a su módulo (/almacen); cualquier otra ruta lo redirige ahí.
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
