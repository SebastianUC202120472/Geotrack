import { Routes, Route, Navigate } from "react-router-dom";

import LayoutAdmin from "./components/LayoutAdmin";
import ProtectedRoute from "./components/ProtectedRoute";

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Pedidos from "./pages/Pedidos";
import AgrupacionZonas from "./pages/AgrupacionZonas";
import AsignacionBloque from "./pages/AsignacionBloque";
import Bandeja from "./pages/Bandeja";
import Flota from "./pages/Flota";
import Conductores from "./pages/Conductores";
import Clientes from "./pages/Clientes";
import Usuarios from "./pages/Usuarios";
import Parametros from "./pages/Parametros";
import SeguimientoConductores from "./pages/SeguimientoConductores";
import IngresoAlmacen from "./pages/IngresoAlmacen";
import RetornosAlmacen from "./pages/RetornosAlmacen";
import ArmarRutaRecojo from "./pages/ArmarRutaRecojo";
import MapaRecojos from "./pages/MapaRecojos";
import ReportesPedido from "./pages/ReportesPedido";
import AuxilioMecanico from "./pages/AuxilioMecanico";
import Notificaciones from "./pages/Notificaciones";

// Rutas del panel admin: /login libre, el resto protegido bajo LayoutAdmin.
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
        <Route path="/pedidos" element={<Pedidos />} />
        <Route path="/agrupacion" element={<AgrupacionZonas />} />
        <Route path="/asignacion-bloque" element={<AsignacionBloque />} />
        <Route path="/bandeja" element={<Bandeja />} />
        <Route path="/flota" element={<Flota />} />
        <Route path="/conductores" element={<Conductores />} />
        <Route path="/clientes" element={<Clientes />} />
        <Route path="/usuarios" element={<Usuarios />} />
        <Route path="/parametros" element={<Parametros />} />
        <Route path="/seguimiento-conductores" element={<SeguimientoConductores />} />
        <Route path="/reportes" element={<ReportesPedido />} />
        <Route path="/auxilio" element={<AuxilioMecanico />} />
        <Route path="/notificaciones" element={<Notificaciones />} />
        <Route path="/almacen" element={<IngresoAlmacen />} />
        <Route path="/almacen/retornos" element={<RetornosAlmacen />} />
        <Route path="/almacen/recojos" element={<ArmarRutaRecojo />} />
        <Route path="/almacen/mapa" element={<MapaRecojos />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
