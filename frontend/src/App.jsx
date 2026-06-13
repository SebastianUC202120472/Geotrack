import { Routes, Route, Navigate } from "react-router-dom";

import LayoutAdmin from "./components/LayoutAdmin";
import ProtectedRoute from "./components/ProtectedRoute";

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import ImportarPedidos from "./pages/ImportarPedidos";
import AgrupacionZonas from "./pages/AgrupacionZonas";
import AsignacionBloque from "./pages/AsignacionBloque";
import Bandeja from "./pages/Bandeja";
import Flota from "./pages/Flota";
import Seguimiento from "./pages/Seguimiento";
import Trazabilidad from "./pages/Trazabilidad";

// Mapa de rutas del panel de administración.
// /login va suelto (sin barra lateral). Todo lo demás cuelga del layout del
// panel y está protegido: sin sesión, ProtectedRoute manda al login.
export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />

      <Route
        element={
          <ProtectedRoute>
            <LayoutAdmin />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Dashboard />} />
        <Route path="/importar" element={<ImportarPedidos />} />
        <Route path="/agrupacion" element={<AgrupacionZonas />} />
        <Route path="/asignacion-bloque" element={<AsignacionBloque />} />
        <Route path="/bandeja" element={<Bandeja />} />
        <Route path="/flota" element={<Flota />} />
        <Route path="/seguimiento" element={<Seguimiento />} />
        <Route path="/trazabilidad" element={<Trazabilidad />} />
      </Route>

      {/* Cualquier ruta desconocida vuelve al inicio. */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
