import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowUpRight, Check, CircleCheck, CircleX, Clock, Link2, LoaderCircle, ShieldCheck, X } from "lucide-react";
import {
  Bar,
  BarChart,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { actualizarAccion } from "./estadoChat";
import { cancelarAccion, confirmarAccion } from "./servicioAsistente";

const COLORES = ["#2563eb", "#16a34a", "#f59e0b", "#dc2626", "#0ea5e9", "#7c3aed", "#64748b", "#db2777"];

// Titulo de una tabla o grafico; en la vista grande lleva el enlace a su fuente. Recibe titulo, fuente y onNavegar.
function Titulo({ titulo, fuente, onNavegar, className = "" }) {
  return (
    <div className={`flex items-center justify-between gap-2 ${className}`}>
      <p className="text-xs font-semibold text-slate-700">{titulo}</p>
      {fuente && <Enlace bloque={fuente} onNavegar={onNavegar} discreto />}
    </div>
  );
}

// Columnas cuyo texto pasa a otra linea en vez de estirar la tabla (Motivo de fallo, Detalle...):
// las que tienen alguna celda de mas de LARGO_CELDA caracteres. Recibe el bloque.
const LARGO_CELDA = 28;
function columnasLargas(bloque) {
  return bloque.columnas.map((_, j) => bloque.filas.some((fila) => String(fila[j] ?? "").length > LARGO_CELDA));
}

// Tabla corta con los datos reales de la consulta. Recibe el bloque, si es grande y la fuente.
function Tabla({ bloque, grande, fuente, onNavegar }) {
  const largas = columnasLargas(bloque);
  // Texto largo: varias lineas, con un ancho minimo para que no quede una palabra por linea.
  const ajuste = (j) =>
    largas[j] ? `whitespace-normal break-words ${grande ? "min-w-[14rem] max-w-md" : "min-w-[11rem] max-w-[16rem]"}` : "whitespace-nowrap";
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200">
      <Titulo
        titulo={bloque.titulo}
        fuente={fuente}
        onNavegar={onNavegar}
        className="border-b border-slate-200 bg-slate-50 px-3 py-1.5"
      />
      <div className={`${grande ? "max-h-[28rem]" : "max-h-64"} overflow-auto`}>
        <table className={`w-full text-left ${grande ? "text-sm" : "text-xs"}`}>
          <thead className="sticky top-0 bg-white">
            <tr>
              {bloque.columnas.map((c, j) => (
                <th key={c} className={`${ajuste(j)} px-2 py-1.5 align-bottom font-semibold text-slate-500`}>
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {bloque.filas.map((fila, i) => (
              <tr key={i} className="border-t border-slate-100">
                {fila.map((celda, j) => (
                  <td key={j} className={`${ajuste(j)} px-2 py-1.5 align-top text-slate-700`}>
                    {String(celda)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {bloque.total > bloque.filas.length && (
        <p className="border-t border-slate-100 px-3 py-1 text-[11px] text-slate-500">
          Mostrando {bloque.filas.length} de {bloque.total}
        </p>
      )}
    </div>
  );
}

// Grafico simple de barras o torta. Recibe el bloque, si es grande y la fuente.
function Grafico({ bloque, grande, fuente, onNavegar }) {
  const datos = bloque.datos || [];
  if (!datos.length) return null;
  const letra = grande ? 12 : 10;
  // En la vista grande las barras crecen con la cantidad de categorias.
  const alto = grande ? Math.max(320, datos.length * 34) : 192;
  return (
    <div className="rounded-lg border border-slate-200 p-2">
      <Titulo titulo={bloque.titulo} fuente={fuente} onNavegar={onNavegar} className="px-1 pb-1" />
      <div className="w-full" style={{ height: bloque.forma === "torta" ? (grande ? 360 : 192) : alto }}>
        <ResponsiveContainer width="100%" height="100%">
          {bloque.forma === "torta" ? (
            <PieChart>
              <Pie
                data={datos}
                dataKey="valor"
                nameKey="etiqueta"
                outerRadius={grande ? 130 : 70}
                label={({ etiqueta, valor }) => (grande ? `${etiqueta}: ${valor}` : etiqueta)}
              >
                {datos.map((_, i) => (
                  <Cell key={i} fill={COLORES[i % COLORES.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          ) : (
            <BarChart data={datos} layout="vertical" margin={{ left: 8, right: grande ? 32 : 16 }}>
              <XAxis type="number" allowDecimals={false} tick={{ fontSize: letra }} />
              <YAxis type="category" dataKey="etiqueta" width={grande ? 180 : 110} tick={{ fontSize: letra }} />
              <Tooltip />
              <Bar dataKey="valor" fill="#2563eb" radius={[0, 4, 4, 0]} />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
}

// Boton que abre una pantalla del panel con los filtros aplicados. Recibe el bloque, onNavegar y discreto.
function Enlace({ bloque, onNavegar, discreto = false }) {
  const navigate = useNavigate();
  // Solo rutas internas del panel: nunca se abre un enlace externo.
  if (typeof bloque.ruta !== "string" || !bloque.ruta.startsWith("/panel")) return null;
  return (
    <button
      type="button"
      onClick={() => {
        navigate(bloque.ruta);
        onNavegar?.();
      }}
      title={discreto ? `Fuente: ${bloque.texto}` : undefined}
      className={
        discreto
          ? "inline-flex shrink-0 items-center gap-1 text-[11px] font-semibold text-brand-600 hover:text-brand-700 hover:underline"
          : "inline-flex items-center gap-1 rounded-full border border-brand-200 bg-brand-50 px-3 py-1 text-xs font-semibold text-brand-700 transition-colors hover:bg-brand-100"
      }
    >
      {discreto ? "Ver fuente" : bloque.texto}
      <ArrowUpRight size={13} />
    </button>
  );
}

// Segundos que le quedan a una propuesta pendiente. Recibe el bloque.
const segundosRestantes = (bloque) => {
  const vence = Date.parse(bloque.vence_en || "");
  return Number.isNaN(vence) ? 0 : Math.max(0, Math.round((vence - Date.now()) / 1000));
};

const ESTADOS_ACCION = {
  EJECUTADA: { texto: "Hecho", clase: "border-success/30 bg-success-soft text-success-strong", Icono: CircleCheck },
  ERROR: { texto: "No se aplicó", clase: "border-danger/30 bg-danger-soft text-danger-strong", Icono: CircleX },
  CANCELADA: { texto: "Cancelada: no se hizo ningún cambio", clase: "border-slate-200 bg-slate-50 text-slate-500", Icono: CircleX },
  VENCIDA: { texto: "Venció sin confirmar: no se hizo ningún cambio", clase: "border-slate-200 bg-slate-50 text-slate-500", Icono: Clock },
  INVALIDADA: { texto: "Sin efecto: no se hizo ningún cambio", clase: "border-slate-200 bg-slate-50 text-slate-500", Icono: Clock },
  EN_CURSO: { texto: "Ejecutando…", clase: "border-brand-200 bg-brand-50 text-brand-700", Icono: LoaderCircle },
  RECHAZADA: { texto: "No se ejecutó", clase: "border-warning/40 bg-warning-soft text-warning-strong", Icono: CircleX },
};

// Estados en los que se muestra el mensaje del servidor o del nucleo.
const CON_MENSAJE = new Set(["EJECUTADA", "ERROR", "RECHAZADA"]);

// Tarjeta de una accion que PROPUSO el asistente. Los textos los arma el servidor; el cambio solo
// ocurre con el clic en Confirmar (una vez: el boton se bloquea y el servidor tambien lo garantiza).
// Recibe el bloque {id, titulo, detalle, estado, vence_en, resultado}.
function TarjetaAccion({ bloque }) {
  const enviando = useRef(false);
  const [ocupado, setOcupado] = useState(false);
  const [restantes, setRestantes] = useState(() => segundosRestantes(bloque));
  const pendiente = bloque.estado === "PENDIENTE";

  useEffect(() => {
    if (!pendiente) return undefined;
    const reloj = setInterval(() => setRestantes(segundosRestantes(bloque)), 1000);
    return () => clearInterval(reloj);
  }, [pendiente, bloque]);

  const vencida = pendiente && restantes <= 0;
  const estado = vencida ? "VENCIDA" : bloque.estado;

  // Envia la decision del usuario y guarda el resultado en la tarjeta. Recibe la operacion.
  const decidir = async (operacion) => {
    if (enviando.current) return;
    enviando.current = true;
    setOcupado(true);
    if (operacion === "confirmar") actualizarAccion(bloque.id, { estado: "EN_CURSO" });
    try {
      const r = await (operacion === "confirmar" ? confirmarAccion(bloque.id) : cancelarAccion(bloque.id));
      actualizarAccion(bloque.id, { estado: r.estado, resultado: r.mensaje });
    } catch (e) {
      // El servidor no la ejecuto. 429: sigue pendiente (puede reintentar); 410: vencio;
      // otro (ya confirmada en otra pestaña, sin permiso...): queda rechazada con su mensaje.
      if (e.status === 429) actualizarAccion(bloque.id, { estado: "PENDIENTE", aviso: e.message });
      else actualizarAccion(bloque.id, { estado: e.status === 410 ? "VENCIDA" : "RECHAZADA", resultado: e.message });
    } finally {
      enviando.current = false;
      setOcupado(false);
    }
  };

  const info = ESTADOS_ACCION[estado];
  const minutos = Math.floor(restantes / 60);
  return (
    <div className="rounded-lg border border-brand-200 bg-white p-3 shadow-sm">
      <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-brand-700">
        <ShieldCheck size={13} /> Acción propuesta · requiere tu confirmación
      </p>
      <p className="mt-1 text-sm font-semibold text-slate-800">{String(bloque.titulo || "")}</p>
      {bloque.detalle && <p className="mt-0.5 text-xs leading-relaxed text-slate-600">{String(bloque.detalle)}</p>}

      {pendiente && !vencida ? (
        <div className="mt-2.5 flex flex-wrap items-center gap-2">
          <button
            type="button"
            disabled={ocupado}
            onClick={() => decidir("confirmar")}
            className="inline-flex items-center gap-1 rounded-md bg-brand-600 px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-brand-700 disabled:opacity-60"
          >
            {ocupado ? <LoaderCircle size={13} className="animate-spin" /> : <Check size={13} />} Confirmar
          </button>
          <button
            type="button"
            disabled={ocupado}
            onClick={() => decidir("cancelar")}
            className="inline-flex items-center gap-1 rounded-md border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-600 transition-colors hover:bg-slate-50 disabled:opacity-60"
          >
            <X size={13} /> Cancelar
          </button>
          <span className="ml-auto inline-flex items-center gap-1 text-[11px] text-slate-400">
            <Clock size={12} /> vence en {minutos}:{String(restantes % 60).padStart(2, "0")}
          </span>
        </div>
      ) : null}
      {pendiente && !vencida && bloque.aviso ? (
        <p className="mt-1.5 text-[11px] text-warning-strong">{String(bloque.aviso)}</p>
      ) : null}
      {!(pendiente && !vencida) && info && (
        <div className={`mt-2.5 flex items-start gap-1.5 rounded-md border px-2.5 py-1.5 text-xs ${info.clase}`}>
          <info.Icono size={14} className={`mt-px shrink-0 ${estado === "EN_CURSO" ? "animate-spin" : ""}`} />
          <span>
            <span className="font-semibold">{info.texto}</span>
            {bloque.resultado && CON_MENSAJE.has(estado) && <span>. {String(bloque.resultado)}</span>}
          </span>
        </div>
      )}
    </div>
  );
}

// Pinta los bloques de una respuesta: primero tablas y graficos, luego la accion propuesta y los enlaces.
// En la vista grande (grande=true) cada tabla o grafico muestra "Ver fuente" cuando la
// respuesta tiene una sola pantalla de origen, y los enlaces van bajo "Fuente de los datos".
// Recibe bloques, onNavegar y grande.
export default function BloquesRespuesta({ bloques, onNavegar, grande = false }) {
  if (!bloques?.length) return null;
  const visuales = bloques.filter((b) => b.tipo === "tabla" || b.tipo === "grafico");
  const enlaces = bloques.filter((b) => b.tipo === "enlace");
  const propuestas = bloques.filter((b) => b.tipo === "accion" && typeof b.id === "string");
  const fuente = grande && enlaces.length === 1 ? enlaces[0] : null;
  return (
    <div className={`mt-2 ${grande ? "space-y-3" : "space-y-2"}`}>
      {visuales.map((b, i) =>
        b.tipo === "tabla" ? (
          <Tabla key={i} bloque={b} grande={grande} fuente={fuente} onNavegar={onNavegar} />
        ) : (
          <Grafico key={i} bloque={b} grande={grande} fuente={fuente} onNavegar={onNavegar} />
        )
      )}
      {propuestas.map((b) => (
        <TarjetaAccion key={b.id} bloque={b} />
      ))}
      {enlaces.length > 0 && (
        <div className="flex flex-wrap items-center gap-1.5">
          {grande && (
            <span className="mr-1 inline-flex items-center gap-1 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
              <Link2 size={12} /> Fuente de los datos
            </span>
          )}
          {enlaces.map((b) => (
            <Enlace key={b.ruta} bloque={b} onNavegar={onNavegar} />
          ))}
        </div>
      )}
    </div>
  );
}
