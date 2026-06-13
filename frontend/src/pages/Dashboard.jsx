import Header from "../components/Header";
import DashboardCards from "../components/DashboardCards";
import EstadoSistema from "../components/EstadoSistema";
import UploadPedidos from "../components/UploadPedidos";
import HistorialImportaciones from "../components/HistorialImportaciones";

export default function Dashboard() {
  return (
    <main className="flex-1 overflow-y-auto p-6 space-y-6">
      <Header titulo="Dashboard" subtitulo="Resumen operativo de SIOL-SAVA" />
      <DashboardCards />

      <div className="grid lg:grid-cols-2 gap-6">
        <EstadoSistema />
        <UploadPedidos />
      </div>

      <HistorialImportaciones />
    </main>
  );
}
