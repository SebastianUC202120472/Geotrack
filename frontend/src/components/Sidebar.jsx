import {
  LayoutDashboard,
  FileSpreadsheet,
  Layers3,
  Route as RouteIcon,
  Truck,
  Radar,
  Search,
  LogOut,
} from "lucide-react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

// Menú del panel. Cada entrada apunta a una pantalla que consume un endpoint
// real del backend del admin. Las funciones de la app móvil del conductor
// (validación QR, evidencias, optimización con GPS) NO viven aquí.
const menu = [
  { icon: LayoutDashboard, label: "Dashboard", path: "/" },
  { icon: FileSpreadsheet, label: "Importar Pedidos", path: "/importar" },
  { icon: Layers3, label: "Agrupación por Zonas", path: "/agrupacion" },
  { icon: RouteIcon, label: "Asignación de Rutas", path: "/asignacion-bloque" },
  { icon: Truck, label: "Flota y Conductores", path: "/flota" },
  { icon: Radar, label: "Seguimiento", path: "/seguimiento" },
  { icon: Search, label: "Trazabilidad", path: "/trazabilidad" },
];

export default function Sidebar() {
  const navigate = useNavigate();
  const { cerrarSesion } = useAuth();

  const salir = () => {
    cerrarSesion();
    navigate("/login", { replace: true });
  };

  return (
    <aside className="w-72 bg-slate-950 text-white flex flex-col border-r border-slate-800">
      <div className="p-6 border-b border-slate-800">
        <h1 className="text-3xl font-bold">GEOTRACK</h1>
        <p className="text-slate-400 text-sm">SIOL - SAVA · Panel Admin</p>
      </div>

      <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
        {menu.map(({ icon: Icon, label, path }) => (
          <NavLink
            key={path}
            to={path}
            end={path === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 p-3 rounded-xl transition-all ${
                isActive ? "bg-blue-600" : "hover:bg-slate-800"
              }`
            }
          >
            <Icon size={20} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-slate-800">
        <button
          onClick={salir}
          className="w-full flex items-center justify-center gap-2 bg-red-600 py-3 rounded-xl hover:bg-red-700 transition-colors"
        >
          <LogOut size={18} />
          Cerrar Sesión
        </button>
      </div>
    </aside>
  );
}
