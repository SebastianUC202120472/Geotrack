import {
  LayoutDashboard,
  Package,
  Layers3,
  Route as RouteIcon,
  MapPinned,
  Mail,
  Inbox,
  Truck,
  Users,
  Building2,
  UserCog,
  SlidersHorizontal,
  Radar,
  MapPin,
  Search,
  AlertTriangle,
  Wrench,
  LogOut,
} from "lucide-react";
import { useEffect, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { contadorIncidencias } from "../services/api";
import Logo from "./ui/Logo";

// Menú agrupado por bloques de trabajo. Cada entrada apunta a una pantalla que
// consume un endpoint real del admin. (Las funciones de la app móvil del
// conductor no viven aquí.)
const secciones = [
  {
    titulo: "Operación",
    items: [
      { icon: LayoutDashboard, label: "Dashboard", path: "/" },
      { icon: Package, label: "Pedidos", path: "/pedidos" },
      { icon: Layers3, label: "Agrupación por Zonas", path: "/agrupacion" },
      { icon: MapPinned, label: "Resolver Direcciones", path: "/direcciones" },
      { icon: RouteIcon, label: "Asignación de Rutas", path: "/asignacion-bloque" },
      { icon: Mail, label: "Bandeja de Solicitudes", path: "/bandeja" },
      { icon: Inbox, label: "Recojos", path: "/recojos" },
    ],
  },
  {
    titulo: "Flota",
    items: [
      { icon: Truck, label: "Flota de Vehículos", path: "/flota" },
      { icon: Users, label: "Conductores", path: "/conductores" },
      { icon: Building2, label: "Clientes", path: "/clientes" },
      { icon: Radar, label: "Seguimiento", path: "/seguimiento" },
      { icon: MapPin, label: "Seguimiento de Conductores", path: "/seguimiento-conductores" },
    ],
  },
  {
    titulo: "Administración",
    items: [
      { icon: UserCog, label: "Usuarios", path: "/usuarios" },
      { icon: SlidersHorizontal, label: "Parámetros", path: "/parametros" },
    ],
  },
  {
    titulo: "Incidencias",
    items: [
      { icon: Wrench, label: "Auxilio Mecánico", path: "/auxilio" },
      { icon: AlertTriangle, label: "Reportes", path: "/reportes" },
    ],
  },
  {
    titulo: "Consulta",
    items: [
      { icon: Search, label: "Trazabilidad", path: "/trazabilidad" },
    ],
  },
];

export default function Sidebar({ onNavigate }) {
  const navigate = useNavigate();
  const { cerrarSesion } = useAuth();

  const [abiertas, setAbiertas] = useState(0);
  // Contador de incidencias abiertas para el aviso (refresco silencioso cada 20 s).
  useEffect(() => {
    let activo = true;
    const traer = () => contadorIncidencias().then((d) => activo && setAbiertas(d.abiertas)).catch(() => {});
    traer();
    const id = setInterval(traer, 20000);
    return () => { activo = false; clearInterval(id); };
  }, []);

  const salir = () => {
    cerrarSesion();
    navigate("/login", { replace: true });
  };

  return (
    <aside className="flex h-full w-72 flex-col border-r border-[#222b38] bg-[#1f2733] text-slate-300">
      <div className="px-6 py-5 border-b border-[#2b3543]">
        <Logo light />
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {secciones.map((seccion) => (
          <div key={seccion.titulo}>
            <p className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
              {seccion.titulo}
            </p>
            <div className="space-y-1">
              {seccion.items.map(({ icon: Icon, label, path }) => (
                <NavLink
                  key={path}
                  to={path}
                  end={path === "/"}
                  onClick={onNavigate}
                  className={({ isActive }) =>
                    `group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all ${
                      isActive
                        ? "bg-gradient-to-r from-brand-600 to-brand-700 text-white shadow-[0_4px_12px_rgba(37,99,235,0.35)]"
                        : "text-slate-300 hover:bg-slate-800 hover:text-white"
                    }`
                  }
                >
                  <Icon size={18} />
                  <span>{label}</span>
                  {/* Chip rojo cuando hay incidencias abiertas sin atender */}
                  {label === "Auxilio Mecánico" && abiertas > 0 && (
                    <span className="ml-auto rounded-full bg-danger px-2 py-0.5 text-[11px] font-bold text-white">{abiertas}</span>
                  )}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>

      <div className="border-t border-slate-800 p-3">
        <button
          onClick={salir}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-slate-800 py-2.5 text-sm font-semibold text-slate-200 transition-colors hover:bg-danger hover:text-white"
        >
          <LogOut size={18} />
          Cerrar sesión
        </button>
      </div>
    </aside>
  );
}
