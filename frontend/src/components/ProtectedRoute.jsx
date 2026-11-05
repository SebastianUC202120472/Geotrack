import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

// Pantallas fuera de /almacen que también abre el personal de almacén.
const RUTAS_EXTRA_ALMACEN = ["/panel/capacidad", "/panel/asistente"];

// Protege rutas: redirige al login sin sesión; almacén solo accede a /almacen, a la
// consulta de capacidad (solo lectura) y al asistente con IA (ve lo mismo que su rol).
export default function ProtectedRoute({ children }) {
  const { autenticado, rol } = useAuth();
  const location = useLocation();

  if (!autenticado) {
    return <Navigate to="/panel/login" replace state={{ from: location }} />;
  }
  const rutaAlmacen =
    location.pathname.startsWith("/panel/almacen") || RUTAS_EXTRA_ALMACEN.includes(location.pathname);
  if (rol === "almacen" && !rutaAlmacen) {
    return <Navigate to="/panel/almacen" replace />;
  }
  return children;
}
