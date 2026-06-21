import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, Legend, LabelList,
  ComposedChart,
} from "recharts";
import { Package, Truck, CircleCheck, Flag, MapPin, Upload, Route as RouteIcon, Fuel, PiggyBank } from "lucide-react";
import StatCard from "../components/ui/StatCard";
import ChartCard from "../components/ui/ChartCard";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import { EstadoBadge } from "../components/ui/Badge";
import EstadoSistema from "../components/EstadoSistema";
import { SkeletonStat } from "../components/ui/Skeleton";
import EmptyState from "../components/ui/EmptyState";
import LiveBadge from "../components/ui/LiveBadge";
import { agruparPedidosPorDia } from "../utils/dashboard";
import { obtenerResumen, listarPedidos, obtenerKpisEficiencia } from "../services/api";

// Color de marca para cada estado (gráficos y puntos de la línea de tiempo).
const COLOR_ESTADO = {
  PENDIENTE: "#f59e0b",
  ASIGNADO: "#2563eb",
  EN_RUTA: "#0ea5e9",
  EN_PROGRESO: "#0ea5e9",
  ENTREGADO: "#16a34a",
  FALLIDO: "#dc2626",
  GEOCODIFICACION_FALLIDA: "#dc2626",
  CANCELADO: "#94a3b8",  // gris neutro: estado terminal sin entrega, diferente al azul de ASIGNADO
  CREADA: "#94a3b8",
};

