// Bloque esqueleto para estados de carga. Recibe className y rounded.
export default function Skeleton({ className = "", rounded = "rounded-lg" }) {
  return <div aria-hidden="true" className={`skeleton ${rounded} ${className}`} />;
}

// Atajo: tarjeta KPI en carga (misma silueta que StatCard).
export function SkeletonStat() {
  return (
    <div className="bg-white border border-slate-200 rounded-card shadow-card p-5">
      <div className="flex items-start justify-between">
        <Skeleton className="h-3 w-20" />
        <Skeleton className="h-9 w-9" rounded="rounded-chip" />
      </div>
      <Skeleton className="mt-4 h-8 w-16" />
      <Skeleton className="mt-3 h-1.5 w-full" rounded="rounded-full" />
    </div>
  );
}
