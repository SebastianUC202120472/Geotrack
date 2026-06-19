import { ResponsiveContainer } from "recharts";
import SectionCard from "./SectionCard";

// Envoltorio de gráfico: cabecera + área responsiva para recharts, con
// animación de entrada nativa de recharts (isAnimationActive).
// Entrada: title, subtitle, action, height (px, def 240), children (gráfico recharts).
export default function ChartCard({ title, subtitle, action, height = 240, children }) {
  return (
    <SectionCard title={title} subtitle={subtitle} action={action}>
      <div style={{ width: "100%", height }}>
        <ResponsiveContainer width="100%" height="100%">
          {children}
        </ResponsiveContainer>
      </div>
    </SectionCard>
  );
}
