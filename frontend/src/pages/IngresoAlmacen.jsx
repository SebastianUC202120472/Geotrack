import { useEffect, useState } from "react";
import { PackageCheck, ArrowLeft, CheckCircle2, AlertCircle, ImageOff, X } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import SectionCard from "../components/ui/SectionCard";
import DataTable from "../components/ui/DataTable";
import EmptyState from "../components/ui/EmptyState";
import Button from "../components/ui/Button";
import { EstadoBadge } from "../components/ui/Badge";
import { etiquetaEstado } from "../utils/estados";
import {
  listarRecojosAlmacen,
  obtenerConciliacion,
  confirmarIngreso,
  resolverObservado,
  urlMedia,
} from "../services/api";

// Lista recojos RECOGIDO/INGRESADO y permite abrir el panel de ingreso manual.
export default function IngresoAlmacen() {
  const [recojos, setRecojos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [seleccion, setSeleccion] = useState(null); // id de recojo en modo ingreso

  // Recarga la lista de recojos.
  const cargar = () => {
    listarRecojosAlmacen()
      .then((d) => setRecojos(d))
      .catch(() => {})
      .finally(() => setCargando(false));
  };

  useEffect(() => {
    let activo = true;
    listarRecojosAlmacen()
      .then((d) => activo && setRecojos(d))
      .catch(() => {})
      .finally(() => activo && setCargando(false));
    return () => {
      activo = false;
    };
  }, []);

  // Vuelve a la lista y la recarga (para reflejar el nuevo estado del recojo).
  const volverALista = () => {
    setSeleccion(null);
    setCargando(true);
    cargar();
  };

  if (seleccion != null) {
    return <PanelIngreso recojoId={seleccion} onVolver={volverALista} />;
  }

  const columnas = [
    {
      key: "codigo",
      header: "Código",
      render: (r) => <span className="font-medium text-slate-800 nums">{r.codigo || "—"}</span>,
    },
    {
      key: "cliente_origen",
      header: "Cliente",
      render: (r) => <span className="text-slate-700">{r.cliente_origen}</span>,
    },
    { key: "estado", header: "Estado", render: (r) => <EstadoBadge estado={r.estado} /> },
    {
      key: "conteo",
      header: "Conciliación",
      render: (r) => <ResumenConteo conteo={r.conteo} />,
    },
  ];

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-in">
      <PageHeader
        titulo="Ingreso a Almacén"
        subtitulo="Revisa las fotos del recojo, marca lo que no llegó y confirma el ingreso a mano."
      />
      <div className="animate-fade-up">
        <DataTable
          columns={columnas}
          rows={recojos}
          rowKey={(r) => r.id}
          loading={cargando}
          empty={{
            icon: PackageCheck,
            title: "No hay recojos por ingresar",
            description: "Aquí aparecen los recojos en estado RECOGIDO o ya INGRESADO.",
          }}
          onRowClick={(r) => setSeleccion(r.id)}
        />
      </div>
    </div>
  );
}

// Muestra resumen del conteo de un recojo. Recibe conteo { esperados, listos, observados, por_recoger }.
function ResumenConteo({ conteo }) {
  const c = conteo ?? { esperados: 0, listos: 0, observados: 0, por_recoger: 0 };
  return (
    <span className="text-slate-600 nums">
      {c.listos}/{c.esperados} listos
      {c.observados > 0 ? ` · ${c.observados} obs.` : ""}
      {c.por_recoger > 0 ? ` · ${c.por_recoger} por recoger` : ""}
    </span>
  );
}

