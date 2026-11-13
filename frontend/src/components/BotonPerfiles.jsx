import { UserPlus } from "lucide-react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

// Botón "Agregar perfil" junto a la foto de perfil: abre Usuarios del Panel, donde se crean y
// administran las cuentas del personal. Solo lo ve el administrador. Recibe compacto (true = solo icono).
export default function BotonPerfiles({ compacto = false }) {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const { rol } = useAuth();
  if (rol !== "admin") return null;
  const activo = pathname === "/panel/usuarios";
  return (
    <button
      type="button"
      onClick={() => navigate("/panel/usuarios")}
      aria-label="Agregar perfil"
      title="Agregar o administrar los perfiles del panel"
      aria-current={activo ? "page" : undefined}
      className={`group inline-flex h-9 items-center gap-2 rounded-full border text-sm font-semibold transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md active:translate-y-0 active:scale-95 ${
        compacto ? "w-9 justify-center" : "px-3.5"
      } ${activo ? "border-brand-600 bg-brand-50 text-brand-700" : "border-slate-200 bg-white text-slate-700 hover:border-brand-300 hover:text-brand-700"}`}
    >
      <UserPlus size={17} className="transition-transform duration-300 group-hover:scale-110 group-hover:-rotate-6" />
      {!compacto && <span>Agregar perfil</span>}
    </button>
  );
}
