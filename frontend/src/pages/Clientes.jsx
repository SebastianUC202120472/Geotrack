import { useEffect, useMemo, useState } from "react";
import { Building2, Plus, CheckCircle2, AlertCircle, X, Pencil, Trash2, Check, IdCard, Mail, MapPin, KeyRound, Copy, ShieldOff, ShieldCheck, MapPinOff, RotateCw, Search } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import KpiCard from "../components/ui/KpiCard";
import DataTable from "../components/ui/DataTable";
import SectionCard from "../components/ui/SectionCard";
import Input from "../components/ui/Input";
import Button from "../components/ui/Button";
import Modal from "../components/ui/Modal";
import Badge from "../components/ui/Badge";
import ConfirmDialog from "../components/ui/ConfirmDialog";
import MapaPicker from "../components/MapaPicker";
import { listarClientes, crearCliente, actualizarCliente, eliminarCliente, generarAccesoPortal, revocarAccesoPortal, reintentarUbicacionCliente, fijarUbicacionCliente, buscarDireccion } from "../services/api";
import { validarCorreo } from "../utils/validaciones";

// Valida el RUC en pantalla: vacio (opcional) o 11 digitos con prefijo 10/15/16/17/20. Recibe el texto.
const validarRuc = (v) => {
  const ruc = (v || "").replace(/\s/g, "");
  if (!ruc) return "";
  if (!/^\d{11}$/.test(ruc)) return "El RUC debe tener exactamente 11 dígitos";
  if (!/^(10|15|16|17|20)/.test(ruc)) return "El RUC debe empezar con 10, 15, 16, 17 o 20";
  return "";
};

// Dice si el cliente tiene direccion de recojo pero no se pudo ubicar en el mapa. Recibe el cliente.
const sinUbicar = (c) => Boolean(c.direccion_origen) && (c.latitud == null || c.longitud == null);

