import { useEffect, useMemo, useState } from "react";
import { UserCog, UserPlus, ShieldCheck, X, Check, KeyRound, CheckCircle2, AlertCircle, Mail } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import KpiCard from "../components/ui/KpiCard";
import DataTable from "../components/ui/DataTable";
import SectionCard from "../components/ui/SectionCard";
import Input from "../components/ui/Input";
import PasswordInput from "../components/ui/PasswordInput";
import Button from "../components/ui/Button";
import Badge, { EstadoBadge } from "../components/ui/Badge";
import Modal from "../components/ui/Modal";
import { listarUsuarios, crearUsuario, actualizarUsuario, restablecerContrasenaUsuario } from "../services/api";

// Roles que se gestionan en el panel (el conductor se administra en su sección).
const ROLES = [
  { valor: "admin", etiqueta: "Administrador" },
  { valor: "almacen", etiqueta: "Almacén" },
];
const etiquetaRol = (r) => ROLES.find((x) => x.valor === r)?.etiqueta || r;

// Gestión de las cuentas del panel (CUS-03): crear, cambiar rol, activar/desactivar y
// restablecer contraseña. Los conductores tienen su propia sección.
export default function Usuarios() {
  const [usuarios, setUsuarios] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [seleccionado, setSeleccionado] = useState(null);

  const [form, setForm] = useState({ correo: "", contrasena: "", rol: "almacen", nombre: "", dni: "", telefono: "", cargo: "" });
  const [aviso, setAviso] = useState(null);
  const [guardando, setGuardando] = useState(false);

  // Sin setCargando(true) síncrono (inicia en true; refresca en callbacks de promesa)
  // para no disparar el error de lint "setState síncrono en effect".
  const cargar = async () => {
    try { setUsuarios(await listarUsuarios()); }
    catch (err) { console.error("No se pudo cargar usuarios:", err.message); }
    finally { setCargando(false); }
  };

  // Carga inicial con setState en callbacks de promesa (evita el lint de effect).
  useEffect(() => {
    let activo = true;
    listarUsuarios()
      .then((d) => activo && setUsuarios(d))
      .catch(() => {})
      .finally(() => activo && setCargando(false));
    return () => { activo = false; };
  }, []);

  const kpis = useMemo(() => ({
    total: usuarios.length,
    activos: usuarios.filter((u) => u.estado).length,
    admins: usuarios.filter((u) => u.rol === "admin").length,
  }), [usuarios]);

  const registrar = async (e) => {
    e.preventDefault();
    setAviso(null);
    setGuardando(true);
    try {
      // Los datos personales son opcionales: solo se envían si tienen valor.
      const u = await crearUsuario({
        correo: form.correo.trim(),
        contrasena: form.contrasena,
        rol: form.rol,
        nombre: form.nombre.trim() || null,
        dni: form.dni.trim() || null,
        telefono: form.telefono.trim() || null,
        cargo: form.cargo.trim() || null,
      });
      setAviso({ ok: true, texto: `Usuario ${u.correo} creado (${u.codigo || "—"}).` });
      setForm({ correo: "", contrasena: "", rol: "almacen", nombre: "", dni: "", telefono: "", cargo: "" });
      cargar();
    } catch (err) {
      setAviso({ ok: false, texto: err.message });
    } finally {
      setGuardando(false);
    }
  };

  const columnas = [
    { key: "codigo", header: "Código", render: (u) => <span className="font-medium text-slate-800 nums">{u.codigo || "—"}</span> },
    {
      key: "correo",
      header: "Usuario",
      render: (u) => (
        <div>
          {u.nombre && <p className="font-medium text-slate-800">{u.nombre}</p>}
          <p className={u.nombre ? "text-xs text-slate-500" : "text-slate-700"}>{u.correo}</p>
        </div>
      ),
    },
    { key: "cargo", header: "Cargo", render: (u) => <span className="text-slate-600">{u.cargo || "—"}</span> },
    { key: "rol", header: "Rol", render: (u) => <Badge tono="info">{etiquetaRol(u.rol)}</Badge> },
    { key: "estado", header: "Estado", render: (u) => <EstadoBadge estado={u.estado ? "DISPONIBLE" : "INACTIVO"} /> },
  ];

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-in">
      <PageHeader titulo="Usuarios del Panel" subtitulo="Crea cuentas de personal y define su rol (administrador o almacén)." />

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4 animate-fade-up">
        <KpiCard label="Total" value={kpis.total} icon={UserCog} tone="brand" />
        <KpiCard label="Activos" value={kpis.activos} icon={ShieldCheck} tone="success" />
        <KpiCard label="Administradores" value={kpis.admins} icon={ShieldCheck} tone="info" />
      </div>

      <div className="grid gap-6 lg:grid-cols-3 animate-fade-up" style={{ animationDelay: "60ms" }}>
        <SectionCard title="Crear usuario" className="lg:col-span-1">
          <form onSubmit={registrar} noValidate className="space-y-4">
            <Input label="Correo (acceso al panel)" type="email" required value={form.correo}
              onChange={(e) => setForm((f) => ({ ...f, correo: e.target.value }))} placeholder="almacen@siol.com" />
            <PasswordInput label="Contraseña" required value={form.contrasena}
              onChange={(e) => setForm((f) => ({ ...f, contrasena: e.target.value }))}
              placeholder="Escribe la contraseña" autoComplete="new-password"
              hint="8+, con mayúscula, minúscula, número y carácter especial" />
            <Input as="select" label="Rol" value={form.rol} onChange={(e) => setForm((f) => ({ ...f, rol: e.target.value }))}>
              {ROLES.map((r) => <option key={r.valor} value={r.valor}>{r.etiqueta}</option>)}
            </Input>
            {/* Datos personales (opcionales): se muestran luego en "Mi Perfil". */}
            <Input label="Nombre completo (opcional)" value={form.nombre}
              onChange={(e) => setForm((f) => ({ ...f, nombre: e.target.value }))} placeholder="Ej. Ana Pérez" />
            <div className="grid grid-cols-2 gap-3">
              <Input label="DNI (opcional)" value={form.dni}
                onChange={(e) => setForm((f) => ({ ...f, dni: e.target.value }))} placeholder="12345678" />
              <Input label="Teléfono (opcional)" value={form.telefono}
                onChange={(e) => setForm((f) => ({ ...f, telefono: e.target.value }))} placeholder="999 888 777" />
            </div>
            <Input label="Cargo (opcional)" value={form.cargo}
              onChange={(e) => setForm((f) => ({ ...f, cargo: e.target.value }))} placeholder="Ej. Jefe de almacén" />
            <Button type="submit" icon={UserPlus} block disabled={guardando}>{guardando ? "Creando…" : "Crear usuario"}</Button>
            {aviso && (
              <div className={`flex items-center gap-2 rounded-xl px-3.5 py-3 text-sm ${aviso.ok ? "bg-success-soft text-success-strong" : "bg-danger-soft text-danger-strong"}`}>
                {aviso.ok ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
                <span>{aviso.texto}</span>
              </div>
            )}
          </form>
        </SectionCard>

        <div className="lg:col-span-2">
          <DataTable columns={columnas} rows={usuarios} rowKey={(u) => u.id} loading={cargando}
            empty={{ icon: UserCog, title: "Aún no hay usuarios del panel", description: "Crea la primera cuenta de personal." }}
            onRowClick={(u) => setSeleccionado(u)} />
        </div>
      </div>

      <Modal open={!!seleccionado} onClose={() => setSeleccionado(null)} variant="center">
        {seleccionado && (
          <DetalleUsuario usuario={seleccionado} onCerrar={() => setSeleccionado(null)} onCambios={() => { setSeleccionado(null); cargar(); }} />
        )}
      </Modal>
    </div>
  );
}

