import { useEffect, useState } from "react";
import { User, X, Mail, IdCard, Phone, Briefcase, ShieldCheck, KeyRound, AlertTriangle, CheckCircle2 } from "lucide-react";
import { obtenerMiPerfil, cambiarMiContrasena } from "../services/api";
import { validarPassword } from "../utils/validaciones";
import PasswordInput from "./ui/PasswordInput";
import Button from "./ui/Button";

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

// Formulario para cambiar la contrasena propia (pide la actual). Recibe onListo (fn al terminar).
function CambiarClave({ onListo }) {
  const [actual, setActual] = useState("");
  const [nueva, setNueva] = useState("");
  const [repetir, setRepetir] = useState("");
  const [error, setError] = useState("");
  const [guardando, setGuardando] = useState(false);
  const [ok, setOk] = useState(false);

  // Valida y envia el cambio de contrasena. Recibe el evento del formulario.
  const guardar = async (e) => {
    e.preventDefault();
    const problema = !actual ? "Escribe tu contraseña actual"
      : validarPassword(nueva) || (nueva !== repetir ? "Las contraseñas nuevas no coinciden" : "");
    if (problema) { setError(problema); return; }
    setGuardando(true);
    setError("");
    try {
      await cambiarMiContrasena(actual, nueva);
      setOk(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setGuardando(false);
    }
  };

  if (ok) {
    return (
      <div className="mt-6 space-y-4">
        <div className="flex items-start gap-3 rounded-xl bg-success-soft px-4 py-3 text-sm text-success-strong">
          <CheckCircle2 size={20} className="shrink-0" />
          <span>Contraseña actualizada. Úsala la próxima vez que inicies sesión.</span>
        </div>
        <Button block onClick={() => onListo(true)}>Listo</Button>
      </div>
    );
  }

  return (
    <form onSubmit={guardar} noValidate className="mt-6 space-y-4">
      <PasswordInput label="Contraseña actual" value={actual} autoComplete="current-password"
        onChange={(e) => { setActual(e.target.value); setError(""); }} />
      <PasswordInput label="Nueva contraseña" value={nueva} autoComplete="new-password"
        onChange={(e) => { setNueva(e.target.value); setError(""); }}
        hint="8+, con mayúscula, minúscula, número y carácter especial" />
      <PasswordInput label="Repite la nueva contraseña" value={repetir} autoComplete="new-password"
        onChange={(e) => { setRepetir(e.target.value); setError(""); }} />
      {error && <p className="rounded-xl bg-danger-soft px-4 py-3 text-sm text-danger-strong">{error}</p>}
      <div className="flex gap-2">
        <Button type="button" variant="secondary" block onClick={() => onListo(false)} disabled={guardando}>Cancelar</Button>
        <Button type="submit" icon={KeyRound} block disabled={guardando}>{guardando ? "Guardando…" : "Cambiar"}</Button>
      </div>
    </form>
  );
}

// Modal con los datos del usuario autenticado y el cambio de su contrasena. Recibe onCerrar (fn).
export default function MiPerfil({ onCerrar }) {
  const [perfil, setPerfil] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);
  const [cambiando, setCambiando] = useState(false);

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
      ) : cambiando ? (
        <CambiarClave
          onListo={(cambio) => {
            setCambiando(false);
            if (cambio) setPerfil((p) => ({ ...p, clave_por_defecto: false }));
          }}
        />
      ) : (
        <div className="mt-6 space-y-3">
          {perfil.clave_por_defecto && (
            <div className="flex items-start gap-2 rounded-xl bg-warning-soft px-3.5 py-3 text-sm text-warning-strong">
              <AlertTriangle size={18} className="mt-0.5 shrink-0" />
              <span>Tu cuenta sigue con la <b>contraseña de fábrica</b>, que es pública. Cámbiala ahora.</span>
            </div>
          )}
          <Dato icon={User} label="Nombre completo" value={perfil.nombre} />
          <div className="grid grid-cols-2 gap-3">
            <Dato icon={IdCard} label="DNI" value={perfil.dni} />
            <Dato icon={Phone} label="Teléfono" value={perfil.telefono} />
          </div>
          <Dato icon={Briefcase} label="Cargo" value={perfil.cargo} />
          <Dato icon={Mail} label="Correo" value={perfil.correo} />
          <Dato icon={ShieldCheck} label="Rol" value={etiquetaRol(perfil.rol)} />
          <Button variant="secondary" icon={KeyRound} block className="mt-2" onClick={() => setCambiando(true)}>
            Cambiar contraseña
          </Button>
        </div>
      )}
    </>
  );
}
