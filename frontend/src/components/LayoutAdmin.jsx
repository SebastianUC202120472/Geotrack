import { useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { Menu, X } from "lucide-react";
import Sidebar from "./Sidebar";
import Logo from "./ui/Logo";
import Topbar from "./Topbar";

// Layout principal del panel: sidebar fijo en escritorio, drawer en móvil, Outlet como contenido.
export default function LayoutAdmin() {
  const [abierto, setAbierto] = useState(false);
  const { pathname } = useLocation();

  return (
    <div className="flex h-screen bg-canvas">
      <div className="hidden lg:block">
        <Sidebar />
      </div>


      {abierto && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div
            className="absolute inset-0 bg-slate-900/50"
            onClick={() => setAbierto(false)}
          />
          <div className="absolute inset-y-0 left-0">
            <Sidebar onNavigate={() => setAbierto(false)} />
          </div>
          <button
            onClick={() => setAbierto(false)}
            aria-label="Cerrar menú"
            className="absolute right-4 top-4 rounded-lg bg-white/10 p-2 text-white"
          >
            <X size={20} />
          </button>
        </div>
      )}

      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex items-center gap-3 border-b border-slate-200 bg-white px-4 py-3 lg:hidden">
          <button
            onClick={() => setAbierto(true)}
            aria-label="Abrir menú"
            className="rounded-lg p-2 text-slate-600 hover:bg-slate-100"
          >
            <Menu size={22} />
          </button>
          <Logo />
        </header>

        <Topbar />

        <main className="flex-1 overflow-y-auto bg-canvas">
          <div key={pathname} className="animate-fade-up">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
