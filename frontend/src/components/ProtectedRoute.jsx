import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

// Protege rutas: redirige al login sin sesión; almacén solo accede a /almacen
// y a la consulta de capacidad (módulo de solo lectura para ese rol).
export default function ProtectedRoute({ children }) {
  const { autenticado, rol } = useAuth();
  const location = useLocation();

  if (!autenticado) {
    return <Navigate to="/panel/login" replace state={{ from: location }} />;
  }
  const rutaAlmacen =
    location.pathname.startsWith("/panel/almacen") || location.pathname === "/panel/capacidad";
  if (rol === "almacen" && !rutaAlmacen) {
    return <Navigate to="/panel/almacen" replace />;
  }
  return children;
}