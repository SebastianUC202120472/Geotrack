import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, Legend, LabelList,
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
import DataTable from "../components/ui/DataTable";
import EmptyState from "../components/ui/EmptyState";
import LiveBadge from "../components/ui/LiveBadge";

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

export default function Dashboard() {
  const navigate = useNavigate();
  const [resumen, setResumen] = useState(null);
  const [pedidos, setPedidos] = useState([]);
  const [cargando, setCargando] = useState(true);
  // Indica si hay un refresco silencioso en curso (no bloquea la pantalla).
  const [actualizando, setActualizando] = useState(false);

  // Lleva a la lista de Pedidos ya filtrada por ese estado (clic en la gráfica).
  const irAEstado = (estadoRaw) => estadoRaw && navigate(`/pedidos?estado=${encodeURIComponent(estadoRaw)}`);

  // Carga (o refresca silenciosamente) el resumen y los pedidos.
  // silencioso=true: no toca `cargando`; usa `actualizando` en su lugar.
  const cargar = (silencioso) => {
    if (silencioso) {
      setActualizando(true);
    }
    Promise.allSettled([
      obtenerResumen().then(setResumen),
      listarPedidos().then(setPedidos),
    ]).finally(() => {
      if (silencioso) {
        setActualizando(false);
      } else {
        setCargando(false);
      }
    });
  };

  useEffect(() => {
    // Carga inicial: setState solo dentro del .then/.finally (no en el cuerpo del effect).
    Promise.allSettled([
      obtenerResumen().then(setResumen),
      listarPedidos().then(setPedidos),
    ]).finally(() => setCargando(false));

    // Auto-refresco cada 20 segundos (silencioso, fuera del cuerpo del effect).
    const intervalo = setInterval(() => cargar(true), 20000);

    // Refresco al recuperar el foco (silencioso, en un callback).
    const alFoco = () => cargar(true);
    window.addEventListener("focus", alFoco);

    return () => {
      clearInterval(intervalo);
      window.removeEventListener("focus", alFoco);
    };
  }, []);

  const porEstado = resumen?.pedidos_por_estado || {};
  const datosEstado = Object.entries(porEstado).map(([estado, cantidad]) => ({
    estado: estado.replaceAll("_", " ").toLowerCase(),
    estadoRaw: estado,
    cantidad,
  }));

  const entregados = porEstado.ENTREGADO || 0;
  const recientes = [...pedidos].slice(-6).reverse();
  const pedidosPorDia = agruparPedidosPorDia(pedidos, 7);

  return (
    <div className="space-y-6 p-6 lg:p-8">
      {/* Cabecera con indicador "en vivo" y chip de actualización */}
      <PageHeader titulo="Dashboard" subtitulo="Resumen operativo de SIOL-SAVA">
        <LiveBadge tone="success">En vivo</LiveBadge>
        {actualizando && (
          <span className="inline-flex items-center gap-2 rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-700">
            Actualizando <span className="updating-bar h-2 w-10 rounded-full" />
          </span>
        )}
      </PageHeader>

      {/* KPIs — bloque 1, entrada animada */}
      <div className="animate-fade-up" style={{ animationDelay: "0ms" }}>
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
      </div>

      {/* Gráficos de barras y tarta — bloque 2, entrada animada */}
      <div className="animate-fade-up grid gap-6 lg:grid-cols-3" style={{ animationDelay: "80ms" }}>
        <Card title="Pedidos por estado" subtitle="Toca un estado para ver esos pedidos" className="lg:col-span-2">
          {datosEstado.length === 0 ? (
            <EmptyState icon={Package} title="Aún no hay datos" description="Importa un Excel de pedidos para ver los gráficos." />
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={datosEstado} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#eef2f6" vertical={false} />
                <XAxis dataKey="estado" tick={{ fontSize: 12, fill: "#64748b" }} tickLine={false} axisLine={{ stroke: "#e2e8f0" }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: "#64748b" }} tickLine={false} axisLine={false} />
                <Tooltip cursor={{ fill: "#f1f5f9" }} contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0", fontSize: 13 }} />
                <Bar dataKey="cantidad" radius={[6, 6, 0, 0]} maxBarSize={56} cursor="pointer"
                  activeBar={{ opacity: 0.8 }}
                  onClick={(d) => irAEstado(d?.estadoRaw)}>
                  <LabelList dataKey="cantidad" position="top" style={{ fontSize: 11, fontWeight: 700, fill: "#475569" }} />
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
            <EmptyState icon={Package} title="Aún no hay datos" description="Importa un Excel de pedidos para ver los gráficos." />
          ) : (
            <div className="relative">
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
              <div className="pointer-events-none absolute inset-x-0 top-[104px] text-center">
                <p className="text-2xl font-bold text-slate-900 nums">{resumen?.total_pedidos ?? 0}</p>
                <p className="text-xs text-slate-400">pedidos</p>
              </div>
            </div>
          )}
        </Card>
      </div>

      {/* Línea de tendencia + EstadoSistema — bloque 3, entrada animada */}
      <div className="animate-fade-up grid gap-6 lg:grid-cols-3" style={{ animationDelay: "160ms" }}>
        <Card
          title="Pedidos por día"
          subtitle="Últimos 7 días (por fecha de creación)"
          className="lg:col-span-2"
        >
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={pedidosPorDia} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eef2f6" vertical={false} />
              <XAxis dataKey="dia" tick={{ fontSize: 12, fill: "#64748b" }} tickLine={false} axisLine={{ stroke: "#e2e8f0" }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: "#64748b" }} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0", fontSize: 13 }} />
              <Line type="monotone" dataKey="pedidos" stroke="#2563eb" strokeWidth={2.5} dot={{ r: 3, fill: "#2563eb" }} activeDot={{ r: 5 }} />
            </LineChart>
          </ResponsiveContainer>
        </Card>

        <EstadoSistema />
      </div>

      {/* Actividad reciente — bloque 4, entrada animada */}
      <div className="animate-fade-up" style={{ animationDelay: "240ms" }}>
        <Card title="Actividad reciente" subtitle="Últimos pedidos registrados">
          <DataTable
            columns={[
              { key: "codigo", header: "Código", className: "font-medium text-slate-800 nums" },
              { key: "cliente_origen", header: "Cliente" },
              { key: "destinatario", header: "Destinatario", render: (p) => p.nombre_destinatario || "—" },
              { key: "distrito", header: "Distrito", render: (p) => p.distrito || "—" },
              { key: "estado", header: "Estado", render: (p) => <EstadoBadge estado={p.estado} /> },
            ]}
            rows={recientes}
            rowKey={(p) => p.id}
            loading={cargando}
            empty={{ icon: Package, title: "Sin pedidos", description: "Aún no hay pedidos registrados." }}
          />
        </Card>
      </div>
    </div>
  );
}