// Detalle: cambiar rol, activar/desactivar y restablecer contraseña.
function DetalleUsuario({ usuario: u, onCerrar, onCambios }) {
  const [modo, setModo] = useState("ver"); // "ver" | "clave"
  const [rol, setRol] = useState(u.rol);
  // Datos personales editables (opcionales); se inician con lo que ya tiene el usuario.
  const [datos, setDatos] = useState({
    nombre: u.nombre || "",
    dni: u.dni || "",
    telefono: u.telefono || "",
    cargo: u.cargo || "",
  });
  const [nuevaClave, setNuevaClave] = useState("");
  const [claveOk, setClaveOk] = useState(false);
  const [aviso, setAviso] = useState(null);
  const [trabajando, setTrabajando] = useState(false);

  // Guarda rol + datos personales en un solo PATCH (los vacíos se mandan como null).
  const guardarRol = async () => {
    setTrabajando(true); setAviso(null);
    try {
      await actualizarUsuario(u.usuario_id ?? u.id, {
        rol,
        nombre: datos.nombre.trim() || null,
        dni: datos.dni.trim() || null,
        telefono: datos.telefono.trim() || null,
        cargo: datos.cargo.trim() || null,
      });
      onCambios();
    }
    catch (err) { setAviso({ texto: err.message }); setTrabajando(false); }
  };

  const cambiarEstado = async () => {
    setTrabajando(true); setAviso(null);
    try { await actualizarUsuario(u.usuario_id ?? u.id, { estado: !u.estado }); onCambios(); }
    catch (err) { setAviso({ texto: err.message }); setTrabajando(false); }
  };

  const restablecer = async () => {
    setTrabajando(true); setAviso(null);
    try { await restablecerContrasenaUsuario(u.usuario_id ?? u.id, nuevaClave); setClaveOk(true); setNuevaClave(""); }
    catch (err) { setAviso({ texto: err.message }); }
    finally { setTrabajando(false); }
  };

  return (
    <>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <span className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-600 text-white"><UserCog size={22} /></span>
          <div>
            <h2 className="font-bold text-slate-900">{u.correo}</h2>
            <p className="text-sm text-slate-500 nums">{u.codigo} · {etiquetaRol(u.rol)}</p>
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
        <div className="mt-6 space-y-4">
          <div className="flex items-center gap-3 rounded-xl bg-slate-50 px-4 py-3 text-sm">
            <Mail size={18} className="text-slate-400" />
            <div><p className="text-xs text-slate-400">Correo</p><p className="font-medium text-slate-700">{u.correo}</p></div>
          </div>
          <Input as="select" label="Rol" value={rol} onChange={(e) => setRol(e.target.value)}>
            {ROLES.map((r) => <option key={r.valor} value={r.valor}>{r.etiqueta}</option>)}
          </Input>
          {/* Datos personales editables (opcionales) */}
          <Input label="Nombre completo" value={datos.nombre}
            onChange={(e) => setDatos((d) => ({ ...d, nombre: e.target.value }))} placeholder="Ej. Ana Pérez" />
          <div className="grid grid-cols-2 gap-3">
            <Input label="DNI" value={datos.dni}
              onChange={(e) => setDatos((d) => ({ ...d, dni: e.target.value }))} placeholder="12345678" />
            <Input label="Teléfono" value={datos.telefono}
              onChange={(e) => setDatos((d) => ({ ...d, telefono: e.target.value }))} placeholder="999 888 777" />
          </div>
          <Input label="Cargo" value={datos.cargo}
            onChange={(e) => setDatos((d) => ({ ...d, cargo: e.target.value }))} placeholder="Ej. Jefe de almacén" />
          <div className="flex gap-2">
            <Button variant="secondary" block onClick={cambiarEstado} disabled={trabajando}>{u.estado ? "Desactivar" : "Activar"}</Button>
            <Button icon={Check} block onClick={guardarRol} disabled={trabajando}>{trabajando ? "Guardando…" : "Guardar cambios"}</Button>
          </div>
          <Button variant="secondary" icon={KeyRound} block onClick={() => { setAviso(null); setClaveOk(false); setNuevaClave(""); setModo("clave"); }}>
            Restablecer contraseña
          </Button>
        </div>
      )}

      {modo === "clave" && (
        <div className="mt-6 space-y-4">
          {claveOk ? (
            <>
              <div className="flex items-start gap-3 rounded-xl bg-success-soft px-4 py-3 text-sm text-success-strong">
                <CheckCircle2 size={20} className="shrink-0" />
                <span>Contraseña restablecida. Comunícasela a la persona.</span>
              </div>
              <Button block onClick={() => setModo("ver")}>Listo</Button>
            </>
          ) : (
            <>
              <PasswordInput label="Nueva contraseña" value={nuevaClave} onChange={(e) => setNuevaClave(e.target.value)}
                placeholder="Escribe la nueva contraseña" autoComplete="new-password"
                hint="8+, con mayúscula, minúscula, número y carácter especial" />
              <div className="flex gap-2">
                <Button variant="secondary" block onClick={() => setModo("ver")} disabled={trabajando}>Cancelar</Button>
                <Button icon={KeyRound} block onClick={restablecer} disabled={trabajando}>{trabajando ? "Guardando…" : "Restablecer"}</Button>
              </div>
            </>
          )}
        </div>
      )}
    </>
  );
}