// Pagina de administracion de clientes corporativos: alta, edicion y baja.
export default function Clientes() {
  const [clientes, setClientes] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [seleccionado, setSeleccionado] = useState(null);
  const [modoInicial, setModoInicial] = useState("ver");

  const [form, setForm] = useState({ razon_social: "", identificador_unico: "", contacto: "", direccion_origen: "" });
  const [error, setError] = useState("");
  const [errorRuc, setErrorRuc] = useState("");
  const [aviso, setAviso] = useState(null);
  const [guardando, setGuardando] = useState(false);

  // Recarga la lista de clientes desde el backend.
  const cargar = async () => {
    try {
      setClientes(await listarClientes());
    } catch (err) {
      console.error("No se pudo cargar clientes:", err.message);
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    let activo = true;
    listarClientes()
      .then((d) => activo && setClientes(d))
      .catch(() => {})
      .finally(() => activo && setCargando(false));
    return () => { activo = false; };
  }, []);

  const kpis = useMemo(() => ({
    total: clientes.length,
    conRuc: clientes.filter((c) => c.identificador_unico).length,
    conPortal: clientes.filter((c) => c.acceso_activo).length,
    sinUbicar: clientes.filter(sinUbicar).length,
  }), [clientes]);

  const registrar = async (e) => {
    e.preventDefault();
    setAviso(null);
    if (form.razon_social.trim().length < 3) {
      setError("La razón social debe tener al menos 3 caracteres.");
      return;
    }
    const problemaRuc = validarRuc(form.identificador_unico);
    if (problemaRuc) {
      setErrorRuc(problemaRuc);
      return;
    }
    setError("");
    setGuardando(true);
    try {
      const c = await crearCliente({
        razon_social: form.razon_social.trim(),
        identificador_unico: form.identificador_unico.trim() || null,
        contacto: form.contacto.trim() || null,
        direccion_origen: form.direccion_origen.trim(),
      });
      setAviso(sinUbicar(c)
        ? { ok: false, texto: `Cliente ${c.razon_social} registrado (${c.codigo || "—"}), pero su dirección de recojo no se pudo ubicar en el mapa. Ábrelo y márcala.` }
        : { ok: true, texto: `Cliente ${c.razon_social} registrado (${c.codigo || "—"}).` });
      setForm({ razon_social: "", identificador_unico: "", contacto: "", direccion_origen: "" });
      cargar();
    } catch (err) {
      setAviso({ ok: false, texto: err.message });
    } finally {
      setGuardando(false);
    }
  };

  const columnas = [
    { key: "codigo", header: "Código", render: (c) => <span className="font-medium text-slate-800 nums">{c.codigo || "—"}</span> },
    {
      key: "razon_social",
      header: "Razón social",
      render: (c) => (
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-slate-700">{c.razon_social}</span>
          {sinUbicar(c) && <Badge tono="warning"><MapPinOff size={12} />Sin ubicar</Badge>}
          {c.acceso_activo && <Badge tono="success"><ShieldCheck size={12} />Portal</Badge>}
        </div>
      ),
    },
    { key: "identificador_unico", header: "RUC", render: (c) => <span className="text-slate-600 nums">{c.identificador_unico || "—"}</span> },
    { key: "contacto", header: "Contacto", render: (c) => <span className="text-slate-600">{c.contacto || "—"}</span> },
    {
      key: "acciones",
      header: "",
      render: (c) => (
        <div className="flex justify-end gap-1">
          <Button variant="ghost" size="sm" icon={KeyRound}
            onClick={(e) => { e.stopPropagation(); setModoInicial("portal"); setSeleccionado(c); }}>Portal</Button>
          <Button variant="ghost" size="sm" icon={Pencil}
            onClick={(e) => { e.stopPropagation(); setModoInicial("editar"); setSeleccionado(c); }}>Editar</Button>
          <Button variant="ghost" size="sm" icon={Trash2}
            onClick={(e) => { e.stopPropagation(); setModoInicial("confirmar"); setSeleccionado(c); }}>Baja</Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-in">
      <PageHeader titulo="Clientes Corporativos" subtitulo="Registra y administra las empresas a las que prestas el servicio." />

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 animate-fade-up">
        <KpiCard label="Total" value={kpis.total} icon={Building2} tone="brand" />
        <KpiCard label="Con RUC" value={kpis.conRuc} icon={IdCard} tone="info" />
        <KpiCard label="Con acceso al portal" value={kpis.conPortal} icon={ShieldCheck} tone="success" />
        <KpiCard label="Sin ubicar" value={kpis.sinUbicar} icon={MapPinOff} tone="warning" />
      </div>

      {kpis.sinUbicar > 0 && (
        <div className="flex items-center gap-2 rounded-xl bg-warning-soft px-4 py-3 text-sm text-warning-strong animate-fade-up">
          <MapPinOff size={18} className="shrink-0" />
          <span>
            <b>{kpis.sinUbicar}</b> {kpis.sinUbicar === 1 ? "cliente tiene" : "clientes tienen"} la dirección de recojo sin ubicar en el mapa:
            sus solicitudes no podrán entrar a una ruta de recojo. Ábrelos y márcala.
          </span>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3 animate-fade-up" style={{ animationDelay: "60ms" }}>
        <SectionCard title="Registrar cliente" className="lg:col-span-1">
          <form onSubmit={registrar} noValidate className="space-y-4">
            <Input label="Razón social" required value={form.razon_social}
              onChange={(e) => { setForm((f) => ({ ...f, razon_social: e.target.value })); setError(""); }}
              placeholder="Ej. Ripley S.A." error={error} hint="Nombre legal de la empresa" />
            <Input label="RUC" value={form.identificador_unico} inputMode="numeric"
              onChange={(e) => { setForm((f) => ({ ...f, identificador_unico: e.target.value.replace(/\D/g, "").slice(0, 11) })); setErrorRuc(""); }}
              placeholder="20123456789" error={errorRuc} hint="11 dígitos (opcional)" />
            <Input label="Contacto" value={form.contacto}
              onChange={(e) => setForm((f) => ({ ...f, contacto: e.target.value }))}
              placeholder="correo / teléfono" hint="Opcional" />
            <Input label="Dirección de recojo" required value={form.direccion_origen}
              onChange={(e) => setForm((f) => ({ ...f, direccion_origen: e.target.value }))}
              placeholder="Ej. Av. Primavera 123, Miraflores"
              hint="Separa el distrito con una coma. Se geocodifica al guardar." />
            <Button type="submit" icon={Plus} block disabled={guardando}>{guardando ? "Registrando…" : "Registrar cliente"}</Button>
            {aviso && (
              <div className={`flex items-center gap-2 rounded-xl px-3.5 py-3 text-sm ${aviso.ok ? "bg-success-soft text-success-strong" : "bg-danger-soft text-danger-strong"}`}>
                {aviso.ok ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
                <span>{aviso.texto}</span>
              </div>
            )}
          </form>
        </SectionCard>

        <div className="lg:col-span-2">
          <DataTable columns={columnas} rows={clientes} rowKey={(c) => c.id} loading={cargando}
            empty={{ icon: Building2, title: "Aún no hay clientes", description: "Usa el formulario para registrar la primera empresa." }}
            onRowClick={(c) => { setModoInicial("ver"); setSeleccionado(c); }} />
        </div>
      </div>

      <Modal open={!!seleccionado} onClose={() => { setSeleccionado(null); setModoInicial("ver"); }} variant="center">
        {seleccionado && (
          <DetalleCliente cliente={seleccionado} modoInicial={modoInicial}
            onCerrar={() => { setSeleccionado(null); setModoInicial("ver"); }}
            onCambios={() => { setSeleccionado(null); setModoInicial("ver"); cargar(); }} />
        )}
      </Modal>
    </div>
  );
}

// Modal de detalle de cliente con modos ver, editar y baja. Recibe el cliente y modoInicial.
function DetalleCliente({ cliente: c, onCerrar, onCambios, modoInicial = "ver" }) {
  const [modo, setModo] = useState(modoInicial);
  const [form, setForm] = useState({ razon_social: c.razon_social || "", identificador_unico: c.identificador_unico || "", contacto: c.contacto || "", direccion_origen: c.direccion_origen || "" });
  const [aviso, setAviso] = useState(null);
  const [trabajando, setTrabajando] = useState(false);

  const [correoPortal, setCorreoPortal] = useState(c.correo_portal || (validarCorreo(c.contacto) ? "" : c.contacto) || "");
  const [credenciales, setCredenciales] = useState(null);
  const [errorPortal, setErrorPortal] = useState("");
  const [confirmarRevocar, setConfirmarRevocar] = useState(false);
  const [ubicacion, setUbicacion] = useState({ lat: c.latitud ?? null, lng: c.longitud ?? null, busqueda: c.direccion_origen || "" });
  const [buscando, setBuscando] = useState(false);

  const guardar = async () => {
    if (form.razon_social.trim().length < 3) { setAviso({ texto: "La razón social debe tener al menos 3 caracteres." }); return; }
    const problemaRuc = validarRuc(form.identificador_unico);
    if (problemaRuc) { setAviso({ texto: problemaRuc }); return; }
    setTrabajando(true); setAviso(null);
    try {
      await actualizarCliente(c.id, {
        razon_social: form.razon_social.trim(),
        identificador_unico: form.identificador_unico.trim() || null,
        contacto: form.contacto.trim() || null,
        direccion_origen: form.direccion_origen.trim() || null,
      });
      onCambios();
    } catch (err) { setAviso({ texto: err.message }); setTrabajando(false); }
  };

  const eliminar = async () => {
    setTrabajando(true); setAviso(null);
    try { await eliminarCliente(c.id); onCambios(); }
    catch (err) { setAviso({ texto: err.message }); setTrabajando(false); setModo("ver"); }
  };

  // Vuelve a intentar ubicar la direccion de recojo con el geocodificador (C07-02).
  const reintentarUbicacion = async () => {
    setTrabajando(true); setAviso(null);
    try { await reintentarUbicacionCliente(c.id); onCambios(); }
    catch (err) { setAviso({ texto: err.message }); setTrabajando(false); }
  };

  // Busca la direccion escrita y mueve el pin al resultado (para marcarla a mano).
  const buscarEnMapa = () => {
    if (!ubicacion.busqueda.trim()) return;
    setBuscando(true); setAviso(null);
    buscarDireccion(ubicacion.busqueda.trim())
      .then((r) => {
        if (r.encontrado) setUbicacion((u) => ({ ...u, lat: r.latitud, lng: r.longitud }));
        else setAviso({ texto: "No se encontró esa dirección. Haz clic en el mapa para marcar el punto." });
      })
      .catch((err) => setAviso({ texto: err.message }))
      .finally(() => setBuscando(false));
  };

  // Guarda el punto de recojo marcado en el mapa (C07-02).
  const guardarUbicacion = async () => {
    if (ubicacion.lat == null) { setAviso({ texto: "Primero marca el punto en el mapa." }); return; }
    setTrabajando(true); setAviso(null);
    try { await fijarUbicacionCliente(c.id, { latitud: ubicacion.lat, longitud: ubicacion.lng }); onCambios(); }
    catch (err) { setAviso({ texto: err.message }); setTrabajando(false); }
  };

  // Genera un nuevo acceso al portal para el correo indicado. La clave solo se muestra esta vez.
  const generarAcceso = async () => {
    const problemaCorreo = validarCorreo(correoPortal);
    if (problemaCorreo) { setErrorPortal(problemaCorreo); return; }
    setTrabajando(true); setErrorPortal("");
    try {
      const datos = await generarAccesoPortal(c.id, correoPortal.trim());
      setCredenciales(datos);
    } catch (err) { setErrorPortal(err.message); }
    finally { setTrabajando(false); }
  };

  // Revoca el acceso al portal del cliente tras confirmarlo; su sesion abierta se corta en la
  // siguiente consulta (no borra sus credenciales).
  const revocarAcceso = async () => {
    setTrabajando(true); setErrorPortal("");
    try { await revocarAccesoPortal(c.id); setConfirmarRevocar(false); onCambios(); }
    catch (err) { setErrorPortal(err.message); setTrabajando(false); setConfirmarRevocar(false); }
  };

  // Copia la clave generada al portapapeles.
  const copiarClave = () => {
    if (credenciales) navigator.clipboard?.writeText(credenciales.clave);
  };

  return (
    <>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <span className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-600 text-white"><Building2 size={22} /></span>
          <div>
            <h2 className="font-bold text-slate-900">{c.razon_social}</h2>
            <p className="text-sm text-slate-500 nums">{c.codigo}</p>
          </div>
        </div>
        <button onClick={onCerrar} aria-label="Cerrar" className="rounded-lg p-2 text-slate-500 hover:bg-slate-100"><X size={20} /></button>
      </div>

      {aviso && (
        <div className="mt-4 flex items-center gap-2 rounded-xl bg-danger-soft px-3.5 py-3 text-sm text-danger-strong">
          <AlertCircle size={18} /> <span>{aviso.texto}</span>
        </div>
      )}

      {modo === "ver" && (
        <>
          {sinUbicar(c) && (
            <div className="mt-4 rounded-xl bg-warning-soft px-4 py-3 text-sm text-warning-strong">
              <p className="flex items-center gap-2 font-semibold"><MapPinOff size={18} /> Dirección de recojo sin ubicar</p>
              <p className="mt-1">No se encontró en el mapa: sus solicitudes no entrarán a una ruta de recojo hasta ubicarla.</p>
              <div className="mt-3 flex gap-2">
                <Button size="sm" variant="secondary" icon={RotateCw} onClick={reintentarUbicacion} disabled={trabajando}>Reintentar</Button>
                <Button size="sm" icon={MapPin} onClick={() => { setAviso(null); setModo("ubicar"); }} disabled={trabajando}>Marcar en el mapa</Button>
              </div>
            </div>
          )}
          <div className="mt-6 space-y-3">
            <Dato icono={IdCard} etiqueta="RUC" valor={c.identificador_unico || "—"} />
            <Dato icono={Mail} etiqueta="Contacto" valor={c.contacto || "—"} />
            <Dato icono={MapPin} etiqueta="Dirección de recojo" valor={c.direccion_origen || "—"} />
            <Dato icono={ShieldCheck} etiqueta="Portal de clientes"
              valor={c.acceso_activo ? `Activo · ${c.codigo_acceso}${c.correo_portal ? ` · ${c.correo_portal}` : ""}` : "Sin acceso"} />
          </div>
          <div className="mt-6 flex gap-2">
            <Button variant="secondary" icon={Pencil} block onClick={() => { setAviso(null); setModo("editar"); }}>Editar</Button>
            <Button variant="danger" icon={Trash2} block onClick={() => { setAviso(null); setModo("confirmar"); }}>Eliminar</Button>
          </div>
          <Button variant="secondary" icon={KeyRound} block className="mt-2" onClick={() => { setAviso(null); setModo("portal"); }}>
            Acceso al portal
          </Button>
        </>
      )}

      {modo === "editar" && (
        <div className="mt-6 space-y-4">
          <Input label="Razón social" value={form.razon_social} onChange={(e) => setForm((f) => ({ ...f, razon_social: e.target.value }))} />
          <Input label="RUC" value={form.identificador_unico} inputMode="numeric" hint="11 dígitos"
            onChange={(e) => setForm((f) => ({ ...f, identificador_unico: e.target.value.replace(/\D/g, "").slice(0, 11) }))} />
          <Input label="Contacto" value={form.contacto} onChange={(e) => setForm((f) => ({ ...f, contacto: e.target.value }))} />
          <Input label="Dirección de recojo" value={form.direccion_origen}
            onChange={(e) => setForm((f) => ({ ...f, direccion_origen: e.target.value }))}
            placeholder="Ej. Av. Primavera 123, Miraflores"
            hint="Separa el distrito con una coma. Se geocodifica al guardar." />
          <div className="flex gap-2">
            <Button variant="secondary" block onClick={() => setModo("ver")} disabled={trabajando}>Cancelar</Button>
            <Button icon={Check} block onClick={guardar} disabled={trabajando}>{trabajando ? "Guardando…" : "Guardar"}</Button>
          </div>
        </div>
      )}

      {modo === "confirmar" && (
        <div className="mt-6 space-y-4">
          <div className="flex items-start gap-3 rounded-xl bg-danger-soft px-4 py-3 text-sm text-danger-strong">
            <AlertCircle size={20} className="shrink-0" />
            <span>
              ¿Dar de baja a <b>{c.razon_social}</b>? Dejará de aparecer en la lista (su historial se conserva)
              {c.acceso_activo ? " y perderá su acceso al portal de inmediato." : "."}
            </span>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" block onClick={() => setModo("ver")} disabled={trabajando}>Cancelar</Button>
            <Button variant="danger" icon={Trash2} block onClick={eliminar} disabled={trabajando}>{trabajando ? "Eliminando…" : "Sí, eliminar"}</Button>
          </div>
        </div>
      )}

      {modo === "ubicar" && (
        <div className="mt-6 space-y-4">
          <div className="flex items-end gap-2">
            <div className="flex-1">
              <Input label="Dirección / lugar" value={ubicacion.busqueda}
                onChange={(e) => setUbicacion((u) => ({ ...u, busqueda: e.target.value }))}
                hint="Busca la dirección y ajusta el pin; o haz clic en el mapa." />
            </div>
            <Button variant="secondary" icon={Search} onClick={buscarEnMapa} disabled={buscando}>{buscando ? "…" : "Buscar"}</Button>
          </div>
          <MapaPicker lat={ubicacion.lat} lng={ubicacion.lng} onChange={(la, lo) => setUbicacion((u) => ({ ...u, lat: la, lng: lo }))} />
          <div className="flex gap-2">
            <Button variant="secondary" block onClick={() => setModo("ver")} disabled={trabajando}>Cancelar</Button>
            <Button icon={Check} block onClick={guardarUbicacion} disabled={trabajando || ubicacion.lat == null}>
              {trabajando ? "Guardando…" : "Guardar ubicación"}
            </Button>
          </div>
        </div>
      )}

      {modo === "portal" && (
        <div className="mt-6 space-y-4">
          {errorPortal && (
            <div className="flex items-center gap-2 rounded-xl bg-danger-soft px-3.5 py-3 text-sm text-danger-strong">
              <AlertCircle size={18} /> <span>{errorPortal}</span>
            </div>
          )}

          {credenciales ? (
            <div className="space-y-3 rounded-xl border border-success/30 bg-success-soft p-4">
              <p className="flex items-center gap-1.5 text-sm font-semibold text-success-strong">
                <CheckCircle2 size={16} /> Acceso generado
              </p>
              <p className="text-xs text-slate-600">Cópiala ahora: la clave no volverá a mostrarse.</p>
              <Dato icono={IdCard} etiqueta="Código de acceso" valor={credenciales.codigoAcceso} />
              <div className="flex items-center gap-2 rounded-xl bg-white px-4 py-3 text-sm">
                <KeyRound size={18} className="text-slate-400" />
                <div className="flex-1">
                  <p className="text-xs text-slate-400">Clave</p>
                  <p className="font-mono font-medium text-slate-800">{credenciales.clave}</p>
                </div>
                <Button variant="ghost" size="sm" icon={Copy} onClick={copiarClave}>Copiar</Button>
              </div>
              <Button block onClick={() => { setCredenciales(null); setModo("ver"); }}>Listo</Button>
            </div>
          ) : (
            <>
              <p className="text-sm text-slate-600">
                Genera o renueva las credenciales que el cliente usará para entrar al panel corporativo del portal.
              </p>
              <Input label="Correo del portal" type="email" value={correoPortal}
                onChange={(e) => { setCorreoPortal(e.target.value); setErrorPortal(""); }}
                placeholder="contacto@empresa.com" hint="Aquí llega el código de verificación de cada ingreso" />
              <Button icon={KeyRound} block onClick={generarAcceso} disabled={trabajando}>
                {trabajando ? "Generando…" : c.acceso_activo ? "Renovar clave de acceso" : "Generar acceso"}
              </Button>
              {c.acceso_activo && (
                <Button variant="danger" icon={ShieldOff} block onClick={() => setConfirmarRevocar(true)} disabled={trabajando}>
                  Revocar acceso
                </Button>
              )}
            </>
          )}

          {!credenciales && (
            <Button variant="secondary" block onClick={() => setModo("ver")} disabled={trabajando}>Volver</Button>
          )}
        </div>
      )}

      <ConfirmDialog
        open={confirmarRevocar}
        titulo="¿Revocar el acceso al portal?"
        mensaje={<><b>{c.razon_social}</b> no podrá volver a entrar al panel corporativo y, si tiene una sesión abierta, se cerrará en su siguiente consulta. Podrás generar un acceso nuevo cuando quieras.</>}
        textoConfirmar="Sí, revocar"
        tono="danger"
        icono={ShieldOff}
        cargando={trabajando}
        onConfirmar={revocarAcceso}
        onCancelar={() => setConfirmarRevocar(false)}
      />
    </>
  );
}

// Fila de dato de la ficha del cliente (icono + etiqueta + valor). Recibe etiqueta, valor e icono.
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
