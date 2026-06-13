import {
  LayoutDashboard,
  FileSpreadsheet,
  MapPinned,
  Layers3,
  Truck,
  History,
  LogOut,
  Navigation

} from "lucide-react";

import {
  NavLink,
  useNavigate
} from "react-router-dom";

export default function Sidebar() {

  const navigate = useNavigate();

const menus = [
  {
    icon: LayoutDashboard,
    label: "Dashboard",
    path: "/",
  },
  {
    icon: FileSpreadsheet,
    label: "Importar Pedidos",
    path: "/importar",
  },
  {
    icon: Layers3,
    label: "Agrupación",
    path: "/agrupacion",
  },
  {
    icon: MapPinned,
    label: "Geocodificación",
    path: "/geocodificacion",
  },
  {
    icon: Truck,
    label: "Flota",
    path: "/flota",
  },
  {
    icon: Truck,
    label: "Asignación de Rutas",
    path: "/asignacion-bloque",
  },
  {
  icon: Navigation,
  label: "Optimización VRP",
  path: "/vrp",
},
 {
    icon: History,
    label: "Manifiestos",
    path: "/admin/manifiestos",
  },
  
  
  
];
  

 const cerrarSesion = () => {
  localStorage.removeItem("admin_token");
  window.location.href = "/login";
};

  return (
    <aside className="w-72 bg-slate-950 text-white flex flex-col border-r border-slate-800">

      <div className="p-6 border-b border-slate-800">
        <h1 className="text-3xl font-bold">
          GEOTRACK
        </h1>

        <p className="text-slate-400 text-sm">
          SIOL - SAVA Admin
        </p>
      </div>

      <nav className="flex-1 p-4 space-y-2">

        {menus.map((item) => {

          const Icon = item.icon;

          return (
            <NavLink
              key={item.label}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 p-3 rounded-xl transition-all ${
                  isActive
                    ? "bg-blue-600"
                    : "hover:bg-slate-800"
                }`
              }
            >
              <Icon size={20} />
              <span>{item.label}</span>
            </NavLink>
          );

        })}

      </nav>

      <div className="p-4 border-t border-slate-800">

        <button
          onClick={cerrarSesion}
          className="w-full flex items-center justify-center gap-2 bg-red-600 py-3 rounded-xl hover:bg-red-700"
        >
          <LogOut size={18} />
          Cerrar Sesión
        </button>

      </div>

    </aside>
  );
}