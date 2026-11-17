// Administración del asistente de atención al cliente (Idea 2), solo para administradores:
// base de conocimiento editable, bandeja de conversaciones derivadas y métricas.
// Página del módulo cargada en diferido; el servicio valida el rol contra el núcleo.
import { BarChart3, BookOpen, Inbox } from "lucide-react";
import PageHeader from "../../../components/ui/PageHeader";
import { usePestanasPagina } from "../../../components/ui/PestanasPagina";
import TabBandeja from "./TabBandeja";
import TabConocimiento from "./TabConocimiento";
import TabMetricas from "./TabMetricas";

const VISTAS = [
  ["conocimiento", "Base de conocimiento", BookOpen],
  ["bandeja", "Bandeja", Inbox],
  ["metricas", "Métricas", BarChart3],
];

// Página de administración del asistente de atención. Sin props.
export default function PaginaAtencion() {
  const [vista, pestanas] = usePestanasPagina(VISTAS, "Secciones del asistente de atención");
  return (
    <div className="space-y-5 px-6 pb-6 pt-4 lg:px-8 lg:pb-8 lg:pt-5 animate-fade-in">
      <PageHeader titulo="Atención al cliente (IA)" />
      {pestanas}
      {vista === "conocimiento" && <TabConocimiento />}
      {vista === "bandeja" && <TabBandeja />}
      {vista === "metricas" && <TabMetricas />}
    </div>
  );
}
