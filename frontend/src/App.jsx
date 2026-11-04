import { lazy, Suspense } from "react";
import { Routes, Route, Navigate } from "react-router-dom";

import LayoutAdmin from "./components/LayoutAdmin";
import ProtectedRoute from "./components/ProtectedRoute";

// Pantallas del panel en carga diferida (EX-19): cada una es su propio archivo y el paquete
// inicial solo trae el armazón. LayoutAdmin las envuelve en un Suspense.
const Login = lazy(() => import("./pages/Login"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Pedidos = lazy(() => import("./pages/Pedidos"));
const AgrupacionZonas = lazy(() => import("./pages/AgrupacionZonas"));
const AsignacionBloque = lazy(() => import("./pages/AsignacionBloque"));
const Bandeja = lazy(() => import("./pages/Bandeja"));
const Flota = lazy(() => import("./pages/Flota"));
const Conductores = lazy(() => import("./pages/Conductores"));
const Clientes = lazy(() => import("./pages/Clientes"));
const Usuarios = lazy(() => import("./pages/Usuarios"));
const Parametros = lazy(() => import("./pages/Parametros"));
const SeguimientoConductores = lazy(() => import("./pages/SeguimientoConductores"));
const IngresoAlmacen = lazy(() => import("./pages/IngresoAlmacen"));
const PedidosObservados = lazy(() => import("./pages/PedidosObservados"));
const RetornosAlmacen = lazy(() => import("./pages/RetornosAlmacen"));
const ArmarRutaRecojo = lazy(() => import("./pages/ArmarRutaRecojo"));
const MapaRecojos = lazy(() => import("./pages/MapaRecojos"));
const ReportesPedido = lazy(() => import("./pages/ReportesPedido"));
const AuxilioMecanico = lazy(() => import("./pages/AuxilioMecanico"));
const Notificaciones = lazy(() => import("./pages/Notificaciones"));
const LibroReclamaciones = lazy(() => import("./pages/LibroReclamaciones"));
const ContactosComerciales = lazy(() => import("./pages/ContactosComerciales"));

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
      <Route
        path="/panel/login"
        element={
          <Suspense fallback={null}>
            <Login />
          </Suspense>
        }
      />

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
        <Route path="contactos" element={<ContactosComerciales />} />
        <Route path="notificaciones" element={<Notificaciones />} />
        <Route path="almacen" element={<IngresoAlmacen />} />
        <Route path="almacen/retornos" element={<RetornosAlmacen />} />
        <Route path="almacen/observados" element={<PedidosObservados />} />
        <Route path="almacen/recojos" element={<ArmarRutaRecojo />} />
        <Route path="almacen/mapa" element={<MapaRecojos />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
