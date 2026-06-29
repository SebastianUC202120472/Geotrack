import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { obtenerResumen, listarRecojosAlmacen } from "../services/api";

// Barra superior de escritorio: indicador de conexión (verde si el backend
// responde). Entrada: ninguna (lee estado y auth).
export default function Topbar() {
  const { rol } = useAuth();
  const [enLinea, setEnLinea] = useState(null); // null = verificando

  // Revisa la conexión al montar y luego cada 20 s (y al volver el foco), para que
  // un arranque lento o un reinicio del backend se recupere solo sin recargar.
  // Sondea un endpoint que el rol actual pueda consultar (admin → resumen;
  // almacén → su lista de recojos) para que el indicador refleje la conexión real
  // y no un 403 de permisos.
  useEffect(() => {
    let activo = true;
    const sondear = rol === "almacen" ? listarRecojosAlmacen : obtenerResumen;
    const comprobar = () =>
      sondear()
        .then(() => activo && setEnLinea(true))
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

  const estado =
    enLinea === null
      ? { txt: "Conectando…", cls: "bg-slate-100 text-slate-500", dot: "bg-slate-400" }
      : enLinea
      ? { txt: "En línea", cls: "bg-success-soft text-success-strong", dot: "bg-success" }
      : { txt: "Sin conexión", cls: "bg-danger-soft text-danger-strong", dot: "bg-danger" };

  return (
    <header className="hidden lg:flex items-center justify-end gap-3 border-b border-warm-200 bg-white px-8 py-3">
      {enLinea === null ? (
        <span
          title="Verificando conexión…"
          className="inline-flex items-center gap-2 rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-700"
        >
          Actualizando <span className="updating-bar h-2 w-12 rounded-full" />
        </span>
      ) : (
        <span
          title={enLinea ? "Servidor y base de datos conectados" : "Sin respuesta del servidor"}
          className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ${estado.cls}`}
        >
          <span className={`h-2 w-2 rounded-full ${estado.dot} ${enLinea ? "live-dot text-success" : ""}`} />
          {estado.txt}
        </span>
      )}
    </header>
  );
}
