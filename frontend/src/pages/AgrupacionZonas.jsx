import { useEffect, useState } from "react";
import { RefreshCw, MapPinned, Package, Layers3 } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import StatCard from "../components/ui/StatCard";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import DistrictCard from "../components/DistrictCard";
import { listarZonas } from "../services/api";

export default function AgrupacionZonas() {
  const [zonas, setZonas] = useState([]);
  const [cargando, setCargando] = useState(true);

  const cargar = async () => {
    setCargando(true);
    try {
      const res = await listarZonas();
      setZonas(res.zonas_operativas || []);
    } catch (err) {
      console.error("Error al cargar zonas:", err.message);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargar();
  }, []);

  const totalPedidos = zonas.reduce((acc, z) => acc + (z.total_pedidos || 0), 0);

  return (
    <div className="space-y-6 p-6 lg:p-8">
      <PageHeader
        titulo="Agrupación por Zonas"
        subtitulo="Los pedidos geocodificados se organizan automáticamente por distrito."
      >
        <Button variant="secondary" icon={RefreshCw} onClick={cargar}>Actualizar</Button>
      </PageHeader>

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard label="Distritos" value={zonas.length} icon={MapPinned} hint="Zonas detectadas" />
        <StatCard label="Pedidos" value={totalPedidos} icon={Package} hint="Listos para enrutar" />
        <StatCard label="Estado" value={zonas.length ? "Agrupado" : "—"} icon={Layers3} hint="Resultado del proceso" />
      </div>

      <Card title="Zonas operativas detectadas">
        {cargando ? (
          <p className="py-10 text-center text-sm text-slate-500">Cargando agrupación…</p>
        ) : zonas.length === 0 ? (
          <p className="py-10 text-center text-sm text-slate-400">
            Aún no hay zonas. Importa pedidos para que se agrupen por distrito.
          </p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {zonas.map((z) => (
              <DistrictCard key={z.distrito} distrito={z.distrito} pedidos={z.total_pedidos} />
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
