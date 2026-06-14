import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { RefreshCw, MapPinned, Clock, Truck } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import StatCard from "../components/ui/StatCard";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import DistrictCard from "../components/DistrictCard";
import { listarPedidos } from "../services/api";

// Agrupa los pedidos por distrito y, dentro de cada uno, cuenta pendientes y
// asignados. Solo interesan las zonas con trabajo por gestionar.
// Entrada: pedidos (array con `distrito` y `estado`).
// Salida: array de zonas { distrito, pendientes, asignados } con al menos un
// pendiente o asignado, ordenadas por la mayor cantidad de esos dos.
function agruparZonas(pedidos) {
  const mapa = new Map();
  for (const p of pedidos) {
    const clave = p.distrito || "";
    if (!mapa.has(clave)) mapa.set(clave, { distrito: clave, pendientes: 0, asignados: 0 });
    const z = mapa.get(clave);
    if (p.estado === "PENDIENTE") z.pendientes++;
    else if (p.estado === "ASIGNADO") z.asignados++;
  }
  return [...mapa.values()]
    .filter((z) => z.pendientes > 0 || z.asignados > 0)
    .sort((a, b) => b.pendientes + b.asignados - (a.pendientes + a.asignados));
}

export default function AgrupacionZonas() {
  const navigate = useNavigate();
  const [pedidos, setPedidos] = useState([]);
  const [cargando, setCargando] = useState(true);

  const cargar = async () => {
    setCargando(true);
    try {
      setPedidos(await listarPedidos());
    } catch (err) {
      console.error("Error al cargar zonas:", err.message);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargar();
  }, []);

  const zonas = useMemo(() => agruparZonas(pedidos), [pedidos]);
  const totalPendientes = zonas.reduce((acc, z) => acc + z.pendientes, 0);
  const totalAsignados = zonas.reduce((acc, z) => acc + z.asignados, 0);

  // Navega al listado de Pedidos filtrado por distrito (y opcionalmente estado).
  const irAPedidos = (distrito, estado) => {
    const params = new URLSearchParams();
    if (distrito) params.set("distrito", distrito);
    if (estado) params.set("estado", estado);
    navigate(`/pedidos?${params.toString()}`);
  };

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-in">
      <PageHeader
        titulo="Agrupación por Zonas"
        subtitulo="Zonas con pedidos pendientes o asignados, listas para enrutar."
      >
        <Button variant="secondary" icon={RefreshCw} onClick={cargar}>Actualizar</Button>
      </PageHeader>

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard label="Zonas activas" value={zonas.length} icon={MapPinned} tone="brand"
          hint="Con pendientes o asignados" />
        <StatCard label="Pendientes" value={totalPendientes} icon={Clock} tone="warning"
          hint="Por asignar a una ruta" />
        <StatCard label="Asignados" value={totalAsignados} icon={Truck} tone="info"
          hint="Ya en una ruta" />
      </div>

      <Card title="Zonas operativas detectadas">
        {cargando ? (
          <p className="py-10 text-center text-sm text-slate-500">Cargando agrupación…</p>
        ) : zonas.length === 0 ? (
          <p className="py-10 text-center text-sm text-slate-400">
            No hay zonas con pedidos pendientes o asignados. Importa o asigna pedidos para verlas aquí.
          </p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
            {zonas.map((z, i) => (
              <div key={z.distrito || "sin-distrito"} style={{ animationDelay: `${i * 40}ms` }} className="animate-fade-up">
                <DistrictCard
                  distrito={z.distrito}
                  pendientes={z.pendientes}
                  asignados={z.asignados}
                  onVerPendientes={() => irAPedidos(z.distrito, "PENDIENTE")}
                  onVerAsignados={() => irAPedidos(z.distrito, "ASIGNADO")}
                  onAbrir={() => irAPedidos(z.distrito)}
                />
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
