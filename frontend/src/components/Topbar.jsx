import { useEffect, useState } from "react";
import { User } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { obtenerResumen, listarRecojosAlmacen } from "../services/api";
import Modal from "./ui/Modal";
import MiPerfil from "./MiPerfil";

// Barra superior: indicador de conexión y botón de perfil. Sin props.
export default function Topbar() {
  const { rol } = useAuth();
  const [enLinea, setEnLinea] = useState(null);
  const [ultimoOk, setUltimoOk] = useState(null);
  const [perfilAbierto, setPerfilAbierto] = useState(false);
  const [ahora, setAhora] = useState(() => Date.now());

  const endpoint = rol === "almacen" ? "/almacen/recojos" : "/dashboard/resumen";

  // Sondea el backend cada 20 s y al recuperar foco. Recibe: rol actual.
  useEffect(() => {
    let activo = true;
    const sondear = rol === "almacen" ? listarRecojosAlmacen : obtenerResumen;
    const comprobar = () =>
      sondear()
        .then(() => {
          if (!activo) return;
          setEnLinea(true);
          setUltimoOk(Date.now());
        })
        .catch(() => activo && setEnLinea(false));

    comprobar();
    const id = setInterval(comprobar, 20000);
    const alEnfocar = () => comprobar();
    window.addEventListener("focus", alEnfocar);
    return () => {
      activo = false;
      clearInterval(id);
      window.removeEventListener("focus", alEnfocar);
    };
  }, [rol]);

  // Avanza el reloj cada segundo para actualizar el tooltip sin re-sondear.
  useEffect(() => {
    const id = setInterval(() => setAhora(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  const segundosDesdeOk = ultimoOk ? Math.max(0, Math.floor((ahora - ultimoOk) / 1000)) : null;
  const ultimaVerif =
    segundosDesdeOk === null
      ? "—"
      : segundosDesdeOk < 60
      ? `hace ${segundosDesdeOk}s`
      : `hace ${Math.floor(segundosDesdeOk / 60)} min`;

  const estado =
    enLinea === null
      ? { txt: "Conectando…", cls: "bg-slate-100 text-slate-500", dot: "bg-slate-400" }
      : enLinea
      ? { txt: "En línea", cls: "bg-success-soft text-success-strong", dot: "bg-success" }
      : { txt: "Sin conexión", cls: "bg-danger-soft text-danger-strong", dot: "bg-danger" };

  return (
    <header className="hidden lg:flex items-center justify-end gap-3 border-b border-warm-200 bg-white px-8 py-3">
      {enLinea === null ? (
        <span className="inline-flex items-center gap-2 rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-700">
          Actualizando <span className="updating-bar h-2 w-12 rounded-full" />
        </span>
      ) : (
        <div className="group relative">
          <span
            className={`inline-flex cursor-default items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ${estado.cls}`}
          >
            <span className={`h-2 w-2 rounded-full ${estado.dot} ${enLinea ? "live-dot text-success" : ""}`} />
            {estado.txt}
          </span>
          <div
            role="tooltip"
            className="pointer-events-none absolute right-0 top-full z-50 mt-2 w-64 origin-top-right scale-95 rounded-xl border border-slate-200 bg-white p-3 text-left text-xs opacity-0 shadow-xl transition-all duration-150 group-hover:scale-100 group-hover:opacity-100"
          >
            <p className="mb-2 font-semibold text-slate-900">
              {enLinea ? "Conexión verificada" : "Sin respuesta del servidor"}
            </p>
            {enLinea ? (
              <ul className="space-y-1 text-slate-600">
                <li className="flex items-center gap-1.5"><span className="text-success">✓</span> Backend conectado</li>
                <li className="flex items-center gap-1.5"><span className="text-success">✓</span> Base de datos</li>
                <li className="mt-1 text-slate-500">Última verificación: {ultimaVerif}</li>
              </ul>
            ) : (
              <ul className="space-y-1 text-slate-600">
                <li className="flex items-center gap-1.5"><span className="text-danger">✕</span> Backend sin respuesta</li>
                <li className="mt-1 text-slate-500">Último contacto OK: {ultimaVerif}</li>
                <li className="text-slate-500">Reintentando cada 20 s…</li>
              </ul>
            )}
            <p className="mt-2 truncate border-t border-slate-100 pt-2 font-mono text-[11px] text-slate-400">
              {endpoint}
            </p>
          </div>
        </div>
      )}

      <button
        onClick={() => setPerfilAbierto(true)}
        aria-label="Mi perfil"
        title="Mi perfil"
        className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-600 text-white transition-colors hover:bg-brand-700"
      >
        <User size={18} />
      </button>

      <Modal open={perfilAbierto} onClose={() => setPerfilAbierto(false)} variant="center">
        <MiPerfil onCerrar={() => setPerfilAbierto(false)} />
      </Modal>
    </header>
  );
}
