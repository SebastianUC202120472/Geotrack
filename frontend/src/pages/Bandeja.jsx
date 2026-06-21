import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { RefreshCw, Send, Mail, Inbox, Loader2, CheckCircle2, AlertCircle, FileSpreadsheet, Download } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import SectionCard from "../components/ui/SectionCard";
import EmptyState from "../components/ui/EmptyState";
import Button from "../components/ui/Button";
import Badge, { EstadoBadge } from "../components/ui/Badge";
import {
  listarConversaciones, obtenerConversacion, sincronizarCorreos,
  responderCorreo, marcarConversacion, descargarAdjunto,
} from "../services/api";

const fmt = (f) => (f ? new Date(f).toLocaleString("es-PE", { dateStyle: "short", timeStyle: "short" }) : "");

// Bandeja de solicitudes de recojo: hilos de correo con los clientes. Se lee la
// bandeja real por IMAP ("Revisar bandeja") y se responde por SMTP, todo con
// historial en la base de datos.
export default function Bandeja() {
  const [conversaciones, setConversaciones] = useState([]);
  const [selId, setSelId] = useState(null);
  const [detalle, setDetalle] = useState(null);
  const [texto, setTexto] = useState("");
  const [sincronizando, setSincronizando] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [aviso, setAviso] = useState(null);
  const navigate = useNavigate();

  const cargarLista = async () => {
    try {
      setConversaciones(await listarConversaciones());
    } catch (err) {
      setAviso({ ok: false, texto: err.message });
    }
  };

  useEffect(() => {
    cargarLista();
  }, []);

  const abrir = async (id) => {
    setSelId(id);
    setDetalle(null);
    try {
      setDetalle(await obtenerConversacion(id));
      cargarLista(); // refresca el contador de no leídos
    } catch (err) {
      setAviso({ ok: false, texto: err.message });
    }
  };

  const sincronizar = async () => {
    setSincronizando(true);
    setAviso(null);
    try {
      const res = await sincronizarCorreos();
      setAviso({ ok: true, texto: res.mensaje });
      await cargarLista();
    } catch (err) {
      setAviso({ ok: false, texto: err.message });
    } finally {
      setSincronizando(false);
    }
  };

  const responder = async (e) => {
    e.preventDefault();
    if (!texto.trim() || !selId) return;
    setEnviando(true);
    setAviso(null);
    try {
      await responderCorreo(selId, texto.trim());
      setTexto("");
      await abrir(selId);
    } catch (err) {
      setAviso({ ok: false, texto: err.message });
    } finally {
      setEnviando(false);
    }
  };

  const descargar = async (adj) => {
    try {
      await descargarAdjunto(adj.id, adj.nombre_archivo);
    } catch (err) {
      setAviso({ ok: false, texto: err.message });
    }
  };

  const alternarEstado = async () => {
    if (!detalle) return;
    const nuevo = detalle.estado === "ATENDIDA" ? "PENDIENTE" : "ATENDIDA";
    try {
      await marcarConversacion(selId, nuevo);
      await abrir(selId);
    } catch (err) {
      setAviso({ ok: false, texto: err.message });
    }
  };

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-in">
      <PageHeader titulo="Bandeja de Solicitudes" subtitulo="Correos de clientes para solicitar el recojo de pedidos.">
        <Button variant="secondary" icon={RefreshCw} onClick={sincronizar} disabled={sincronizando}>
          {sincronizando ? "Revisando…" : "Revisar bandeja"}
        </Button>
      </PageHeader>

      {aviso && (
        <div className={`flex items-center gap-2 rounded-xl px-4 py-3 text-sm animate-fade-up ${aviso.ok ? "bg-success-soft text-success-strong" : "bg-danger-soft text-danger-strong"}`}>
          {aviso.ok ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
          <span>{aviso.texto}</span>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3 animate-fade-up" style={{ animationDelay: "60ms" }}>
        {/* Lista de conversaciones */}
        <SectionCard title="Conversaciones" className="lg:col-span-1">
          {conversaciones.length === 0 ? (
            <EmptyState
              icon={Inbox}
              title="No hay solicitudes todavía"
              description='Pulsa "Revisar bandeja" para traer los correos nuevos.'
            />
          ) : (
            <ul className="-mx-1 divide-y divide-slate-50">
              {conversaciones.map((c) => (
                <li key={c.id}>
                  <button
                    onClick={() => abrir(c.id)}
                    className={`flex w-full flex-col gap-1 rounded-lg p-3 text-left transition-colors ${selId === c.id ? "bg-brand-50" : "hover:bg-slate-50"}`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="truncate text-sm font-semibold text-slate-800">
                        {c.contraparte_nombre || c.contraparte_email}
                      </span>
                      {c.no_leidos > 0 && (
                        <span className="rounded-full bg-brand-600 px-2 py-0.5 text-xs font-semibold text-white">{c.no_leidos}</span>
                      )}
                    </div>
                    <span className="truncate text-sm text-slate-500">{c.asunto}</span>
                    <div className="flex items-center justify-between">
                      <EstadoBadge estado={c.estado} />
                      <span className="text-xs text-slate-400">{fmt(c.ultimo_mensaje_en)}</span>
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </SectionCard>

        {/* Hilo seleccionado */}
        <SectionCard
          className="lg:col-span-2"
          title={detalle ? detalle.asunto : "Conversación"}
          action={detalle && (
            <div className="flex items-center gap-2">
              {/* Atajo: abre Recojos precargando el cliente de esta conversación (CUS-10) */}
              <Button variant="secondary" size="sm" icon={Inbox} onClick={() => navigate("/recojos", {
                state: {
                  crearDesdeBandeja: {
                    conversacion_id: detalle.id,
                    email: detalle.contraparte_email,
                    nombre: detalle.contraparte_nombre,
                  },
                },
              })}>
                Crear recojo
              </Button>
              <Button variant="ghost" size="sm" onClick={alternarEstado}>
                {detalle.estado === "ATENDIDA" ? "Marcar pendiente" : "Marcar atendida"}
              </Button>
            </div>
          )}
        >
          {!selId ? (
            <EmptyState
              icon={Mail}
              title="Selecciona una conversación"
              description="El hilo completo de mensajes aparecerá aquí."
            />
          ) : !detalle ? (
            <div className="flex items-center justify-center py-16 text-sm text-slate-500">
              <Loader2 className="animate-spin mr-2" size={18} /> Cargando conversación…
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              <div className="flex items-center gap-2 text-sm text-slate-500">
                <Badge tono="neutral">{detalle.contraparte_email}</Badge>
              </div>

              {/* Mensajes */}
              <div className="space-y-3">
                {detalle.mensajes.map((m) => {
                  const saliente = m.direccion === "SALIENTE";
                  return (
                    <div key={m.id} className={`flex ${saliente ? "justify-end" : "justify-start"}`}>
                      <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm ${saliente ? "bg-brand-600 text-white" : "bg-slate-100 text-slate-700"}`}>
                        <div className={`mb-1 flex items-center gap-2 text-xs ${saliente ? "text-brand-100" : "text-slate-400"}`}>
                          <span>{saliente ? "Tú" : m.remitente}</span>
                          <span>·</span>
                          <span>{fmt(m.fecha)}</span>
                        </div>
                        <p className="whitespace-pre-wrap break-words">{m.cuerpo || "(sin contenido)"}</p>

                        {m.adjuntos?.length > 0 && (
                          <div className="mt-3 space-y-1.5 border-t border-white/20 pt-2">
                            {m.adjuntos.map((adj) => (
                              <button
                                key={adj.id}
                                onClick={() => descargar(adj)}
                                className={`flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-left text-xs transition-colors ${saliente ? "bg-white/15 hover:bg-white/25" : "bg-white hover:bg-slate-50 border border-slate-200"}`}
                              >
                                <FileSpreadsheet size={16} className={saliente ? "" : "text-success"} />
                                <span className="flex-1 truncate">{adj.nombre_archivo}</span>
                                <Download size={14} />
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Responder */}
              <form onSubmit={responder} className="mt-2 border-t border-slate-100 pt-4">
                <textarea
                  value={texto}
                  onChange={(e) => setTexto(e.target.value)}
                  rows={3}
                  placeholder="Escribe tu respuesta…"
                  aria-label="Respuesta"
                  className="w-full resize-y rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-800 outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/30"
                />
                <div className="mt-3 flex justify-end">
                  <Button type="submit" icon={enviando ? undefined : Send} disabled={enviando || !texto.trim()}>
                    {enviando ? <Loader2 className="animate-spin" size={18} /> : "Enviar respuesta"}
                  </Button>
                </div>
              </form>
            </div>
          )}
        </SectionCard>
      </div>
    </div>
  );
}
