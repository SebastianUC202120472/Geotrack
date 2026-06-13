import { useState } from "react";

// Logo de la empresa. Intenta cargar la imagen desde public/logo.png; si aún no
// existe, muestra un monograma + wordmark como placeholder elegante.
//   -> Coloca tu archivo en  frontend/public/logo.png  (o logo.svg y cambia src).
//   -> Tamaño recomendado: alto ~40px, fondo transparente.
// "light" = true cuando va sobre fondo oscuro (sidebar); el texto se aclara.
export default function Logo({ light = false, wordmark = true, className = "" }) {
  const [falla, setFalla] = useState(false);

  if (!falla) {
    return (
      <img
        src="/logo.png"
        alt="GeoTrack"
        className={`h-9 w-auto ${className}`}
        onError={() => setFalla(true)}
      />
    );
  }

  return (
    <div className={`flex items-center gap-2.5 ${className}`}>
      <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-lg font-bold text-white">
        G
      </span>
      {wordmark && (
        <div className="leading-tight">
          <p className={`text-lg font-bold tracking-tight ${light ? "text-white" : "text-slate-900"}`}>
            GeoTrack
          </p>
          <p className={`text-[11px] ${light ? "text-slate-400" : "text-slate-500"}`}>
            SIOL · SAVA
          </p>
        </div>
      )}
    </div>
  );
}
