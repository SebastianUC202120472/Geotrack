import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, Legend,
} from "recharts";
import { Package, Truck, CircleCheck, Flag } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import StatCard from "../components/ui/StatCard";
import Card from "../components/ui/Card";
import { EstadoBadge } from "../components/ui/Badge";
import EstadoSistema from "../components/EstadoSistema";
import { SkeletonStat } from "../components/ui/Skeleton";
import { agruparPedidosPorDia } from "../utils/dashboard";
import { obtenerResumen, listarPedidos } from "../services/api";

// Color de marca para cada estado (gráficos).
const COLOR_ESTADO = {
  PENDIENTE: "#f59e0b",
  ASIGNADO: "#2563eb",
  EN_RUTA: "#0ea5e9",
  EN_PROGRESO: "#0ea5e9",
  ENTREGADO: "#16a34a",
  FALLIDO: "#dc2626",
  GEOCODIFICACION_FALLIDA: "#dc2626",
  CREADA: "#94a3b8",
};

// Tendencia semanal de ejemplo (no hay endpoint histórico todavía).
const TENDENCIA_EJEMPLO = [
  { dia: "Lun", pedidos: 42 }, { dia: "Mar", pedidos: 55 }, { dia: "Mié", pedidos: 48 },
  { dia: "Jue", pedidos: 67 }, { dia: "Vie", pedidos: 73 }, { dia: "Sáb", pedidos: 38 },
  { dia: "Dom", pedidos: 21 },
];

export default function Dashboard() {
  const navigate = useNavigate();
  const [resumen, setResumen] = useState(null);
  const [pedidos, setPedidos] = useState([]);

  // Lleva a la lista de Pedidos ya filtrada por ese estado (clic en la gráfica).
  const irAEstado = (estadoRaw) => estadoRaw && navigate(`/pedidos?estado=${encodeURIComponent(estadoRaw)}`);

  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    Promise.allSettled([
      obtenerResumen().then(setResumen),
      listarPedidos().then(setPedidos),
    ]).finally(() => setCargando(false));
  }, []);

  const porEstado = resumen?.pedidos_por_estado || {};
  const datosEstado = Object.entries(porEstado).map(([estado, cantidad]) => ({
    estado: estado.replaceAll("_", " ").toLowerCase(),
    estadoRaw: estado,
    cantidad,
  }));

  const entregados = porEstado.ENTREGADO || 0;
  const recientes = [...pedidos].slice(-6).reverse();

  return (
    <div className="space-y-6 p-6 lg:p-8">
      <PageHeader titulo="Dashboard" subtitulo="Resumen operativo de SIOL-SAVA" />

      {/* KPIs */}
      {cargando ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <SkeletonStat /><SkeletonStat /><SkeletonStat /><SkeletonStat />
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard label="Pedidos totales" value={resumen?.total_pedidos ?? 0} icon={Package}
            tone="brand" hint="Acumulado en el sistema" />
          <StatCard label="Rutas activas" value={resumen?.rutas_activas ?? 0} icon={Truck}
            tone="info"
            progress={resumen?.total_rutas ? (resumen.rutas_activas / resumen.total_rutas) * 100 : 0}
            progressLabel={`de ${resumen?.total_rutas ?? 0} rutas`} />
          <StatCard label="Entregados" value={entregados} icon={CircleCheck}
            tone="success"
            progress={resumen?.total_pedidos ? (entregados / resumen.total_pedidos) * 100 : 0}
            progressLabel={resumen?.total_pedidos ? `${Math.round((entregados / resumen.total_pedidos) * 100)}% del total` : "Sin pedidos"} />
          <StatCard label="Rutas finalizadas" value={resumen?.rutas_finalizadas ?? 0} icon={Flag}
            tone="warning"
            progress={resumen?.total_rutas ? (resumen.rutas_finalizadas / resumen.total_rutas) * 100 : 0}
            progressLabel="Operaciones cerradas" />
        </div>
      )}

      {/* Gráficos */}
      <div className="grid gap-6 lg:grid-cols-3">
        <Card title="Pedidos por estado" subtitle="Toca un estado para ver esos pedidos" className="lg:col-span-2">
          {datosEstado.length === 0 ? (
            <VacioGrafico />
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={datosEstado} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#eef2f6" vertical={false} />
                <XAxis dataKey="estado" tick={{ fontSize: 12, fill: "#64748b" }} tickLine={false} axisLine={{ stroke: "#e2e8f0" }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: "#64748b" }} tickLine={false} axisLine={false} />
                <Tooltip cursor={{ fill: "#f1f5f9" }} contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0", fontSize: 13 }} />
                <Bar dataKey="cantidad" radius={[6, 6, 0, 0]} maxBarSize={56} cursor="pointer"
                  onClick={(d) => irAEstado(d?.estadoRaw)}>
                  {datosEstado.map((d) => (
                    <Cell key={d.estadoRaw} fill={COLOR_ESTADO[d.estadoRaw] || "#2563eb"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>

        <Card title="Distribución de estados">
          {datosEstado.length === 0 ? (
            <VacioGrafico />
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={datosEstado} dataKey="cantidad" nameKey="estado" innerRadius={58} outerRadius={92} paddingAngle={2}
                  cursor="pointer" onClick={(d) => irAEstado(d?.estadoRaw)}>
                  {datosEstado.map((d) => (
                    <Cell key={d.estadoRaw} fill={COLOR_ESTADO[d.estadoRaw] || "#2563eb"} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0", fontSize: 13 }} />
                <Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card
          title="Tendencia de pedidos"
          subtitle="Últimos 7 días"
          className="lg:col-span-2"
          action={<span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-500">datos de ejemplo</span>}
        >
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={TENDENCIA_EJEMPLO} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eef2f6" vertical={false} />
              <XAxis dataKey="dia" tick={{ fontSize: 12, fill: "#64748b" }} tickLine={false} axisLine={{ stroke: "#e2e8f0" }} />
              <YAxis tick={{ fontSize: 12, fill: "#64748b" }} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0", fontSize: 13 }} />
              <Line type="monotone" dataKey="pedidos" stroke="#2563eb" strokeWidth={2.5} dot={{ r: 3, fill: "#2563eb" }} activeDot={{ r: 5 }} />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        <EstadoSistema />
      </div>

      {/* Actividad reciente */}
      <Card title="Actividad reciente" subtitle="Últimos pedidos registrados">
        {recientes.length === 0 ? (
          <p className="py-8 text-center text-sm text-slate-400">No hay pedidos registrados todavía.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-400">
                  <th className="pb-3 font-semibold">Código</th>
                  <th className="pb-3 font-semibold">Cliente</th>
                  <th className="pb-3 font-semibold">Destinatario</th>
                  <th className="pb-3 font-semibold">Distrito</th>
                  <th className="pb-3 font-semibold">Estado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {recientes.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50">
                    <td className="py-3 font-medium text-slate-800 nums">{p.codigo}</td>
                    <td className="py-3 text-slate-600">{p.cliente_origen}</td>
                    <td className="py-3 text-slate-600">{p.nombre_destinatario || "—"}</td>
                    <td className="py-3 text-slate-600">{p.distrito || "—"}</td>
                    <td className="py-3"><EstadoBadge estado={p.estado} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}

function VacioGrafico() {
  return (
    <div className="flex h-[280px] flex-col items-center justify-center text-center text-sm text-slate-400">
      <Package size={32} className="mb-2 opacity-40" />
      <p>Aún no hay pedidos para graficar.</p>
      <p className="text-xs">Importa un Excel para ver los datos aquí.</p>
    </div>
  );
}
