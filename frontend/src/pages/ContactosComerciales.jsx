import { useEffect, useMemo, useState } from "react";
import { Handshake, Search, Download, Mail, Phone } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import KpiCard from "../components/ui/KpiCard";
import SectionCard from "../components/ui/SectionCard";
import DataTable from "../components/ui/DataTable";
import Input from "../components/ui/Input";
import Button from "../components/ui/Button";
import { listarContactos, descargarContactos } from "../services/api";

// Fecha legible corta (es-PE). Entrada: fecha ISO. Salida: "dd/mm/aa hh:mm" o "—".
const fmt = (f) => (f ? new Date(f).toLocaleString("es-PE", { dateStyle: "short", timeStyle: "short" }) : "—");

// Contactos comerciales que llegan desde el formulario del landing, con exportación a Excel (C39-01).
export default function ContactosComerciales() {
  const [contactos, setContactos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [busqueda, setBusqueda] = useState("");
  const [descargando, setDescargando] = useState(false);
  const [error, setError] = useState("");
  const [ultimos7, setUltimos7] = useState(0);

  useEffect(() => {
    let activo = true;
    listarContactos()
      .then((d) => {
        if (!activo) return;
        const lista = Array.isArray(d) ? d : [];
        const desde = Date.now() - 7 * 864e5;
        setContactos(lista);
        setUltimos7(lista.filter((c) => c.creado_en && new Date(c.creado_en).getTime() >= desde).length);
      })
      .catch((e) => activo && setError(e.message))
      .finally(() => activo && setCargando(false));
    return () => { activo = false; };
  }, []);

  const filtrados = useMemo(() => {
    const q = busqueda.trim().toLowerCase();
    if (!q) return contactos;
    return contactos.filter((c) => [c.nombre, c.empresa, c.email, c.telefono].some((v) => (v || "").toLowerCase().includes(q)));
  }, [contactos, busqueda]);

  // Descarga todos los contactos en Excel. Sin parámetros.
  const exportar = () => {
    setDescargando(true);
    setError("");
    descargarContactos().catch((e) => setError(e.message)).finally(() => setDescargando(false));
  };

  const columnas = [
    { key: "creado_en", header: "Fecha", render: (c) => <span className="text-xs text-slate-500 nums">{fmt(c.creado_en)}</span> },
    { key: "nombre", header: "Contacto", render: (c) => (
      <div>
        <p className="font-medium text-slate-800">{c.nombre}</p>
        <p className="text-xs text-slate-500">{c.empresa || "Sin empresa"}</p>
      </div>
    ) },
    { key: "email", header: "Datos", render: (c) => (
      <div className="space-y-0.5 text-xs">
        <a href={`mailto:${c.email}`} className="flex items-center gap-1 text-brand-600 hover:underline"><Mail size={12} /> {c.email}</a>
        {c.telefono && <a href={`tel:${c.telefono}`} className="flex items-center gap-1 text-slate-600 hover:underline"><Phone size={12} /> {c.telefono}</a>}
      </div>
    ) },
    { key: "volumen", header: "Pedidos/día", render: (c) => <span className="text-slate-700 nums">{c.volumen ?? "—"}</span> },
    { key: "mensaje", header: "Mensaje", render: (c) => <span className="text-xs text-slate-600 line-clamp-3">{c.mensaje || "—"}</span> },
  ];

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-in">
      <PageHeader
        titulo="Contactos comerciales"
        subtitulo="Empresas que pidieron una propuesta desde el sitio público."
      >
        <Button icon={Download} variant="secondary" className="shrink-0 whitespace-nowrap" onClick={exportar} disabled={descargando || !contactos.length}>
          {descargando ? "Descargando…" : "Exportar a Excel"}
        </Button>
      </PageHeader>

      <div className="grid grid-cols-2 gap-4 animate-fade-up">
        <KpiCard label="Total" value={contactos.length} icon={Handshake} tone="brand" />
        <KpiCard label="Últimos 7 días" value={ultimos7} icon={Handshake} tone="success" />
      </div>

      {error && <p className="rounded-xl bg-danger-soft px-4 py-2.5 text-sm text-danger-strong">{error}</p>}

      <SectionCard className="animate-fade-up" title="Contactos" subtitle={`${filtrados.length} de ${contactos.length}`}
        action={
          <div className="relative">
            <Search size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <Input value={busqueda} onChange={(e) => setBusqueda(e.target.value)} placeholder="Nombre, empresa o correo" className="pl-9" />
          </div>
        }
      >
        <DataTable columns={columnas} rows={filtrados} rowKey={(c) => c.id} loading={cargando}
          empty={{ icon: Handshake, title: "Sin contactos", description: "Aún no llegan contactos desde el sitio público." }} />
      </SectionCard>
    </div>
  );
}
