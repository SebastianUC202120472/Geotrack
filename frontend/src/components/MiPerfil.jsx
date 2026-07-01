import { useEffect, useState } from "react";
import { User, X, Mail, IdCard, Phone, Briefcase, ShieldCheck } from "lucide-react";
import { obtenerMiPerfil } from "../services/api";

// Etiqueta legible del rol del panel.
const etiquetaRol = (r) =>
  r === "admin" ? "Administrador" : r === "almacen" ? "Almacén" : r || "—";

// Devuelve 1-2 iniciales en mayúscula a partir del nombre o correo del perfil.
function iniciales(perfil) {
  const base = perfil?.nombre?.trim() || perfil?.correo || "";
  const partes = base.split(/[\s@.]+/).filter(Boolean);
  if (partes.length === 0) return "?";
  if (partes.length === 1) return partes[0].slice(0, 2).toUpperCase();
  return (partes[0][0] + partes[1][0]).toUpperCase();
}

// Fila de dato (icono + etiqueta + valor) en modo solo lectura.
// Entrada: icon (componente lucide), label, value.
function Dato({ icon: Icon, label, value }) {
  return (
    <div className="flex items-center gap-3 rounded-xl bg-slate-50 px-4 py-3 text-sm">
      <Icon size={18} className="shrink-0 text-slate-400" />
      <div className="min-w-0">
        <p className="text-xs text-slate-400">{label}</p>
        <p className="truncate font-medium text-slate-700">{value || "—"}</p>
      </div>
    </div>
  );
}

// Modal de solo lectura con los datos del usuario autenticado. Recibe onCerrar (fn).
export default function MiPerfil({ onCerrar }) {
  const [perfil, setPerfil] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let activo = true;
    obtenerMiPerfil()
      .then((p) => activo && setPerfil(p))
      .catch((e) => activo && setError(e.message))
      .finally(() => activo && setCargando(false));
    return () => { activo = false; };
  }, []);

  return (
    <>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <span className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-600 text-sm font-bold text-white">
            {perfil ? iniciales(perfil) : <User size={22} />}
          </span>
          <div>
            <h2 className="font-bold text-slate-900">{perfil?.nombre || "Mi Perfil"}</h2>
            <p className="text-sm text-slate-500 nums">
              {perfil?.codigo ? `${perfil.codigo} · ` : ""}{etiquetaRol(perfil?.rol)}
            </p>
          </div>
        </div>
        <button onClick={onCerrar} aria-label="Cerrar" className="rounded-lg p-2 text-slate-500 hover:bg-slate-100">
          <X size={20} />
        </button>
      </div>

      {cargando ? (
        <p className="mt-6 text-center text-sm text-slate-500">Cargando perfil…</p>
      ) : error ? (
        <p className="mt-6 rounded-xl bg-danger-soft px-4 py-3 text-sm text-danger-strong">{error}</p>
      ) : (
        <div className="mt-6 space-y-3">
          <Dato icon={User} label="Nombre completo" value={perfil.nombre} />
          <div className="grid grid-cols-2 gap-3">
            <Dato icon={IdCard} label="DNI" value={perfil.dni} />
            <Dato icon={Phone} label="Teléfono" value={perfil.telefono} />
          </div>
          <Dato icon={Briefcase} label="Cargo" value={perfil.cargo} />
          <Dato icon={Mail} label="Correo" value={perfil.correo} />
          <Dato icon={ShieldCheck} label="Rol" value={etiquetaRol(perfil.rol)} />
        </div>
      )}
    </>
  );
}
