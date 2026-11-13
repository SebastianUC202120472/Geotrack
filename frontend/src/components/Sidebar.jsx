import {
  Package,
  Route as RouteIcon,
  Mail,
  Truck,
  Users,
  Building2,
  MapPin,
  LogOut,
  PackageCheck,
  Undo2,
  ClipboardList,
  Wrench,
  BookText,
  AlertOctagon,
  Scale,
  ChevronRight,
} from "lucide-react";
import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import Logo from "./ui/Logo";
import ConfirmDialog from "./ui/ConfirmDialog";
import CampanaNotificaciones from "./CampanaNotificaciones";
import IconoAsistente from "../modulos/asistente/IconoAsistente";
import { useAsistenteDisponible } from "../modulos/asistente/estadoServicio";

// Secciones de navegacion agrupadas por rol. El resumen (Dashboard) se abre con el logo; la
// capacidad vive en Flota de Vehiculos, el seguimiento en Conductores, los parametros en el resumen,
// los contactos comerciales en Clientes y Usuarios en el boton "Agregar perfil" de la barra superior.
const secciones = [
  {
    titulo: "Operación",
    roles: ["admin"],
    items: [
      { icon: Package, label: "Pedidos", path: "/panel/pedidos" },
      { icon: RouteIcon, label: "Asignación de Rutas", path: "/panel/asignacion-bloque" },
      { icon: Mail, label: "Bandeja de Solicitudes", path: "/panel/bandeja" },
      { icon: IconoAsistente, label: "Asistente IA", path: "/panel/asistente", asistente: true },
    ],
  },
  {
    titulo: "Flota",
    roles: ["admin"],
    items: [
      { icon: Truck, label: "Flota de Vehículos", path: "/panel/flota" },
      { icon: Users, label: "Conductores", path: "/panel/conductores" },
      { icon: Building2, label: "Clientes", path: "/panel/clientes" },
    ],
  },
  {
    titulo: "Trazabilidad",
    roles: ["admin"],
    items: [
      { icon: ClipboardList, label: "Reportes de pedido", path: "/panel/reportes" },
      { icon: Wrench, label: "Auxilio mecánico", path: "/panel/auxilio" },
      { icon: BookText, label: "Libro de Reclamaciones", path: "/panel/reclamos" },
    ],
  },
  {
    titulo: "Almacén",
    roles: ["almacen"],
    items: [
      { icon: RouteIcon, label: "Armar ruta de recojo", path: "/panel/almacen/recojos" },
      { icon: PackageCheck, label: "Ingreso a Almacén", path: "/panel/almacen" },
      { icon: AlertOctagon, label: "Pedidos observados", path: "/panel/almacen/observados" },
      { icon: Undo2, label: "Retornos de Ruta", path: "/panel/almacen/retornos" },
      { icon: MapPin, label: "Mapa de recojos", path: "/panel/almacen/mapa" },
      { icon: Scale, label: "Capacidad de Vehículos", path: "/panel/capacidad" }, // Consulta de solo lectura
      { icon: IconoAsistente, label: "Asistente IA", path: "/panel/asistente", asistente: true },
    ],
  },
];

// Barra lateral de navegacion. Recibe onNavigate (callback opcional al navegar).
export default function Sidebar({ onNavigate }) {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const { cerrarSesion, rol } = useAuth();
  // La entrada del asistente solo aparece si su servicio esta activo (igual que el boton flotante).
  const asistenteDisponible = useAsistenteDisponible(rol);
  const visibles = secciones
    .filter((s) => !s.roles || s.roles.includes(rol))
    .map((s) => ({ ...s, items: s.items.filter((i) => !i.asistente || asistenteDisponible) }));
  const [confirmandoSalida, setConfirmandoSalida] = useState(false);

  // Cierra la sesion tras confirmarla en el dialogo (C05-01). Sin input.
  const salir = () => {
    setConfirmandoSalida(false);
    cerrarSesion();
    navigate("/panel/login", { replace: true });
  };

  return (
    <aside className="flex h-full w-72 flex-col border-r border-[#222b38] bg-[#1f2733] text-slate-300">
      <div className="flex items-center gap-2 px-6 py-5 border-b border-[#2b3543]">
        <button
          type="button"
          onClick={() => { navigate("/panel"); onNavigate?.(); }}
          aria-label="Ir al resumen operativo"
          title="Resumen operativo"
          className={`group -m-1.5 flex cursor-pointer items-center gap-1 rounded-xl p-1.5 pr-2 transition-all duration-300 hover:bg-slate-800 hover:shadow-[0_0_0_1px_rgba(59,130,246,0.45),0_0_18px_rgba(37,99,235,0.35)] active:scale-95 ${pathname === "/panel" ? "bg-slate-800" : ""}`}
        >
          {/* Al pasar el mouse el logo da un pequeño salto y aparece una flecha: invita a hacer clic. */}
          <Logo
            light
            className="[&_img]:transition-transform [&_img]:duration-500 [&_img]:ease-[cubic-bezier(.34,1.56,.64,1)] motion-safe:group-hover:[&_img]:-rotate-12 motion-safe:group-hover:[&_img]:scale-110"
          />
          <ChevronRight
            size={16}
            aria-hidden="true"
            className="-translate-x-1 text-brand-400 opacity-0 transition-all duration-300 group-hover:translate-x-0 group-hover:opacity-100"
          />
        </button>
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
                  className={`group relative flex w-full items-center gap-3 overflow-hidden rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-300 active:scale-[0.98] ${
                    pathname === path
                      ? "bg-gradient-to-r from-brand-600 to-brand-700 text-white shadow-[0_4px_12px_rgba(37,99,235,0.35)]"
                      : "text-slate-300 hover:bg-slate-800 hover:text-white"
                  }`}
                >
                  {/* Al pasar el mouse: barra de acento a la izquierda, icono que se inclina y texto que se desliza */}
                  {pathname !== path && (
                    <span aria-hidden="true" className="absolute left-0 top-1/2 h-0 w-1 -translate-y-1/2 rounded-r-full bg-brand-400 transition-all duration-300 group-hover:h-6" />
                  )}
                  <Icon size={18} className="shrink-0 transition-transform duration-300 group-hover:-rotate-6 group-hover:scale-115" />
                  <span className="transition-transform duration-300 group-hover:translate-x-1">{label}</span>
                </button>
              ))}
            </div>
          </div>
        ))}
      </nav>

      <div className="border-t border-slate-800 p-3">
        <button
          onClick={() => setConfirmandoSalida(true)}
          className="group flex w-full items-center justify-center gap-2 rounded-lg bg-slate-800 py-2.5 text-sm font-semibold text-slate-200 transition-all duration-300 hover:bg-danger hover:text-white active:scale-[0.98]"
        >
          <LogOut size={18} className="transition-transform duration-300 group-hover:translate-x-1" />
          Cerrar sesión
        </button>
      </div>

      <ConfirmDialog
        open={confirmandoSalida}
        titulo="¿Cerrar sesión?"
        mensaje="Tendrás que volver a ingresar tu correo y contraseña para usar el panel."
        textoConfirmar="Cerrar sesión"
        tono="danger"
        icono={LogOut}
        onConfirmar={salir}
        onCancelar={() => setConfirmandoSalida(false)}
      />
    </aside>
  );
}
