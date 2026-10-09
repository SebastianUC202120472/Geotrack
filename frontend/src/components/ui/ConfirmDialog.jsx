import { AlertTriangle, HelpCircle } from "lucide-react";
import Modal from "./Modal";
import Button from "./Button";

// Dialogo de confirmacion reutilizable para acciones que conviene pensar dos veces.
// Recibe open, titulo, mensaje (texto o nodo), textoConfirmar, tono ("danger" | "brand"),
// icono opcional, cargando, onConfirmar y onCancelar. children agrega contenido extra (p. ej. un motivo).
export default function ConfirmDialog({
  open,
  titulo,
  mensaje,
  textoConfirmar = "Confirmar",
  tono = "brand",
  icono,
  cargando = false,
  deshabilitado = false,
  onConfirmar,
  onCancelar,
  children,
}) {
  const Icono = icono || (tono === "danger" ? AlertTriangle : HelpCircle);
  const fondoIcono = tono === "danger" ? "bg-danger-soft text-danger-strong" : "bg-brand-50 text-brand-700";

  return (
    <Modal open={open} onClose={cargando ? () => {} : onCancelar} variant="center">
      <div className="flex items-start gap-4">
        <span className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full ${fondoIcono}`}>
          <Icono size={22} />
        </span>
        <div className="min-w-0 flex-1">
          <h2 className="text-base font-bold text-slate-900">{titulo}</h2>
          {mensaje && <div className="mt-1.5 text-sm leading-relaxed text-slate-600">{mensaje}</div>}
        </div>
      </div>
      {children && <div className="mt-4">{children}</div>}
      <div className="mt-6 flex gap-2">
        <Button variant="secondary" block onClick={onCancelar} disabled={cargando}>
          Cancelar
        </Button>
        <Button
          variant={tono === "danger" ? "danger" : "primary"}
          block
          onClick={onConfirmar}
          disabled={cargando || deshabilitado}
          autoFocus
        >
          {cargando ? "Procesando…" : textoConfirmar}
        </Button>
      </div>
    </Modal>
  );
}
