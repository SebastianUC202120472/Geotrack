import { Routes, Route } from "react-router-dom";

import Sidebar from "./components/Sidebar";
import "leaflet/dist/leaflet.css";
/* =========================
   PAGES
========================= */
import Dashboard from "./pages/Dashboard";
import ImportarPedidos from "./pages/ImportarPedidos";
import AgrupacionZonas from "./pages/AgrupacionZonas";
import Geocodificacion from "./pages/Geocodificacion";
import AsignacionBloque from "./pages/AsignacionBloque";
import EjecucionEnrutamiento from "./pages/EjecucionEnrutamiento";
import AdminManifiesto from './pages/AdminManifiesto';
import Flota from "./pages/Flota";
import Login from "./pages/Login";

export default function App() {
  return (
    <div className="flex h-screen bg-slate-950">

      <Sidebar />

      <div className="flex-1 overflow-y-auto">

        <Routes>

          {/* AUTH */}
          <Route path="/login" element={<Login />} />

          {/* DASHBOARD */}
          <Route path="/" element={<Dashboard />} />

          {/* CUS-15 / CUS-16 / CUS-17 */}
          <Route path="/importar" element={<ImportarPedidos />} />
          <Route path="/agrupacion" element={<AgrupacionZonas />} />
          <Route path="/geocodificacion" element={<Geocodificacion />} />

          {/* CUS-18 */}
          <Route path="/asignacion-bloque" element={<AsignacionBloque />} />

          {/* CUS-19 (VRP EJECUCIÓN) */}
          <Route path="/vrp" element={<EjecucionEnrutamiento />} />
          <Route path="/admin/manifiestos" element={<AdminManifiesto />} />
          {/* FLOTA */}
          <Route path="/flota" element={<Flota />} />

        </Routes>

      </div>
    </div>
  );
}