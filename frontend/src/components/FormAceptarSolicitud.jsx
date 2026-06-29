import { useState, useEffect } from "react";
import {
  UploadCloud,
  CheckCircle2,
  Loader2,
  FileSpreadsheet,
  FileX2,
  AlertTriangle,
} from "lucide-react";
import SectionCard from "./ui/SectionCard";
import EmptyState from "./ui/EmptyState";
import Button from "./ui/Button";
import Input from "./ui/Input";

import { listarClientes, aceptarSolicitud } from "../services/api";

// Formulario reutilizable para aceptar una solicitud de recojo.
// Recibe: desdeCorreo? { conversacion_id, nombre, email } — precarga el cliente si viene de la bandeja.
export default function FormAceptarSolicitud({ desdeCorreo }) {
  const [clientes, setClientes] = useState([]);
  const [clienteId, setClienteId] = useState("");
  const [file, setFile] = useState(null);
  const [referencia, setReferencia] = useState("");
  const [contactoOrigen, setContactoOrigen] = useState("");
  const [cargando, setCargando] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState("");

  // Carga la lista de clientes y, si viene de un correo, preselecciona el cliente que coincida.
  useEffect(() => {
    listarClientes()
      .then((data) => {
        setClientes(data);
        if (desdeCorreo) {
          // Busca por razon_social (normalizado) o por contacto (email).
          const nombreNorm = (desdeCorreo.nombre || "").trim().toLowerCase();
          const emailNorm = (desdeCorreo.email || "").trim().toLowerCase();
          const match = data.find(
            (c) =>
              (nombreNorm && c.razon_social?.trim().toLowerCase() === nombreNorm) ||
              (emailNorm && c.contacto?.trim().toLowerCase() === emailNorm)
          );
          if (match) setClienteId(String(match.id));
        }
      })
      .catch(() => {});
  }, [desdeCorreo]);

  // Guarda el archivo seleccionado y limpia estados previos.
  const elegirArchivo = (e) => {
    const archivo = e.target.files[0];
    if (archivo) {
      setFile(archivo);
      setError("");
      setResultado(null);
    }
  };

  // Envía el formulario al backend y almacena el resumen o el error.
  // Si viene de un correo, incluye el conversacion_id para cerrar el hilo al aceptar.
  const aceptar = () => {
    if (!clienteId || !file) return;
    setCargando(true);
    setError("");
    setResultado(null);
    aceptarSolicitud(Number(clienteId), file, {
      referencia: referencia.trim() || undefined,
      contacto_origen: contactoOrigen.trim() || undefined,
      conversacion_id: desdeCorreo?.conversacion_id || undefined,
    })
      .then((data) => {
        setResultado(data);
        setCargando(false);
      })
      .catch((err) => {
        setError(err.message || "Error al procesar la solicitud");
        setCargando(false);
      });
  };

  return (
    <div className="space-y-6">
      {/* Datos de la solicitud */}
      <SectionCard
        title="Datos de la solicitud"
        subtitle="Completa los campos obligatorios (marcados con *)"
      >
        <div className="space-y-4">
          {/* Selector de cliente registrado */}
          <Input
            as="select"
            label="Cliente *"
            value={clienteId}
            onChange={(e) => {
              setClienteId(e.target.value);
              setError("");
              setResultado(null);
            }}
          >
            <option value="">— Selecciona un cliente —</option>
            {clientes.map((c) => (
              <option key={c.id} value={c.id}>
                {c.razon_social}
              </option>
            ))}
          </Input>

          {/* Campo opcional de referencia interna */}
          <Input
            label="Referencia (opcional)"
            placeholder="Ej. OC-2026-001"
            value={referencia}
            onChange={(e) => setReferencia(e.target.value)}
          />

          {/* Campo opcional de contacto en origen */}
          <Input
            label="Contacto en origen (opcional)"
            placeholder="Nombre o teléfono del responsable de carga"
            value={contactoOrigen}
            onChange={(e) => setContactoOrigen(e.target.value)}
          />
        </div>
      </SectionCard>

      {/* Zona de carga del Excel */}
      <SectionCard
        title="Archivo de pedidos *"
        subtitle="Formatos permitidos: XLSX"
      >
        {/* Input oculto para selección de archivo */}
        <input
          id="excel-recojo-form"
          type="file"
          accept=".xlsx"
          className="hidden"
          onChange={elegirArchivo}
        />

        {/* Estado vacío: aún no se eligió archivo */}
        {!file ? (
          <label htmlFor="excel-recojo-form" className="block cursor-pointer">
            <EmptyState
              icon={UploadCloud}
              title="Selecciona el Excel de pedidos"
              description="Haz clic aquí para elegir el archivo .xlsx con los pedidos del cliente."
            />
          </label>
        ) : (
          /* Archivo seleccionado: preview con nombre */
          <label
            htmlFor="excel-recojo-form"
            className="block cursor-pointer rounded-xl border-2 border-dashed border-brand-300 bg-brand-50 p-8 text-center transition-colors hover:border-brand-400 hover:bg-brand-100/60"
          >
            <FileSpreadsheet className="mx-auto text-brand-600" size={48} />
            <p className="mt-3 text-base font-semibold text-slate-800">
              {file.name}
            </p>
            <p className="mt-1 text-sm text-slate-500">
              Haz clic para cambiar el archivo
            </p>
          </label>
        )}

        {/* Botón de envío */}
        <Button
          onClick={aceptar}
          disabled={!clienteId || !file || cargando}
          size="lg"
          block
          icon={cargando ? undefined : FileSpreadsheet}
          className="mt-5"
        >
          {cargando ? (
            <>
              <Loader2 className="animate-spin" size={20} />
              Procesando solicitud…
            </>
          ) : (
            "Aceptar solicitud"
          )}
        </Button>
      </SectionCard>

      {/* Resumen exitoso */}
      {resultado && (
        <div className="rounded-card border border-emerald-200 bg-emerald-50 p-5 shadow-card">
          <div className="flex items-center gap-4">
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
              <CheckCircle2 size={24} />
            </span>
            <div>
              <h3 className="text-base font-semibold text-slate-900">
                Recojo registrado — <span className="font-mono">{resultado.codigo}</span>
              </h3>
              <p className="text-sm text-slate-600">
                {resultado.pedidos_creados} pedidos creados ·{" "}
                {resultado.pedidos_geocodificados} geocodificados
                {resultado.pedidos_sin_ubicar > 0 &&
                  ` · ${resultado.pedidos_sin_ubicar} sin ubicar`}
                .
              </p>
            </div>
          </div>

          {/* Lista de filas rechazadas por el backend */}
          {resultado.filas_rechazadas && resultado.filas_rechazadas.length > 0 && (
            <div className="mt-4 rounded-card border border-amber-200 bg-amber-50 p-4">
              <div className="flex items-center gap-2">
                <AlertTriangle size={16} className="text-amber-700" />
                <p className="text-sm font-semibold text-amber-800">
                  {resultado.filas_rechazadas.length} fila(s) no se importaron:
                </p>
              </div>
              <ul className="mt-2 space-y-1 text-sm text-amber-700">
                {resultado.filas_rechazadas.map((r, i) => (
                  <li key={i} className="nums">{r}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Error de envío */}
      {error && (
        <div className="rounded-card border border-red-200 bg-red-50 p-5 shadow-card">
          <div className="flex items-start gap-3">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-red-100 text-red-600">
              <FileX2 size={20} />
            </span>
            <div>
              <h3 className="text-sm font-semibold text-red-800">
                Error al procesar la solicitud
              </h3>
              <p className="mt-0.5 text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
