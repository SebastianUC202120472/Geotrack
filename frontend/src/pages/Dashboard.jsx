import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, Legend, LabelList,
} from "recharts";
import { Package, Truck, CircleCheck, Flag, Users } from "lucide-react";
import StatCard from "../components/ui/StatCard";
import Card from "../components/ui/Card";
import { EstadoBadge } from "../components/ui/Badge";
import { SkeletonStat } from "../components/ui/Skeleton";
import EmptyState from "../components/ui/EmptyState";
import { agruparPedidosPorDia } from "../utils/dashboard";
import { obtenerResumen, listarPedidos, obtenerSeguimientoClientes, obtenerUbicacionesFlota } from "../services/api";

// Colores por estado para gráficos.
const COLOR_ESTADO = {
  POR_RECOGER: "#94a3b8",
  OBSERVADO: "#f97316",
  LISTO_PARA_ENVIO: "#f59e0b",
  ASIGNADO: "#2563eb",
  EN_RUTA: "#0ea5e9",
  EN_PROGRESO: "#0ea5e9",
  ENTREGADO: "#16a34a",
  FALLIDO: "#dc2626",
  GEOCODIFICACION_FALLIDA: "#dc2626",
  CANCELADO: "#94a3b8",
  CREADA: "#94a3b8",
};

export default function Dashboard() {
  const navigate = useNavigate();
  const [resumen, setResumen] = useState(null);
  const [pedidos, setPedidos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [actualizando, setActualizando] = useState(false);
  const [pendientesPorCliente, setPendientesPorCliente] = useState([]);
  const [conductoresEnLinea, setConductoresEnLinea] = useState(0);

  // Lleva a la lista de Pedidos ya filtrada por estado (clic en gráfica).
  const irAEstado = (estadoRaw) => estadoRaw && navigate(`/pedidos?estado=${encodeURIComponent(estadoRaw)}`);

  useEffect(() => {
    const actualizarClientes = (data) => {
      const top6 = [...data].sort((a, b) => b.pendientes - a.pendientes).slice(0, 6);
      setPendientesPorCliente(top6);
    };
    const actualizarFlota = (data) => {
      setConductoresEnLinea(data.filter((u) => u.en_linea === true).length);
    };

    // Refresca todos los datos. Recibe silencioso: si true usa actualizando, si false usa cargando.
    const refrescar = (silencioso) => {
      if (silencioso) setActualizando(true);
      Promise.allSettled([
        obtenerResumen().then(setResumen),
        listarPedidos().then(setPedidos),
        obtenerSeguimientoClientes().then(actualizarClientes),
        obtenerUbicacionesFlota().then(actualizarFlota),
      ]).finally(() => {
        if (silencioso) setActualizando(false);
        else setCargando(false);
      });
    };

    refrescar(false);

    // Auto-refresco cada 20 s y al recuperar el foco.
    const intervalo = setInterval(() => refrescar(true), 20000);
    const alFoco = () => refrescar(true);
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

  // Maximo de pendientes del top-6 para escalar las barras de progreso.
  const maxPendCliente = Math.max(1, ...pendientesPorCliente.map((c) => c.pendientes));

  const fecha = new Date().toLocaleDateString("es-PE", {
    weekday: "long", day: "numeric", month: "long", year: "numeric",
  });

  return (
    <div className="space-y-6 p-6 lg:p-8">
      <div className="animate-fade-up flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Resumen operativo</h1>
          <p className="mt-1 text-sm capitalize text-slate-500">{fecha}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {actualizando && (
            <span className="inline-flex items-center gap-2 rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-700">
              Actualizando <span className="updating-bar h-2 w-10 rounded-full" />
            </span>
          )}
        </div>
      </div>

      <div className="animate-fade-up" style={{ animationDelay: "60ms" }}>
        {cargando ? (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
            <SkeletonStat /><SkeletonStat /><SkeletonStat /><SkeletonStat /><SkeletonStat />
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
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
            <StatCard label="Conductores en línea" value={conductoresEnLinea} icon={Users}
              tone="info" hint="Con ubicación activa en este momento" />
          </div>
        )}
      </div>

      <div className="animate-fade-up grid gap-6 lg:grid-cols-3" style={{ animationDelay: "120ms" }}>
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

      <div className="animate-fade-up" style={{ animationDelay: "180ms" }}>
        <Card title="Pedidos por día" subtitle="Últimos 7 días (por fecha de creación)">
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
      </div>

      <div className="animate-fade-up grid gap-6 lg:grid-cols-2" style={{ animationDelay: "240ms" }}>
        <Card title="Pedidos pendientes por cliente" subtitle="Top 6 · toca para ver los pedidos">
          {pendientesPorCliente.length === 0 ? (
            <EmptyState icon={Package} title="Sin pendientes" description="No hay pedidos pendientes por cliente." />
          ) : (
            <div className="space-y-3.5">
              {pendientesPorCliente.map((c) => (
                <button
                  key={c.cliente}
                  onClick={() => navigate("/pedidos")}
                  className="flex w-full items-center gap-3 text-left transition-colors hover:opacity-90"
                >
                  <span className="w-36 truncate text-sm font-medium text-slate-700">{c.cliente}</span>
                  <span className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
                    <span className="block h-full rounded-full bg-brand-600 transition-[width] duration-700"
                      style={{ width: `${(c.pendientes / maxPendCliente) * 100}%` }} />
                  </span>
                  <span className="w-8 text-right text-sm font-bold text-slate-700 nums">{c.pendientes}</span>
                </button>
              ))}
            </div>
          )}
        </Card>

        <Card title="Actividad reciente" subtitle="Últimos pedidos registrados">
          {recientes.length === 0 ? (
            <EmptyState icon={Package} title="Sin pedidos" description="Aún no hay pedidos registrados." />
          ) : (
            <div className="space-y-4">
              {recientes.map((p) => (
                <div key={p.id} className="flex items-start gap-3">
                  <span className="mt-1.5 h-2.5 w-2.5 flex-none rounded-full"
                    style={{ background: COLOR_ESTADO[p.estado] || "#94a3b8" }} />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-slate-800">
                      <span className="nums">{p.codigo}</span> · {p.cliente_origen}
                    </p>
                    <p className="text-xs text-slate-400">{p.distrito || "—"}</p>
                  </div>
                  <EstadoBadge estado={p.estado} />
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
