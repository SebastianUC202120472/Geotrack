// Previews del bloque "esqueleto" de carga. Solo se usan clases Tailwind que
// el sistema ya compila (h-8/h-3/h-1.5/w-20/w-full/rounded-*), porque el campo
// className es la única forma de dimensionar el componente.
import { Skeleton } from "frontend-geotrack";

const col = { display: "flex", flexDirection: "column" as const, gap: 12, maxWidth: 320 };

export const Lineas = () => (
  <div style={col}>
    <Skeleton className="h-8 w-20" />
    <Skeleton className="h-3 w-full" />
    <Skeleton className="h-3 w-full" />
    <Skeleton className="h-1.5 w-full" rounded="rounded-full" />
  </div>
);

export const Bloque = () => (
  <div style={col}>
    <Skeleton className="h-9 w-full" rounded="rounded-card" />
  </div>
);
