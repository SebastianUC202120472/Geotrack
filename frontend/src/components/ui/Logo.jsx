import { useState } from "react";
import logoUrl from "../../assets/logo.png";
// Logo de la empresa: ícono (empaquetado con hash por Vite; monograma si falla) + nombre y
// subtítulo. Importar el asset evita problemas de caché del navegador (URL versionada por build).
// "light" = true sobre fondo oscuro (sidebar).
export default function Logo({ light = false, wordmark = true, className = "" }) {
  const [falla, setFalla] = useState(false);
  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      {!falla ? (
        <img src={logoUrl} alt="GeoTrack" className="h-9 w-auto" onError={() => setFalla(true)} />
      ) : (
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-lg font-bold text-white">G</span>
      )}
      {wordmark && (
        <div className="leading-tight">
          <p className={`text-lg font-bold tracking-tight ${light ? "text-white" : "text-slate-900"}`}>GeoTrack</p>
          <p className={`text-[11px] ${light ? "text-slate-400" : "text-slate-500"}`}>SAVA S.A.C</p>
        </div>
      )}
    </div>
  );
}
