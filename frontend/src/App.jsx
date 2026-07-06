import { lazy, Suspense } from "react";
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
import LibroReclamaciones from "./pages/LibroReclamaciones";

// Landing público (carga diferida: no forma parte del bundle del panel admin).
const Landing = lazy(() => import("./pages/landing/Landing"));
// Portal de clientes (carga diferida, igual que el Landing).
const Portal = lazy(() => import("./pages/portal/Portal"));

// Rutas: "/" es el landing público de SAVA; "/portal" es el portal de clientes;
// /login redirige al login del panel; el panel completo vive bajo /panel;
// cualquier ruta desconocida vuelve a "/".
export default function App() {
  return (
    <Routes>
      <Route
        path="/"
        element={
          <Suspense fallback={null}>
            <Landing />
          </Suspense>
        }
      />
      <Route
        path="/portal"
        element={
          <Suspense fallback={null}>
            <Portal />
          </Suspense>
        }
      />
      <Route path="/login" element={<Navigate to="/panel/login" replace />} />
      <Route path="/panel/login" element={<Login />} />

      <Route
        path="/panel"
        element={
          <ProtectedRoute>
            <LayoutAdmin />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="pedidos" element={<Pedidos />} />
        <Route path="agrupacion" element={<AgrupacionZonas />} />
        <Route path="asignacion-bloque" element={<AsignacionBloque />} />
        <Route path="bandeja" element={<Bandeja />} />
        <Route path="flota" element={<Flota />} />
        <Route path="conductores" element={<Conductores />} />
        <Route path="clientes" element={<Clientes />} />
        <Route path="usuarios" element={<Usuarios />} />
        <Route path="parametros" element={<Parametros />} />
        <Route path="seguimiento-conductores" element={<SeguimientoConductores />} />
        <Route path="reportes" element={<ReportesPedido />} />
        <Route path="auxilio" element={<AuxilioMecanico />} />
        <Route path="reclamos" element={<LibroReclamaciones />} />
        <Route path="notificaciones" element={<Notificaciones />} />
        <Route path="almacen" element={<IngresoAlmacen />} />
        <Route path="almacen/retornos" element={<RetornosAlmacen />} />
        <Route path="almacen/recojos" element={<ArmarRutaRecojo />} />
        <Route path="almacen/mapa" element={<MapaRecojos />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
