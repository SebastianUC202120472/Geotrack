// Punto de entrada del kit de UI de GeoTrack para la sincronización con
// claude.ai/design. Reexporta los componentes reutilizables de
// frontend/src/components/ui como exportaciones con nombre, para que esbuild
// los empaquete en window.GeoTrackUI.<Componente>.
//
// No es código de la app: solo agrupa los componentes ya existentes. La app
// los importa directamente desde sus archivos; este barril existe únicamente
// para el empaquetado del sistema de diseño.
export { default as Badge, EstadoBadge } from "../frontend/src/components/ui/Badge.jsx";
export { default as Button } from "../frontend/src/components/ui/Button.jsx";
export { default as Card } from "../frontend/src/components/ui/Card.jsx";
export { default as Input } from "../frontend/src/components/ui/Input.jsx";
export { default as Logo } from "../frontend/src/components/ui/Logo.jsx";
export { default as Modal } from "../frontend/src/components/ui/Modal.jsx";
export { default as PageHeader } from "../frontend/src/components/ui/PageHeader.jsx";
export { default as PasswordInput } from "../frontend/src/components/ui/PasswordInput.jsx";
export { default as Skeleton, SkeletonStat } from "../frontend/src/components/ui/Skeleton.jsx";
export { default as StatCard } from "../frontend/src/components/ui/StatCard.jsx";