// Panel de ingreso manual de un recojo. Recibe recojoId y onVolver.
function PanelIngreso({ recojoId, onVolver }) {
  const [conc, setConc] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [faltantes, setFaltantes] = useState({}); // { [referencia]: true } marcados "No llegó"
  const [trabajando, setTrabajando] = useState(false);
  const [aviso, setAviso] = useState(null);
  const [fotoAmpliada, setFotoAmpliada] = useState(null); // URL de la foto en el visor
  const [resolviendo, setResolviendo] = useState(null); // pedido_id en proceso de resolver

  // Refresca la conciliacion tras una accion.
  const refrescar = () =>
    obtenerConciliacion(recojoId)
      .then((d) => setConc(d))
      .catch(() => {});

  useEffect(() => {
    let activo = true;
    obtenerConciliacion(recojoId)
      .then((d) => activo && setConc(d))
      .catch(() => {})
      .finally(() => activo && setCargando(false));
    return () => {
      activo = false;
    };
  }, [recojoId]);

  // Marca/desmarca una referencia como "No llegó". Entrada: referencia del pedido.
  const alternarFaltante = (referencia) =>
    setFaltantes((prev) => ({ ...prev, [referencia]: !prev[referencia] }));

  // Confirma el ingreso a mano enviando las referencias marcadas como faltantes.
  const confirmar = async () => {
    setTrabajando(true);
    setAviso(null);
    const refs = Object.keys(faltantes).filter((ref) => faltantes[ref]);
    try {
      const r = await confirmarIngreso(recojoId, refs);
      setAviso({ ok: true, texto: r.mensaje || "Ingreso confirmado." });
      setFaltantes({});
      await refrescar();
    } catch (err) {
      setAviso({ ok: false, texto: err.message });
    } finally {
      setTrabajando(false);
    }
  };

  // Resuelve un pedido OBSERVADO y refresca la conciliación. Entrada: pedido_id.
  const resolver = async (pedidoId) => {
    setResolviendo(pedidoId);
    setAviso(null);
    try {
      const r = await resolverObservado(pedidoId);
      setAviso({ ok: true, texto: r.mensaje || "Pedido resuelto." });
      await refrescar();
    } catch (err) {
      setAviso({ ok: false, texto: err.message });
    } finally {
      setResolviendo(null);
    }
  };

  const conteo = conc?.conteo ?? { esperados: 0, listos: 0, observados: 0, por_recoger: 0 };
  const enRecogido = conc?.estado_recojo === "RECOGIDO";
  const pedidos = conc?.pedidos ?? [];
  const fotos = conc?.fotos ?? [];
  const observados = pedidos.filter((p) => p.estado === "OBSERVADO");

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-in">
      <PageHeader
        titulo="Ingreso a Almacén"
        subtitulo={conc ? `Recojo ${conc.recojo_id} · ${etiquetaEstado(conc.estado_recojo)}` : "Cargando…"}
      >
        <Button variant="secondary" icon={ArrowLeft} onClick={onVolver}>
          Volver
        </Button>
      </PageHeader>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 animate-fade-up">
        <Contador etiqueta="Esperados" valor={conteo.esperados} />
        <Contador etiqueta="Listos" valor={conteo.listos} tono="success" />
        <Contador
          etiqueta="Observados"
          valor={conteo.observados}
          tono={conteo.observados > 0 ? "danger" : "neutral"}
        />
        <Contador
          etiqueta="Por recoger"
          valor={conteo.por_recoger}
          tono={conteo.por_recoger > 0 ? "warning" : "neutral"}
        />
      </div>

      {aviso && (
        <div
          className={`flex items-center gap-2 rounded-xl px-3.5 py-3 text-sm animate-fade-up ${
            aviso.ok ? "bg-success-soft text-success-strong" : "bg-danger-soft text-danger-strong"
          }`}
        >
          {aviso.ok ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
          <span>{aviso.texto}</span>
        </div>
      )}

      {/* Galería de fotos que tomó el conductor durante el recojo */}
      <SectionCard title={`Fotos del recojo (${fotos.length})`}>
        {fotos.length === 0 ? (
          <div className="flex items-center gap-2 py-2 text-sm text-slate-400">
            <ImageOff size={18} />
            <span>El conductor no adjuntó fotos de este recojo.</span>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
            {fotos.map((ruta) => {
              const url = urlMedia(ruta);
              return (
                <button
                  key={ruta}
                  type="button"
                  onClick={() => setFotoAmpliada(url)}
                  className="group overflow-hidden rounded-xl border border-slate-200 outline-none transition focus-visible:ring-2 focus-visible:ring-brand-600"
                  title="Ver en grande"
                >
                  <img
                    src={url}
                    alt="Foto del recojo"
                    loading="lazy"
                    className="h-32 w-full object-cover transition-transform duration-200 group-hover:scale-105"
                  />
                </button>
              );
            })}
          </div>
        )}
      </SectionCard>

      {/* Tabla de pedidos del recojo. En RECOGIDO, cada POR_RECOGER puede marcarse "No llegó". */}
      <SectionCard
        title={`Pedidos del recojo (${pedidos.length})`}
        subtitle={enRecogido ? "Marca lo que no llegó al almacén antes de confirmar." : undefined}
        action={
          enRecogido ? (
            <Button onClick={confirmar} disabled={trabajando || cargando}>
              {trabajando ? "Confirmando…" : "Confirmar ingreso"}
            </Button>
          ) : undefined
        }
      >
        {cargando ? (
          <p className="py-6 text-center text-sm text-slate-400">Cargando pedidos…</p>
        ) : pedidos.length === 0 ? (
          <EmptyState icon={PackageCheck} title="Sin pedidos" description="Este recojo no tiene pedidos registrados." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 text-left text-xs font-semibold uppercase tracking-wide text-slate-400">
                  {enRecogido && <th className="px-3 py-2.5 w-24">No llegó</th>}
                  <th className="px-3 py-2.5">Referencia</th>
                  <th className="px-3 py-2.5">Destinatario</th>
                  <th className="px-3 py-2.5">Dirección</th>
                  <th className="px-3 py-2.5">Estado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {pedidos.map((p) => {
                  const marcable = enRecogido && p.estado === "POR_RECOGER";
                  return (
                    <tr key={p.pedido_id} className="hover:bg-slate-50">
                      {enRecogido && (
                        <td className="px-3 py-2.5">
                          {marcable ? (
                            <input
                              type="checkbox"
                              checked={!!faltantes[p.referencia]}
                              onChange={() => alternarFaltante(p.referencia)}
                              className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-600"
                              aria-label={`Marcar ${p.referencia} como no llegó`}
                            />
                          ) : (
                            <span className="text-slate-300">—</span>
                          )}
                        </td>
                      )}
                      <td className="px-3 py-2.5 nums font-medium text-slate-800">{p.referencia || p.codigo || "—"}</td>
                      <td className="px-3 py-2.5 text-slate-700">{p.nombre_destinatario || "—"}</td>
                      <td className="px-3 py-2.5 text-slate-500">{p.direccion_destino || "—"}</td>
                      <td className="px-3 py-2.5">
                        <EstadoBadge estado={p.estado} />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </SectionCard>

      {/* Pedidos observados (faltantes/discrepancias) pendientes de resolver a mano */}
      {observados.length > 0 && (
        <SectionCard
          title={`Observados (${observados.length})`}
          subtitle="Pedidos marcados como no llegados; resuélvelos cuando se aclare la discrepancia."
        >
          <div className="divide-y divide-slate-100">
            {observados.map((p) => (
              <div key={p.pedido_id} className="flex flex-wrap items-center justify-between gap-3 py-3">
                <div className="min-w-0">
                  <p className="nums text-sm font-medium text-slate-800">{p.referencia || p.codigo || "—"}</p>
                  <p className="truncate text-xs text-slate-500">
                    {p.nombre_destinatario || "Sin destinatario"} · {p.direccion_destino || "Sin dirección"}
                  </p>
                </div>
                <Button
                  variant="secondary"
                  size="sm"
                  icon={CheckCircle2}
                  onClick={() => resolver(p.pedido_id)}
                  disabled={resolviendo === p.pedido_id}
                >
                  {resolviendo === p.pedido_id ? "Resolviendo…" : "Resolver"}
                </Button>
              </div>
            ))}
          </div>
        </SectionCard>
      )}

      {/* Visor de foto en grande (lightbox) */}
      {fotoAmpliada && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 animate-fade-in"
          onClick={() => setFotoAmpliada(null)}
          role="dialog"
          aria-modal="true"
        >
          <button
            type="button"
            onClick={() => setFotoAmpliada(null)}
            className="absolute right-4 top-4 rounded-full bg-white/90 p-2 text-slate-700 outline-none transition hover:bg-white focus-visible:ring-2 focus-visible:ring-white"
            aria-label="Cerrar"
          >
            <X size={20} />
          </button>
          <img
            src={fotoAmpliada}
            alt="Foto del recojo ampliada"
            className="max-h-[90vh] max-w-[90vw] rounded-xl object-contain shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}
    </div>
  );
}

// Tarjeta de contador con tono semántico. Entrada: { etiqueta, valor, tono }.
function Contador({ etiqueta, valor, tono = "neutral" }) {
  const colores = {
    neutral: "text-slate-700",
    success: "text-success-strong",
    warning: "text-warning-strong",
    danger: "text-danger-strong",
  };
  return (
    <div className="rounded-card border border-slate-200 bg-white p-4">
      <p className="text-xs text-slate-400">{etiqueta}</p>
      <p className={`text-2xl font-bold nums ${colores[tono]}`}>{valor}</p>
    </div>
  );
}
