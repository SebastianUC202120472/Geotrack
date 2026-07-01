import { ResponsiveContainer } from "recharts";
import SectionCard from "./SectionCard";

// Envoltorio responsivo para graficos recharts. Recibe title, subtitle, action, height y children.
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
