import { Routes, Route, Navigate } from "react-router-dom";

import LayoutAdmin from "./components/LayoutAdmin";
import ProtectedRoute from "./components/ProtectedRoute";

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import ImportarPedidos from "./pages/ImportarPedidos";
import Pedidos from "./pages/Pedidos";
import AgrupacionZonas from "./pages/AgrupacionZonas";
import AsignacionBloque from "./pages/AsignacionBloque";
import Direcciones from "./pages/Direcciones";
import Bandeja from "./pages/Bandeja";
import Flota from "./pages/Flota";
import Conductores from "./pages/Conductores";
import Clientes from "./pages/Clientes";
import Usuarios from "./pages/Usuarios";
import Parametros from "./pages/Parametros";
import Seguimiento from "./pages/Seguimiento";
import SeguimientoConductores from "./pages/SeguimientoConductores";
import Reportes from "./pages/Reportes";
import AuxilioMecanico from "./pages/AuxilioMecanico";
import Devueltos from "./pages/Devueltos";
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
        <Route path="/pedidos" element={<Pedidos />} />
        <Route path="/agrupacion" element={<AgrupacionZonas />} />
        <Route path="/asignacion-bloque" element={<AsignacionBloque />} />
        <Route path="/direcciones" element={<Direcciones />} />
        <Route path="/bandeja" element={<Bandeja />} />
        <Route path="/flota" element={<Flota />} />
        <Route path="/conductores" element={<Conductores />} />
        <Route path="/clientes" element={<Clientes />} />
        <Route path="/usuarios" element={<Usuarios />} />
        <Route path="/parametros" element={<Parametros />} />
        <Route path="/seguimiento" element={<Seguimiento />} />
        <Route path="/seguimiento-conductores" element={<SeguimientoConductores />} />
        <Route path="/reportes" element={<Reportes />} />
        <Route path="/auxilio" element={<AuxilioMecanico />} />
        <Route path="/devueltos" element={<Devueltos />} />
        <Route path="/trazabilidad" element={<Trazabilidad />} />
      </Route>

      {/* Cualquier ruta desconocida vuelve al inicio. */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
