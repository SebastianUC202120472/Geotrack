import { useEffect, useState } from "react";
import { Building2, FileSpreadsheet, Loader2 } from "lucide-react";
import Card from "../ui/Card";
import SectionCard from "../ui/SectionCard";
import EmptyState from "../ui/EmptyState";
import Button from "../ui/Button";
import { obtenerSeguimientoClientes, generarLiquidacion, descargarLiquidacion } from "../../services/api";

// Carga y muestra los repartos agrupados por empresa (CUS-36).
// Sin props: autocontenido; carga datos con obtenerSeguimientoClientes() al montar.
export default function VistaPorCliente() {
  const [clientes, setClientes] = useState(null);
  const [cargando, setCargando] = useState(true);

  // Solicita los clientes con pedidos activos al montar; setState solo dentro de callbacks.
  useEffect(() => {
    let activo = true;
    obtenerSeguimientoClientes()
      .then((data) => { if (activo) setClientes(data || []); })
      .catch((err) => {
        console.error("No se pudo cargar los clientes:", err.message);
        if (activo) setClientes([]);
      })
      .finally(() => { if (activo) setCargando(false); });
    return () => { activo = false; };
  }, []);

  if (cargando) {
    return (
      <SectionCard>
        <div className="flex justify-center py-12 text-slate-400">
          <Loader2 className="animate-spin" size={24} />
        </div>
      </SectionCard>
    );
  }

  if (!clientes || clientes.length === 0) {
    return (
      <SectionCard title="Clientes">
        <EmptyState
          icon={Building2}
          title="Sin pedidos de clientes"
          description="Los repartos agrupados por empresa aparecerán aquí."
        />
      </SectionCard>
    );
  }

  return (
    <SectionCard
      title="Por cliente"
      subtitle={`${clientes.length} empresa${clientes.length !== 1 ? "s" : ""} con pedidos activos`}
    >
      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        {clientes.map((c, i) => (
          <div key={c.cliente} style={{ animationDelay: `${i * 40}ms` }} className="animate-fade-up">
            <ClienteCard c={c} />
          </div>
        ))}
      </div>
    </SectionCard>
  );
}

const MINI_DOT = { success: "bg-success", info: "bg-info", warning: "bg-warning", danger: "bg-danger", neutral: "bg-slate-400" };

// Conteo de un grupo dentro de la tarjeta del cliente (color + número + etiqueta).
// Entrada: tono (string clave de MINI_DOT), valor (number), etiqueta (string).
function Mini({ tono, valor, etiqueta }) {
  return (
    <div className="flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2 transition-colors hover:bg-brand-50">
      <span className={`h-2 w-2 shrink-0 rounded-full ${MINI_DOT[tono]}`} />
      <span className="text-lg font-bold text-slate-800 nums">{valor}</span>
      <span className="text-xs text-slate-400">{etiqueta}</span>
    </div>
  );
}

// Tarjeta individual de empresa con barra de progreso y desglose de estados.
// Entrada: c (objeto cliente con campos total, entregados, en_proceso, pendientes, fallidos).
function ClienteCard({ c }) {
  const avance = c.total ? Math.round((c.entregados / c.total) * 100) : 0;
  const [generando, setGenerando] = useState(false);
  const [error, setError] = useState(null);

  // CUS-36: genera la liquidación del cliente y descarga el Excel; setState en callbacks.
  const descargar = () => {
    setGenerando(true);
    setError(null);
    generarLiquidacion({ cliente: c.cliente })
      .then((res) => descargarLiquidacion(res.descarga_url, res.archivo))
      .catch((err) => setError(err.message))
      .finally(() => setGenerando(false));
  };

  return (
    <Card hover>
      <div className="mb-4 flex items-start justify-between gap-2">
        <div className="flex min-w-0 items-center gap-2">
          <span className="shrink-0 rounded-xl bg-brand-50 p-2 text-brand-600">
            <Building2 size={18} />
          </span>
          <h3 className="truncate font-semibold text-slate-900" title={c.cliente}>
            {c.cliente}
          </h3>
        </div>
        <span className="shrink-0 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-500 nums">
          {c.total}
        </span>
      </div>

      {/* Barra de progreso de entregas */}
      <div className="mb-4">
        <div className="mb-1 flex justify-between text-sm">
          <span className="text-slate-500">Entregado</span>
          <span className="font-semibold text-slate-700 nums">{avance}%</span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full rounded-full bg-success transition-all"
            style={{ width: `${avance}%` }}
          />
        </div>
      </div>

      {/* Desglose por estado (CANCELADO se muestra aparte de Fallidos para no confundir) */}
      <div className="grid grid-cols-2 gap-2">
        <Mini tono="success" valor={c.entregados} etiqueta="Entregados" />
        <Mini tono="info" valor={c.en_proceso} etiqueta="En proceso" />
        <Mini tono="warning" valor={c.pendientes} etiqueta="Pendientes" />
        <Mini tono="danger" valor={c.fallidos} etiqueta="Fallidos" />
        {c.cancelados > 0 && <Mini tono="neutral" valor={c.cancelados} etiqueta="Cancelados" />}
      </div>

      {/* CUS-36: liquidación del cliente (genera y descarga el Excel) */}
      <Button
        variant="secondary"
        size="sm"
        block
        className="mt-4"
        icon={generando ? Loader2 : FileSpreadsheet}
        onClick={descargar}
        disabled={generando}
      >
        {generando ? "Generando…" : "Descargar liquidación (Excel)"}
      </Button>
      {error && <p className="mt-2 text-xs text-danger-strong">{error}</p>}
    </Card>
  );
}
