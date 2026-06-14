import { useState } from "react";
import { Outlet } from "react-router-dom";
import { Menu, X } from "lucide-react";
import Sidebar from "./Sidebar";
import Logo from "./ui/Logo";
import Topbar from "./Topbar";

// Estructura del panel: barra lateral fija en escritorio y, en móvil/tablet,
// un cajón (drawer) que se abre con el botón de menú. El contenido de cada
// página se pinta en el Outlet sobre el fondo "canvas".
export default function LayoutAdmin() {
  const [abierto, setAbierto] = useState(false);

  return (
    <div className="flex h-screen bg-slate-50">
      {/* Sidebar de escritorio */}
      <div className="hidden lg:block">
        <Sidebar />
      </div>

      {/* Sidebar móvil (drawer) + fondo oscuro */}
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
        {/* Barra superior solo en móvil para abrir el menú */}
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

        {/* Barra superior de escritorio */}
        <Topbar />

        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
