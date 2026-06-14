import { useEffect, useState } from "react";
import { LogOut } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { obtenerResumen } from "../services/api";

// Barra superior de escritorio: indicador de conexión (verde si el backend
// responde) y botón de cerrar sesión. Entrada: ninguna (lee estado y auth).
export default function Topbar() {
  const navigate = useNavigate();
  const { cerrarSesion } = useAuth();
  const [enLinea, setEnLinea] = useState(null); // null = verificando

  useEffect(() => {
    obtenerResumen().then(() => setEnLinea(true)).catch(() => setEnLinea(false));
  }, []);

  const salir = () => {
    cerrarSesion();
    navigate("/login", { replace: true });
  };

  const estado =
    enLinea === null
      ? { txt: "Conectando…", cls: "bg-slate-100 text-slate-500", dot: "bg-slate-400" }
      : enLinea
      ? { txt: "En línea", cls: "bg-success-soft text-success-strong", dot: "bg-success" }
      : { txt: "Sin conexión", cls: "bg-danger-soft text-danger-strong", dot: "bg-danger" };

  return (
    <header className="hidden lg:flex items-center justify-end gap-3 border-b border-slate-200 bg-white px-8 py-3">
      <span className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ${estado.cls}`}>
        <span className={`h-2 w-2 rounded-full ${estado.dot}`} />
        {estado.txt}
      </span>
      <button
        onClick={salir}
        className="inline-flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100"
      >
        <LogOut size={16} />
        Salir
      </button>
    </header>
  );
}
