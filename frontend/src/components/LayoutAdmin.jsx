import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";

// Estructura del panel: barra lateral fija + área de contenido donde se pinta
// la página activa (Outlet). El login NO usa este layout, por eso el Sidebar
// ya no aparece en la pantalla de inicio de sesión.
export default function LayoutAdmin() {
  return (
    <div className="flex h-screen bg-slate-100">
      <Sidebar />
      <div className="flex-1 overflow-y-auto">
        <Outlet />
      </div>
    </div>
  );
}
