import { useEffect, useMemo, useState } from "react";
import { UserPlus, Users, Truck, X, Phone, IdCard, Mail, CheckCircle2, AlertCircle, Check, Pencil, Trash2, Camera, KeyRound } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import KpiCard from "../components/ui/KpiCard";
import DataTable from "../components/ui/DataTable";
import Input from "../components/ui/Input";
import PasswordInput from "../components/ui/PasswordInput";
import Button from "../components/ui/Button";
import Badge, { EstadoBadge } from "../components/ui/Badge";
import Modal from "../components/ui/Modal";
import SectionCard from "../components/ui/SectionCard";
import { listarConductores, crearConductor, actualizarConductor, eliminarConductor, subirFotoConductor, restablecerContrasenaConductor, urlMedia } from "../services/api";
import { validarNombre, validarCorreo, validarPassword, validarTelefono, validarDni, soloDigitos } from "../utils/validaciones";

// Apartado de conductores: ficha completa (nombre, teléfono, DNI), vehículo
// asignado y detalle en un modal. La cuenta (correo/contraseña) es la que el
// conductor usa en la app móvil.
export default function Conductores() {
  const [conductores, setConductores] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [seleccionado, setSeleccionado] = useState(null);

  const [form, setForm] = useState({ nombre: "", correo: "", contrasena: "", telefono: "", dni: "" });
  const [errores, setErrores] = useState({});
  const [aviso, setAviso] = useState(null);
  const [guardando, setGuardando] = useState(false);

  const cargar = async () => {
    setCargando(true);
    try {
      setConductores(await listarConductores());
    } catch (err) {
      console.error("No se pudo cargar conductores:", err.message);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    cargar();
  }, []);

  // KPIs calculados desde el array ya cargado (sin petición extra).
  const kpis = useMemo(() => {
    const total = conductores.length;
    const activos = conductores.filter((c) => c.estado).length;
    const sinVehiculo = conductores.filter((c) => c.estado && !c.vehiculo).length;
    const inactivos = conductores.filter((c) => !c.estado).length;
    // Conductores que pidieron restablecer su clave y siguen pendientes (extra CUS-04).
    const solicitudes = conductores.filter((c) => c.solicito_restablecimiento).length;
    return { total, activos, sinVehiculo, inactivos, solicitudes };
  }, [conductores]);

  // Actualiza un campo y limpia su error mientras el usuario corrige.
  const set = (campo, transform) => (e) => {
    const valor = transform ? transform(e.target.value) : e.target.value;
    setForm((f) => ({ ...f, [campo]: valor }));
    setErrores((er) => ({ ...er, [campo]: "" }));
  };

  const validar = () => ({
    nombre: validarNombre(form.nombre),
    correo: validarCorreo(form.correo),
    contrasena: validarPassword(form.contrasena),
    telefono: validarTelefono(form.telefono),
    dni: validarDni(form.dni),
  });

  const registrar = async (e) => {
    e.preventDefault();
    setAviso(null);

    const errs = validar();
    if (Object.values(errs).some(Boolean)) {
      setErrores(errs);
      return;
    }

    setGuardando(true);
    try {
      const c = await crearConductor({
        nombre: form.nombre,
        correo: form.correo,
        contrasena: form.contrasena,
        telefono: form.telefono || null,
        dni: form.dni || null,
      });
      setAviso({ ok: true, texto: `Conductor ${c.nombre} registrado (${c.codigo}).` });
      setForm({ nombre: "", correo: "", contrasena: "", telefono: "", dni: "" });
      cargar();
    } catch (err) {
      setAviso({ ok: false, texto: err.message });
    } finally {
      setGuardando(false);
    }
  };

  // Columnas para DataTable
  const columnas = [
    {
      key: "codigo",
      header: "Código",
      render: (c) => <span className="font-medium text-slate-800 nums">{c.codigo || "—"}</span>,
    },
    {
      key: "nombre",
      header: "Nombre",
      render: (c) => (
        <span className="flex items-center gap-2">
          <span className="text-slate-700">{c.nombre || "—"}</span>
          {c.solicito_restablecimiento && (
            <span className="inline-flex items-center gap-1 rounded-full bg-warning-soft px-2 py-0.5 text-xs font-semibold text-warning-strong"
              title="Solicitó restablecer su contraseña">
              <KeyRound size={12} /> Solicitó clave
            </span>
          )}
        </span>
      ),
    },
    {
      key: "telefono",
      header: "Teléfono",
      render: (c) => <span className="text-slate-600 nums">{c.telefono || "—"}</span>,
    },
    {
      key: "vehiculo",
      header: "Vehículo",
      render: (c) =>
        c.vehiculo
          ? <Badge tono="info"><Truck size={13} className="inline mr-1" />{c.vehiculo.placa}</Badge>
          : <span className="text-slate-400">Sin vehículo</span>,
    },
    {
      key: "estado",
      header: "Estado",
      render: (c) => <EstadoBadge estado={!c.estado ? "INACTIVO" : c.en_ruta ? "EN_RUTA" : "DISPONIBLE"} />,
    },
  ];

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-in">
      <PageHeader
        titulo="Conductores"
        subtitulo="Registra y consulta a los conductores de reparto."
      />

      {/* Aviso: conductores que solicitaron restablecer su contraseña (extra CUS-04) */}
      {kpis.solicitudes > 0 && (
        <div className="flex items-center gap-2 rounded-xl bg-warning-soft px-4 py-3 text-sm text-warning-strong animate-fade-up">
          <KeyRound size={18} className="shrink-0" />
          <span>
            <b>{kpis.solicitudes}</b> {kpis.solicitudes === 1 ? "conductor solicitó" : "conductores solicitaron"} restablecer su contraseña.
            Ábrelos (marcados abajo) y usa <b>"Restablecer contraseña"</b>.
          </span>
        </div>
      )}

      {/* KPIs derivados de la lista cargada */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 animate-fade-up">
        <KpiCard label="Total" value={kpis.total} icon={Users} tone="brand" />
        <KpiCard label="Activos" value={kpis.activos} icon={Users} tone="success" />
        <KpiCard label="Sin vehículo" value={kpis.sinVehiculo} icon={Truck} tone="warning" />
        <KpiCard label="Inactivos" value={kpis.inactivos} icon={Users} tone="danger" />
      </div>

      <div className="grid gap-6 lg:grid-cols-3 animate-fade-up" style={{ animationDelay: "60ms" }}>
        {/* Formulario de alta */}
        <SectionCard title="Registrar conductor" className="lg:col-span-1">
          <form onSubmit={registrar} noValidate className="space-y-4">
            <Input label="Nombre completo" required value={form.nombre} onChange={set("nombre")}
              placeholder="Ej. Juan Pérez" error={errores.nombre} hint="Al menos 3 caracteres" />
            <Input label="Correo (acceso a la app)" type="email" required value={form.correo} onChange={set("correo")}
              placeholder="conductor@siol.com" error={errores.correo} hint="Formato nombre@dominio.com" />
            <div>
              <PasswordInput label="Contraseña inicial" required value={form.contrasena} onChange={set("contrasena")}
                placeholder="Escribe la contraseña" error={errores.contrasena} autoComplete="new-password" />
              <RequisitosPassword value={form.contrasena} />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Input label="Teléfono" inputMode="numeric" value={form.telefono} onChange={set("telefono", (v) => soloDigitos(v, 9))}
                placeholder="987654321" error={errores.telefono} hint="9 dígitos (empieza en 9)" />
              <Input label="DNI" inputMode="numeric" value={form.dni} onChange={set("dni", (v) => soloDigitos(v, 8))}
                placeholder="12345678" error={errores.dni} hint="8 dígitos" />
            </div>
            <Button type="submit" icon={UserPlus} block disabled={guardando}>
              {guardando ? "Registrando…" : "Registrar conductor"}
            </Button>
            {aviso && (
              <div className={`flex items-center gap-2 rounded-xl px-3.5 py-3 text-sm ${aviso.ok ? "bg-success-soft text-success-strong" : "bg-danger-soft text-danger-strong"}`}>
                {aviso.ok ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
                <span>{aviso.texto}</span>
              </div>
            )}
          </form>
        </SectionCard>

        {/* Tabla de conductores */}
        <div className="lg:col-span-2">
          <DataTable
            columns={columnas}
            rows={conductores}
            rowKey={(c) => c.usuario_id}
            loading={cargando}
            empty={{
              icon: Users,
              title: "Aún no hay conductores registrados",
              description: "Usa el formulario de la izquierda para añadir el primer conductor.",
            }}
            onRowClick={(c) => setSeleccionado(c)}
          />
        </div>
      </div>

      <Modal open={!!seleccionado} onClose={() => setSeleccionado(null)} variant="center">
        {seleccionado && (
          <DetalleConductor
            conductor={seleccionado}
            onCerrar={() => setSeleccionado(null)}
            onCambios={() => { setSeleccionado(null); cargar(); }}
          />
        )}
      </Modal>
    </div>
  );
}

// Detalle del conductor con tres modos: ver la ficha, editarla, o confirmar su
// eliminación. `onCambios` se llama tras editar/eliminar (cierra + recarga lista).
function DetalleConductor({ conductor: c, onCerrar, onCambios }) {
  const [modo, setModo] = useState("ver"); // "ver" | "editar" | "confirmar" | "clave"
  const [form, setForm] = useState({ nombre: c.nombre || "", telefono: c.telefono || "", dni: c.dni || "" });
  const [errores, setErrores] = useState({});
  const [aviso, setAviso] = useState(null);
  const [trabajando, setTrabajando] = useState(false);
  const [subiendoFoto, setSubiendoFoto] = useState(false);
  // CUS-04: restablecer contraseña (nueva clave + estado del proceso).
  const [nuevaClave, setNuevaClave] = useState("");
  const [errorClave, setErrorClave] = useState("");
  const [claveOk, setClaveOk] = useState(false);

  // Actualiza un campo del formulario y limpia su error.
  const set = (campo, transform) => (e) => {
    const valor = transform ? transform(e.target.value) : e.target.value;
    setForm((f) => ({ ...f, [campo]: valor }));
    setErrores((er) => ({ ...er, [campo]: "" }));
  };

  // Valida y guarda la edición de la ficha.
  const guardar = async () => {
    const errs = {
      nombre: validarNombre(form.nombre),
      telefono: validarTelefono(form.telefono),
      dni: validarDni(form.dni),
    };
    if (Object.values(errs).some(Boolean)) {
      setErrores(errs);
      return;
    }
    setTrabajando(true);
    setAviso(null);
    try {
      await actualizarConductor(c.usuario_id, {
        nombre: form.nombre,
        telefono: form.telefono || null,
        dni: form.dni || null,
      });
      onCambios();
    } catch (err) {
      setAviso({ texto: err.message });
      setTrabajando(false);
    }
  };

  // Elimina (desactiva) el conductor.
  const eliminar = async () => {
    setTrabajando(true);
    setAviso(null);
    try {
      await eliminarConductor(c.usuario_id);
      onCambios();
    } catch (err) {
      setAviso({ texto: err.message });
      setTrabajando(false);
      setModo("ver");
    }
  };

  // Sube la foto elegida y recarga la lista. Recibe: el evento del <input file>.
  const cambiarFoto = async (e) => {
    const archivo = e.target.files?.[0];
    if (!archivo) return;
    setSubiendoFoto(true);
    setAviso(null);
    try {
      await subirFotoConductor(c.usuario_id, archivo);
      onCambios();
    } catch (err) {
      setAviso({ texto: err.message });
      setSubiendoFoto(false);
    }
  };

  // CUS-04: valida y fija la nueva contraseña del conductor. No cierra el modal:
  // muestra confirmación para que el admin pueda comunicarle la clave.
  const restablecer = async () => {
    const error = validarPassword(nuevaClave);
    if (error) {
      setErrorClave(error);
      return;
    }
    setTrabajando(true);
    setAviso(null);
    try {
      await restablecerContrasenaConductor(c.usuario_id, nuevaClave);
      setClaveOk(true);
      setNuevaClave("");
    } catch (err) {
      setAviso({ texto: err.message });
    } finally {
      setTrabajando(false);
    }
  };

  return (
    <>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          {c.foto_url ? (
            <img
              src={urlMedia(c.foto_url)}
              alt={c.nombre || "Conductor"}
              className="h-12 w-12 rounded-full object-cover ring-2 ring-brand-100"
            />
          ) : (
            <span className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-600 text-lg font-bold text-white">
              {(c.nombre || "?").charAt(0).toUpperCase()}
            </span>
          )}
          <div>
            <h2 className="font-bold text-slate-900">{c.nombre || "Conductor"}</h2>
            <p className="text-sm text-slate-500 nums">{c.codigo}</p>
          </div>
        </div>
        <button onClick={onCerrar} aria-label="Cerrar" className="rounded-lg p-2 text-slate-500 hover:bg-slate-100">
          <X size={20} />
        </button>
      </div>

      {aviso && (
        <div className="mt-4 flex items-center gap-2 rounded-xl bg-danger-soft px-3.5 py-3 text-sm text-danger-strong">
          <AlertCircle size={18} /> <span>{aviso.texto}</span>
        </div>
      )}

      {modo === "ver" && (
        <>
          <div className="mt-6 space-y-3">
            <Dato icono={Mail} etiqueta="Correo" valor={c.correo} />
            <Dato icono={Phone} etiqueta="Teléfono" valor={c.telefono || "—"} />
            <Dato icono={IdCard} etiqueta="DNI" valor={c.dni || "—"} />
            <Dato icono={Truck} etiqueta="Vehículo asignado"
              valor={c.vehiculo ? `${c.vehiculo.placa}${c.vehiculo.codigo ? ` (${c.vehiculo.codigo})` : ""}` : "Sin vehículo asignado"} />
          </div>
          {c.solicito_restablecimiento && (
            <div className="mt-4 flex items-start gap-2 rounded-xl bg-warning-soft px-3.5 py-3 text-sm text-warning-strong">
              <KeyRound size={18} className="shrink-0" />
              <span>Este conductor <b>solicitó restablecer su contraseña</b>. Genera una nueva y comunícasela.</span>
            </div>
          )}
          <div className="mt-6 flex gap-2">
            <Button variant="secondary" icon={Pencil} block onClick={() => { setAviso(null); setModo("editar"); }}>Editar</Button>
            <Button variant="danger" icon={Trash2} block onClick={() => { setAviso(null); setModo("confirmar"); }}>Eliminar</Button>
          </div>
          <Button variant="secondary" icon={KeyRound} block className="mt-2"
            onClick={() => { setAviso(null); setClaveOk(false); setErrorClave(""); setNuevaClave(""); setModo("clave"); }}>
            Restablecer contraseña
          </Button>
        </>
      )}

      {modo === "clave" && (
        <div className="mt-6 space-y-4">
          {claveOk ? (
            <>
              <div className="flex items-start gap-3 rounded-xl bg-success-soft px-4 py-3 text-sm text-success-strong">
                <CheckCircle2 size={20} className="shrink-0" />
                <span>Contraseña restablecida. Comunícasela a <b>{c.nombre || "el conductor"}</b> para que entre a la app.</span>
              </div>
              <Button block onClick={() => setModo("ver")}>Listo</Button>
            </>
          ) : (
            <>
              <p className="text-sm text-slate-500">
                Define una nueva contraseña para <b>{c.nombre || "el conductor"}</b>. La usará para iniciar sesión en la app móvil.
              </p>
              <div>
                <PasswordInput label="Nueva contraseña" value={nuevaClave}
                  onChange={(e) => { setNuevaClave(e.target.value); setErrorClave(""); }}
                  placeholder="Escribe la nueva contraseña" error={errorClave} autoComplete="new-password" />
                <RequisitosPassword value={nuevaClave} />
              </div>
              <div className="flex gap-2">
                <Button variant="secondary" block onClick={() => { setModo("ver"); setErrorClave(""); setNuevaClave(""); }} disabled={trabajando}>Cancelar</Button>
                <Button icon={KeyRound} block onClick={restablecer} disabled={trabajando}>{trabajando ? "Guardando…" : "Restablecer"}</Button>
              </div>
            </>
          )}
        </div>
      )}

      {modo === "editar" && (
        <div className="mt-6 space-y-4">
          <Input label="Nombre completo" value={form.nombre} onChange={set("nombre")} error={errores.nombre} hint="Al menos 3 caracteres" />
          <div className="grid grid-cols-2 gap-4">
            <Input label="Teléfono" inputMode="numeric" value={form.telefono} onChange={set("telefono", (v) => soloDigitos(v, 9))}
              error={errores.telefono} hint="9 dígitos" />
            <Input label="DNI" inputMode="numeric" value={form.dni} onChange={set("dni", (v) => soloDigitos(v, 8))}
              error={errores.dni} hint="8 dígitos" />
          </div>
          <label className="flex cursor-pointer items-center justify-center gap-2 rounded-xl border border-slate-200 px-4 py-3 text-sm font-medium text-slate-600 hover:bg-slate-50">
            <Camera size={18} className="text-slate-400" />
            {subiendoFoto ? "Subiendo…" : c.foto_url ? "Cambiar foto" : "Subir foto"}
            <input type="file" accept="image/*" className="hidden" onChange={cambiarFoto} disabled={subiendoFoto} />
          </label>
          <div className="flex gap-2">
            <Button variant="secondary" block onClick={() => { setModo("ver"); setErrores({}); }} disabled={trabajando}>Cancelar</Button>
            <Button icon={Check} block onClick={guardar} disabled={trabajando}>{trabajando ? "Guardando…" : "Guardar"}</Button>
          </div>
        </div>
      )}

      {modo === "confirmar" && (
        <div className="mt-6 space-y-4">
          <div className="flex items-start gap-3 rounded-xl bg-danger-soft px-4 py-3 text-sm text-danger-strong">
            <AlertCircle size={20} className="shrink-0" />
            <span>¿Eliminar a <b>{c.nombre || "este conductor"}</b>? Se quitará de la lista (su historial se conserva).</span>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" block onClick={() => setModo("ver")} disabled={trabajando}>Cancelar</Button>
            <Button variant="danger" icon={Trash2} block onClick={eliminar} disabled={trabajando}>{trabajando ? "Eliminando…" : "Sí, eliminar"}</Button>
          </div>
        </div>
      )}
    </>
  );
}

function Dato({ etiqueta, valor, icono: Icono }) {
  return (
    <div className="flex items-center gap-3 rounded-xl bg-slate-50 px-4 py-3 text-sm">
      <Icono size={18} className="text-slate-400" />
      <div>
        <p className="text-xs text-slate-400">{etiqueta}</p>
        <p className="font-medium text-slate-700">{valor}</p>
      </div>
    </div>
  );
}

// Lista de requisitos de la contraseña que se va marcando en vivo al escribir.
function RequisitosPassword({ value }) {
  if (!value) return null;
  const reglas = [
    { ok: value.length >= 8, texto: "Al menos 8 caracteres" },
    { ok: /[A-Z]/.test(value), texto: "Una mayúscula" },
    { ok: /[a-z]/.test(value), texto: "Una minúscula" },
    { ok: /\d/.test(value), texto: "Un número" },
    { ok: /[^A-Za-z0-9]/.test(value), texto: "Un carácter especial (!@#$…)" },
  ];
  return (
    <ul className="mt-2 space-y-1">
      {reglas.map((r) => (
        <li key={r.texto} className={`flex items-center gap-2 text-xs ${r.ok ? "text-success-strong" : "text-slate-400"}`}>
          <span className={`flex h-4 w-4 items-center justify-center rounded-full ${r.ok ? "bg-success-soft" : "bg-slate-100"}`}>
            <Check size={11} />
          </span>
          {r.texto}
        </li>
      ))}
    </ul>
  );
}
