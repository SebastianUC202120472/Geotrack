import { useState } from "react";
import { X, CheckCircle2, MapPin, Wrench } from "lucide-react";
import Button from "./ui/Button";
import Badge from "./ui/Badge";
import { resolverIncidencia } from "../services/api";

// Modal de resolución de incidencia de auxilio mecánico.
// Muestra placa, ruta, descripción, ubicación y foto si existe.
// Entrada: incidencia (objeto), onClose (fn), onResuelta (fn llamada tras resolver).
export default function ResolverIncidenciaModal({ incidencia: i, onClose, onResuelta }) {
  const [resolviendo, setResolviendo] = useState(false);
  const [error, setError] = useState(null);

  // Llama al endpoint para marcar como resuelta; notifica al padre y cierra.
  const resolver = () => {
    setResolviendo(true);
    setError(null);
    resolverIncidencia(i.id)
      .then(() => {
        onResuelta();
        onClose();
      })
      .catch((e) => {
        setError(e.message);
        setResolviendo(false);
      });
  };

  return (
    <>
      {/* Cabecera */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <Wrench size={20} className="text-danger" />
          <div>
            <h2 className="font-bold text-slate-900">
              {i.codigo ?? `IN-${i.id}`}
            </h2>
            <p className="text-xs text-slate-500">Incidencia de auxilio mecánico</p>
          </div>
        </div>
        <button
          onClick={onClose}
          aria-label="Cerrar"
          className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"
        >
          <X size={20} />
        </button>
      </div>

      {/* Datos principales */}
      <div className="mt-5 space-y-2.5">
        {i.vehiculo_placa && (
          <Fila etiqueta="Placa" valor={i.vehiculo_placa} />
        )}
        <Fila etiqueta="Ruta" valor={i.ruta_nombre ?? `Ruta ${i.ruta_id}`} />
        <Fila etiqueta="Conductor" valor={i.conductor_nombre ?? "—"} />
        <div className="flex items-start gap-2 rounded-xl bg-slate-50 px-4 py-3 text-sm">
          <span className="w-24 shrink-0 text-xs text-slate-400">Descripción</span>
          <span className="text-slate-700">{i.descripcion || "Sin detalle"}</span>
        </div>

        {/* Enlace a ubicación GPS si existe */}
        {i.latitud != null && i.longitud != null && (
          <a
            className="inline-flex items-center gap-1.5 rounded-xl bg-brand-50 px-4 py-2.5 text-sm font-medium text-brand-600 hover:underline"
            href={`https://www.google.com/maps?q=${i.latitud},${i.longitud}`}
            target="_blank"
            rel="noreferrer"
          >
            <MapPin size={15} /> Ver ubicación en Google Maps
          </a>
        )}

        {/* Foto de evidencia si existe */}
        {i.url_evidencia && (
          <div className="mt-1">
            <p className="mb-1.5 text-xs text-slate-400">Foto de evidencia</p>
            <img
              src={i.url_evidencia}
              alt="Evidencia de la avería"
              className="max-h-48 w-full rounded-xl object-cover"
            />
          </div>
        )}

        {/* Estado */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Estado</span>
          <Badge tono={i.estado === "ABIERTA" ? "danger" : "success"}>{i.estado}</Badge>
        </div>
      </div>

      {/* Error */}
      {error && (
        <p className="mt-3 rounded-xl bg-danger-soft px-4 py-2.5 text-sm text-danger-strong">
          {error}
        </p>
      )}

      {/* Acción */}
      {i.estado === "ABIERTA" && (
        <div className="mt-6">
          <Button
            icon={CheckCircle2}
            block
            disabled={resolviendo}
            onClick={resolver}
          >
            {resolviendo ? "Resolviendo…" : "Marcar resuelta"}
          </Button>
        </div>
      )}
    </>
  );
}

// Fila de dato simple con etiqueta + valor.
function Fila({ etiqueta, valor }) {
  return (
    <div className="flex items-center gap-2 rounded-xl bg-slate-50 px-4 py-3 text-sm">
      <span className="w-24 shrink-0 text-xs text-slate-400">{etiqueta}</span>
      <span className="font-medium text-slate-700">{valor}</span>
    </div>
  );
}
