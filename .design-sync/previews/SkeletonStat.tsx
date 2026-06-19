// Preview del esqueleto de KPI: misma silueta que StatCard mientras cargan los
// datos del dashboard.
import { SkeletonStat } from "frontend-geotrack";

export const Carga = () => (
  <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(200px, 1fr))", gap: 16 }}>
    <SkeletonStat />
    <SkeletonStat />
  </div>
);
