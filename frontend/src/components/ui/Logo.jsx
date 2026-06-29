import { useState } from "react";
import logoUrl from "../../assets/logo.png";

// Clases por tamaño: imagen/monograma y textos. "md" = uso normal (sidebar/header); "lg" = login.
const TAMANOS = {
  md: { gap: "gap-2.5", img: "h-9", chip: "h-9 w-9 rounded-xl text-lg", titulo: "text-lg", sub: "text-[11px]" },
  lg: { gap: "gap-3.5", img: "h-16", chip: "h-16 w-16 rounded-2xl text-3xl", titulo: "text-3xl", sub: "text-sm" },
};

// Logo de la empresa: ícono (empaquetado con hash por Vite; monograma si falla) + nombre y
// subtítulo. Importar el asset evita problemas de caché del navegador (URL versionada por build).
// "light" = true sobre fondo oscuro (sidebar). "size" = "md" (defecto) | "lg" (login).
export default function Logo({ light = false, wordmark = true, size = "md", className = "" }) {
  const [falla, setFalla] = useState(false);
  const t = TAMANOS[size] || TAMANOS.md;
  return (
    <div className={`flex items-center ${t.gap} ${className}`}>
      {!falla ? (
        <img src={logoUrl} alt="GeoTrack" className={`${t.img} w-auto`} onError={() => setFalla(true)} />
      ) : (
        <span className={`flex ${t.chip} items-center justify-center bg-brand-600 font-bold text-white`}>G</span>
      )}
      {wordmark && (
        <div className="leading-tight">
          <p className={`${t.titulo} font-bold tracking-tight ${light ? "text-white" : "text-slate-900"}`}>GeoTrack</p>
          <p className={`${t.sub} ${light ? "text-slate-400" : "text-slate-500"}`}>SAVA S.A.C</p>
        </div>
      )}
    </div>
  );
}
