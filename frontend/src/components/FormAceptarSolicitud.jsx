import { useState, useEffect } from "react";
import {
  UploadCloud,
  CheckCircle2,
  Loader2,
  FileSpreadsheet,
  FileX2,
  AlertTriangle,
  PenLine,
  MapPinOff,
} from "lucide-react";
import SectionCard from "./ui/SectionCard";
import EmptyState from "./ui/EmptyState";
import Button from "./ui/Button";
import Input from "./ui/Input";
import EditorPedidosManual from "./EditorPedidosManual";
import { PEDIDO_VACIO, validarPedidosManual } from "../utils/pedidosManual";
import { listarClientes, aceptarSolicitud, registrarSolicitudManual } from "../services/api";

// Fecha local de hoy en formato "AAAA-MM-DD" (minimo del selector de fecha de recojo).
const hoyISO = () => new Date().toLocaleDateString("en-CA");

// Formulario para registrar una solicitud de recojo: con el Excel del cliente o escribiendo
// los pedidos a mano (pedido por telefono, C11-02), y con la fecha pedida para el recojo
// (C11-04). Recibe desdeCorreo? { conversacion_id, nombre, email } cuando nace de un correo.
export default function FormAceptarSolicitud({ desdeCorreo }) {
  const [clientes, setClientes] = useState([]);
  const [clienteId, setClienteId] = useState("");
  const [modo, setModo] = useState("excel"); // "excel" | "manual"
  const [file, setFile] = useState(null);
  const [filas, setFilas] = useState([{ ...PEDIDO_VACIO }]);
  const [erroresFilas, setErroresFilas] = useState({});
  const [referencia, setReferencia] = useState("");
  const [contactoOrigen, setContactoOrigen] = useState("");
  const [fechaProgramada, setFechaProgramada] = useState("");
  const [cargando, setCargando] = useState(false);
  const [resultado, setResultado] = useState(null);
  const [error, setError] = useState("");

  // Carga clientes y preselecciona si viene de un correo.
  useEffect(() => {
    listarClientes()
      .then((data) => {
        setClientes(data);
        if (desdeCorreo) {
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

  const cliente = clientes.find((c) => String(c.id) === clienteId);
  const clienteSinUbicar = cliente && (cliente.latitud == null || cliente.longitud == null);

  // Guarda el archivo seleccionado y limpia estados previos.
  const elegirArchivo = (e) => {
    const archivo = e.target.files[0];
    if (archivo) {
      setFile(archivo);
      setError("");
      setResultado(null);
    }
  };

  // Termina el envio mostrando el resultado o el error. Recibe la promesa de la API.
  const procesar = (promesa, alTerminarBien) => {
    setCargando(true);
    setError("");
    setResultado(null);
    promesa
      .then((data) => {
        setResultado(data);
        alTerminarBien?.();
      })
      .catch((err) => setError(err.message || "Error al procesar la solicitud"))
      .finally(() => setCargando(false));
  };

  // Envía el Excel; si viene de correo incluye conversacion_id para cerrar el hilo.
  const aceptarExcel = () => {
    if (!clienteId || !file) return;
    procesar(
      aceptarSolicitud(Number(clienteId), file, {
        referencia: referencia.trim() || undefined,
        contacto_origen: contactoOrigen.trim() || undefined,
        conversacion_id: desdeCorreo?.conversacion_id || undefined,
        fecha_programada: fechaProgramada || undefined,
      })
    );
  };

  // Valida y envía los pedidos escritos a mano (C11-02).
  const registrarManual = () => {
    if (!clienteId) return;
    const { errores, pedidos } = validarPedidosManual(filas);
    setErroresFilas(errores);
    if (Object.keys(errores).length) {
      setError("Revisa los pedidos marcados en rojo.");
      return;
    }
    procesar(
      registrarSolicitudManual({
        cliente_id: Number(clienteId),
        referencia: referencia.trim() || null,
        contacto_origen: contactoOrigen.trim() || null,
        fecha_programada: fechaProgramada || null,
        pedidos,
      }),
      () => setFilas([{ ...PEDIDO_VACIO }])
    );
  };

  const puedeEnviar = Boolean(clienteId) && !clienteSinUbicar && !cargando && (modo === "manual" || file);

  return (
    <div className="space-y-6">
      <SectionCard
        title="Datos de la solicitud"
        subtitle="Completa los campos obligatorios (marcados con *)"
      >
        <div className="space-y-4">
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

          {clienteSinUbicar && (
            <div className="flex items-start gap-2 rounded-xl bg-warning-soft px-3.5 py-3 text-sm text-warning-strong">
              <MapPinOff size={18} className="mt-0.5 shrink-0" />
              <span>La dirección de recojo de este cliente no está ubicada en el mapa. Ubícala en <b>Clientes</b> antes de registrar la solicitud.</span>
            </div>
          )}

          <div className="grid gap-4 sm:grid-cols-2">
            <Input
              label="Fecha de recojo"
              type="date"
              min={hoyISO()}
              value={fechaProgramada}
              onChange={(e) => setFechaProgramada(e.target.value)}
              hint="Día que el cliente pidió (opcional)"
            />
            <Input
              label="Referencia (opcional)"
              placeholder="Ej. OC-2026-001"
              value={referencia}
              onChange={(e) => setReferencia(e.target.value)}
            />
          </div>

          <Input
            label="Contacto en origen (opcional)"
            placeholder="Nombre o teléfono del responsable de carga"
            value={contactoOrigen}
            onChange={(e) => setContactoOrigen(e.target.value)}
          />
        </div>
      </SectionCard>

      <SectionCard
        title="Pedidos *"
        subtitle={modo === "excel" ? "Sube el Excel del cliente (.xlsx)" : "Escribe los pedidos que el cliente dictó por teléfono"}
      >
        <div className="mb-4 flex w-fit gap-1 rounded-xl border border-slate-200 bg-slate-50 p-1">
          {[
            { id: "excel", label: "Con Excel", icon: FileSpreadsheet },
            { id: "manual", label: "Ingresar a mano", icon: PenLine },
          ].map(({ id, label, icon: Icono }) => (
            <button
              key={id}
              type="button"
              onClick={() => { setModo(id); setError(""); setResultado(null); }}
              className={`inline-flex items-center gap-1.5 rounded-lg px-3.5 py-2 text-sm font-medium transition-colors ${
                modo === id ? "bg-white text-brand-700 shadow-sm" : "text-slate-500 hover:text-slate-700"
              }`}
            >
              <Icono size={16} /> {label}
            </button>
          ))}
        </div>

        {modo === "excel" ? (
          <>
            <input
              id="excel-recojo-form"
              type="file"
              accept=".xlsx"
              className="hidden"
              onChange={elegirArchivo}
            />

            {!file ? (
              <label htmlFor="excel-recojo-form" className="block cursor-pointer">
                <EmptyState
                  icon={UploadCloud}
                  title="Selecciona el Excel de pedidos"
                  description="Haz clic aquí para elegir el archivo .xlsx con los pedidos del cliente."
                />
              </label>
            ) : (
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
          </>
        ) : (
          <EditorPedidosManual filas={filas} onCambiar={(f) => { setFilas(f); setErroresFilas({}); setError(""); }} errores={erroresFilas} />
        )}

        <Button
          onClick={modo === "excel" ? aceptarExcel : registrarManual}
          disabled={!puedeEnviar}
          size="lg"
          block
          icon={cargando ? undefined : modo === "excel" ? FileSpreadsheet : PenLine}
          className="mt-5"
        >
          {cargando ? (
            <>
              <Loader2 className="animate-spin" size={20} />
              Procesando solicitud…
            </>
          ) : modo === "excel" ? (
            "Aceptar solicitud"
          ) : (
            `Registrar solicitud con ${filas.length} pedido${filas.length !== 1 ? "s" : ""}`
          )}
        </Button>
      </SectionCard>

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
              {resultado.geocodificacion_en_segundo_plano ? (
                <p className="text-sm text-slate-600">
                  {resultado.pedidos_creados} pedidos creados · ubicándose en el mapa en segundo
                  plano (puede tardar unos minutos).
                </p>
              ) : (
                <p className="text-sm text-slate-600">
                  {resultado.pedidos_creados} pedidos creados ·{" "}
                  {resultado.pedidos_geocodificados} geocodificados
                  {resultado.pedidos_sin_ubicar > 0 &&
                    ` · ${resultado.pedidos_sin_ubicar} sin ubicar`}
                  .
                </p>
              )}
            </div>
          </div>

          {resultado.filas_rechazadas && resultado.filas_rechazadas.length > 0 && (
            <div className="mt-4 rounded-card border border-amber-200 bg-amber-50 p-4">
              <div className="flex items-center gap-2">
                <AlertTriangle size={16} className="text-amber-700" />
                <p className="text-sm font-semibold text-amber-800">
                  {resultado.filas_rechazadas.length} pedido(s) no se registraron:
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

      {error && (
        <div className="rounded-card border border-red-200 bg-red-50 p-5 shadow-card">
          <div className="flex items-start gap-3">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-red-100 text-red-600">
              <FileX2 size={20} />
            </span>
            <div>
              <h3 className="text-sm font-semibold text-red-800">
                No se registró la solicitud
              </h3>
              <p className="mt-0.5 text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