export default function Dashboard() {
  const navigate = useNavigate();
  const [resumen, setResumen] = useState(null);
  const [pedidos, setPedidos] = useState([]);
  const [cargando, setCargando] = useState(true);
  // Indica si hay un refresco silencioso en curso (no bloquea la pantalla).
  const [actualizando, setActualizando] = useState(false);
  // KPIs de eficiencia: cajas, km recorridos/ahorrados, ahorro en soles, serie 7 días (CUS-34).
  const [efic, setEfic] = useState(null);

  // Lleva a la lista de Pedidos ya filtrada (clic en gráfica/zona).
  const irAEstado = (estadoRaw) => estadoRaw && navigate(`/pedidos?estado=${encodeURIComponent(estadoRaw)}`);
  const irAZona = (distrito) => navigate(`/pedidos?distrito=${encodeURIComponent(distrito)}&estado=PENDIENTE`);

  // Carga (o refresca silenciosamente) el resumen y los pedidos.
  // silencioso=true: no toca `cargando`; usa `actualizando` en su lugar.
  const cargar = (silencioso) => {
    if (silencioso) {
      setActualizando(true);
    }
    Promise.allSettled([
      obtenerResumen().then(setResumen),
      listarPedidos().then(setPedidos),
      obtenerKpisEficiencia().then(setEfic),
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
      obtenerKpisEficiencia().then(setEfic),
    ]).finally(() => setCargando(false));

    // Auto-refresco cada 20 s (silencioso) + al recuperar el foco.
    const intervalo = setInterval(() => cargar(true), 20000);
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

  // Zonas con pendientes: agrupa los pedidos por distrito contando los que
  // aún no están entregados/fallidos. Datos reales, top 6.
  const PEND = ["PENDIENTE", "ASIGNADO", "EN_RUTA", "EN_PROGRESO", "CREADA"];
  const zonasPendientes = Object.entries(
    pedidos.reduce((acc, p) => {
      if (p.distrito && PEND.includes(p.estado)) acc[p.distrito] = (acc[p.distrito] || 0) + 1;
      return acc;
    }, {}),
  )
    .map(([distrito, cantidad]) => ({ distrito, cantidad }))
    .sort((a, b) => b.cantidad - a.cantidad)
    .slice(0, 6);
  const maxZona = Math.max(1, ...zonasPendientes.map((z) => z.cantidad));

  // Fecha legible en español (se calcula en el cliente, en cada render).
  const fecha = new Date().toLocaleDateString("es-PE", {
    weekday: "long", day: "numeric", month: "long", year: "numeric",
  });

  return (
    <div className="space-y-6 p-6 lg:p-8">
      {/* Cabecera tipo "hero": saludo, fecha y acciones */}
      <div className="animate-fade-up flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Resumen operativo</h1>
          <p className="mt-1 text-sm capitalize text-slate-500">{fecha}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <LiveBadge tone="success">En vivo</LiveBadge>
          {actualizando && (
            <span className="inline-flex items-center gap-2 rounded-full bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-700">
              Actualizando <span className="updating-bar h-2 w-10 rounded-full" />
            </span>
          )}
          <Button size="sm" icon={Upload} onClick={() => navigate("/importar")}>
            Importar
          </Button>
        </div>
      </div>

      {/* KPIs */}
      <div className="animate-fade-up" style={{ animationDelay: "60ms" }}>
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

      {/* KPIs de eficiencia (CUS-34): cajas, km recorridos, km ahorrados y ahorro en combustible */}
      {/* StatCard no tiene prop prefix/suffix: el valor se formatea como string directamente. */}
      {efic && (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4 animate-fade-up">
          <StatCard label="Cajas entregadas hoy" value={efic.cajas_entregadas_hoy} tone="success" icon={Package} />
          <StatCard label="Km recorridos (estim.)" value={`${efic.km_recorridos} km`} tone="info" icon={RouteIcon} />
          <StatCard label="Km ahorrados" value={`${efic.km_ahorrados} km`} tone="brand" icon={Fuel} />
          <StatCard label="Ahorro en combustible" value={`S/ ${efic.soles_ahorrados}`} tone="warning" icon={PiggyBank} />
        </div>
      )}

      {/* Gráfico de eficiencia últimos 7 días: ahorro en S/ (barras) y cajas entregadas (línea) */}
      {efic && (
        <ChartCard title="Eficiencia · últimos 7 días" subtitle="Ahorro de combustible y cajas entregadas" height={260}>
          <ComposedChart data={efic.serie_7dias} margin={{ top: 8, right: 16, left: -8, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#eef2f6" vertical={false} />
            <XAxis dataKey="fecha" tickFormatter={(f) => f.slice(5)} tick={{ fontSize: 12, fill: "#64748b" }} tickLine={false} axisLine={{ stroke: "#e2e8f0" }} />
            <YAxis yAxisId="left" tick={{ fontSize: 12, fill: "#64748b" }} tickLine={false} axisLine={false} />
            <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12, fill: "#64748b" }} tickLine={false} axisLine={false} />
            <Tooltip contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0", fontSize: 13 }} />
            <Bar yAxisId="left" dataKey="soles_ahorrados" name="Ahorro S/" fill="#f59e0b" radius={[6, 6, 0, 0]} maxBarSize={48} />
            <Line yAxisId="right" type="monotone" dataKey="cajas" name="Cajas" stroke="#16a34a" strokeWidth={2} dot={{ r: 3 }} activeDot={{ r: 5 }} />
          </ComposedChart>
        </ChartCard>
      )}

      {/* Gráficos: barras + dona */}
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

      {/* Tendencia por día + estado del sistema */}
      <div className="animate-fade-up grid gap-6 lg:grid-cols-3" style={{ animationDelay: "180ms" }}>
        <Card title="Pedidos por día" subtitle="Últimos 7 días (por fecha de creación)" className="lg:col-span-2">
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

      {/* Zonas con pendientes + Actividad reciente (línea de tiempo) */}
      <div className="animate-fade-up grid gap-6 lg:grid-cols-2" style={{ animationDelay: "240ms" }}>
        <Card title="Zonas con pendientes" subtitle="Carga por distrito · toca para ver">
          {zonasPendientes.length === 0 ? (
            <EmptyState icon={MapPin} title="Sin pendientes" description="No hay pedidos pendientes por zona." />
          ) : (
            <div className="space-y-3.5">
              {zonasPendientes.map((z) => (
                <button
                  key={z.distrito}
                  onClick={() => irAZona(z.distrito)}
                  className="flex w-full items-center gap-3 text-left transition-colors hover:opacity-90"
                >
                  <span className="w-28 truncate text-sm font-medium text-slate-700">{z.distrito}</span>
                  <span className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">
                    <span className="block h-full rounded-full bg-brand-600 transition-[width] duration-700"
                      style={{ width: `${(z.cantidad / maxZona) * 100}%` }} />
                  </span>
                  <span className="w-8 text-right text-sm font-bold text-slate-700 nums">{z.cantidad}</span>
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
