import {
  LayoutDashboard,
  Package,
  Layers3,
  Route as RouteIcon,
  Mail,
  Truck,
  Users,
  Building2,
  UserCog,
  SlidersHorizontal,
  MapPin,
  LogOut,
  PackageCheck,
  Undo2,
} from "lucide-react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Logo from "./ui/Logo";
import CampanaNotificaciones from "./CampanaNotificaciones";

// Menú agrupado por bloques de trabajo. Cada entrada apunta a una pantalla que
// consume un endpoint real del admin. (Las funciones de la app móvil del
// conductor no viven aquí.)
const secciones = [
  {
    titulo: "Operación",
    roles: ["admin"],
    items: [
      { icon: LayoutDashboard, label: "Dashboard", path: "/" },
      { icon: Package, label: "Pedidos", path: "/pedidos" },
      { icon: Layers3, label: "Agrupación por Zonas", path: "/agrupacion" },
      { icon: RouteIcon, label: "Asignación de Rutas", path: "/asignacion-bloque" },
      { icon: Mail, label: "Bandeja de Solicitudes", path: "/bandeja" },
    ],
  },
  {
    titulo: "Flota",
    roles: ["admin"],
    items: [
      { icon: Truck, label: "Flota de Vehículos", path: "/flota" },
      { icon: Users, label: "Conductores", path: "/conductores" },
      { icon: Building2, label: "Clientes", path: "/clientes" },
      { icon: MapPin, label: "Seguimiento de Conductores", path: "/seguimiento-conductores" },
    ],
  },
  {
    titulo: "Administración",
    roles: ["admin"],
    items: [
      { icon: UserCog, label: "Usuarios", path: "/usuarios" },
      { icon: SlidersHorizontal, label: "Parámetros", path: "/parametros" },
    ],
  },
  {
    titulo: "Almacén",
    roles: ["almacen"],
    items: [
      { icon: RouteIcon, label: "Armar ruta de recojo", path: "/almacen/recojos" },
      { icon: PackageCheck, label: "Ingreso a Almacén", path: "/almacen" },
      { icon: Undo2, label: "Retornos de Ruta", path: "/almacen/retornos" },
      { icon: MapPin, label: "Mapa de recojos", path: "/almacen/mapa" },
    ],
  },
];

export default function Sidebar({ onNavigate }) {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const { cerrarSesion, rol } = useAuth();
  const visibles = secciones.filter((s) => !s.roles || s.roles.includes(rol));

  const salir = () => {
    cerrarSesion();
    navigate("/login", { replace: true });
  };

  return (
    <aside className="flex h-full w-72 flex-col border-r border-[#222b38] bg-[#1f2733] text-slate-300">
      {/* Header: logo + campana de notificaciones (solo admin, con espacio flex) */}
      <div className="flex items-center gap-2 px-6 py-5 border-b border-[#2b3543]">
        <Logo light />
        {rol === "admin" && (
          <div className="ml-auto">
            <CampanaNotificaciones />
          </div>
        )}
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {visibles.map((seccion) => (
          <div key={seccion.titulo}>
            <p className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
              {seccion.titulo}
            </p>
            <div className="space-y-1">
              {seccion.items.map(({ icon: Icon, label, path }) => (
                <button
                  key={path}
                  onClick={() => { navigate(path); onNavigate?.(); }}
                  aria-current={pathname === path ? "page" : undefined}
                  className={`group flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all ${
                    pathname === path
                      ? "bg-gradient-to-r from-brand-600 to-brand-700 text-white shadow-[0_4px_12px_rgba(37,99,235,0.35)]"
                      : "text-slate-300 hover:bg-slate-800 hover:text-white"
                  }`}
                >
                  <Icon size={18} />
                  <span>{label}</span>
                </button>
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
