// Pestaña "Base de conocimiento": lo que el asistente sabe de SAVA, editable sin programar.
// Cada cambio crea una versión nueva (quién y cuándo) y el asistente lo usa al instante.
import { useEffect, useMemo, useState } from "react";
import { BookOpen, History, Plus, Search, FlaskConical } from "lucide-react";
import SectionCard from "../../../components/ui/SectionCard";
import DataTable from "../../../components/ui/DataTable";
import Input from "../../../components/ui/Input";
import Button from "../../../components/ui/Button";
import Badge from "../../../components/ui/Badge";
import Modal from "../../../components/ui/Modal";
import {
  cambiarEstadoArticulo, crearArticulo, editarArticulo, historialArticulo, listarArticulos, probarBusqueda,
} from "./servicioAdminAtencion";

const VACIO = { clave: "", idioma: "es", categoria: "", titulo: "", contenido: "", etiquetas: "" };
// Fecha legible corta. Recibe una fecha ISO.
const fmt = (f) => (f ? new Date(`${f}Z`).toLocaleString("es-PE", { dateStyle: "short", timeStyle: "short" }) : "—");

// Panel lateral para crear o editar un artículo, con su historial. Recibe el artículo (o null) y callbacks.
function EditorArticulo({ articulo, onCerrar, onGuardado }) {
  const nuevo = !articulo?.id;
  const [datos, setDatos] = useState(() => ({ ...VACIO, ...(articulo || {}) }));
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState("");
  const [historial, setHistorial] = useState(null);

  // Actualiza un campo del formulario. Recibe el nombre del campo.
  const campo = (nombre) => (e) => setDatos((d) => ({ ...d, [nombre]: e.target.value }));

  // Guarda el artículo (nuevo o nueva versión). Recibe el evento del formulario.
  const guardar = async (e) => {
    e.preventDefault();
    setGuardando(true);
    setError("");
    const { categoria, titulo, contenido, etiquetas } = datos;
    try {
      const r = nuevo ? await crearArticulo(datos) : await editarArticulo(articulo.id, { categoria, titulo, contenido, etiquetas });
      onGuardado(r);
    } catch (err) {
      setError(err.message);
    } finally {
      setGuardando(false);
    }
  };

  return (
    <form onSubmit={guardar} className="flex h-full flex-col">
      <div className="border-b border-slate-200 px-6 py-4">
        <h2 className="text-lg font-semibold text-slate-900">{nuevo ? "Nuevo artículo" : "Editar artículo"}</h2>
        {!nuevo && <p className="text-xs text-slate-500">{articulo.clave} · {articulo.idioma.toUpperCase()} · versión {articulo.version}</p>}
      </div>
      <div className="flex-1 space-y-4 overflow-y-auto px-6 py-4">
        {nuevo && (
          <div className="grid grid-cols-2 gap-3">
            <Input label="Clave" value={datos.clave} onChange={campo("clave")} placeholder="cobertura-chosica" required
                   hint="Minúsculas y guiones. Español e inglés comparten la clave." />
            <Input as="select" label="Idioma" value={datos.idioma} onChange={campo("idioma")}>
              <option value="es">Español</option>
              <option value="en">Inglés</option>
            </Input>
          </div>
        )}
        <Input label="Categoría" value={datos.categoria} onChange={campo("categoria")} placeholder="cobertura" required />
        <Input label="Pregunta o título" value={datos.titulo} onChange={campo("titulo")} maxLength={200} required />
        <Input as="textarea" label="Respuesta" value={datos.contenido} onChange={campo("contenido")} rows={7} maxLength={3000} required
               hint="Escríbela como información para el cliente. No se aceptan instrucciones para el asistente ni enlaces fuera de SAVA." />
        <Input label="Palabras clave (opcional)" value={datos.etiquetas} onChange={campo("etiquetas")} maxLength={400}
               hint="Sinónimos y formas de preguntar que ayudan a encontrar el artículo." />
        {error && <p role="alert" className="rounded-xl border border-danger/30 bg-danger-soft px-3 py-2 text-sm text-danger-strong">{error}</p>}

        {!nuevo && (
          <div className="border-t border-slate-100 pt-4">
            {historial === null ? (
              <Button type="button" variant="ghost" size="sm" icon={History}
                      onClick={() => historialArticulo(articulo.id).then(setHistorial).catch((e) => setError(e.message))}>
                Ver historial de versiones
              </Button>
            ) : (
              <ol className="space-y-2">
                {historial.map((v) => (
                  <li key={v.version} className="rounded-xl bg-warm-50 px-3 py-2 text-xs text-slate-600">
                    <span className="font-semibold text-slate-800">v{v.version} · {v.accion}</span> · {v.editado_por} · {fmt(v.editado_en)}
                    <p className="mt-1 line-clamp-2 text-slate-500">{v.contenido}</p>
                  </li>
                ))}
              </ol>
            )}
          </div>
        )}
      </div>
      <div className="flex justify-end gap-2 border-t border-slate-200 px-6 py-4">
        <Button type="button" variant="secondary" onClick={onCerrar}>Cancelar</Button>
        <Button type="submit" disabled={guardando}>{guardando ? "Guardando…" : nuevo ? "Crear artículo" : "Guardar nueva versión"}</Button>
      </div>
    </form>
  );
}

// Prueba qué artículos usaría el asistente para una pregunta (sin gastar IA). Sin props.
function ProbarBusqueda() {
  const [consulta, setConsulta] = useState("");
  const [idioma, setIdioma] = useState("es");
  const [resultados, setResultados] = useState(null);
  const [error, setError] = useState("");

  // Ejecuta la prueba. Recibe el evento del formulario.
  const probar = (e) => {
    e.preventDefault();
    if (consulta.trim().length < 2) return;
    setError("");
    probarBusqueda(consulta.trim(), idioma).then(setResultados).catch((err) => setError(err.message));
  };

  return (
    <SectionCard title="Probar una pregunta" subtitle="Muestra qué artículos recibiría el asistente, sin llamar a la IA.">
      <form onSubmit={probar} className="flex flex-col gap-2 sm:flex-row">
        <div className="flex-1"><Input value={consulta} onChange={(e) => setConsulta(e.target.value)} placeholder="¿Llegan a Ventanilla los sábados?" aria-label="Pregunta de prueba" /></div>
        <Input as="select" value={idioma} onChange={(e) => setIdioma(e.target.value)} aria-label="Idioma de la prueba">
          <option value="es">Español</option>
          <option value="en">Inglés</option>
        </Input>
        <Button type="submit" variant="secondary" icon={FlaskConical}>Probar</Button>
      </form>
      {error && <p role="alert" className="mt-2 text-sm text-danger-strong">{error}</p>}
      {resultados && (
        <ul className="mt-3 space-y-1.5 text-sm">
          {resultados.length === 0 && <li className="text-slate-500">Ningún artículo responde esa pregunta: el asistente diría que no lo sabe y ofrecería el contacto.</li>}
          {resultados.map((r) => (
            <li key={`${r.clave}-${r.idioma}`} className="flex items-center justify-between gap-3 rounded-xl bg-warm-50 px-3 py-2">
              <span><span className="font-medium text-slate-800">{r.titulo}</span> <span className="text-xs text-slate-500">({r.clave} · {r.idioma})</span></span>
              <Badge tono={r.se_usaria ? "success" : "neutral"}>{r.se_usaria ? `Se usa · ${r.puntaje}` : `Débil · ${r.puntaje}`}</Badge>
            </li>
          ))}
        </ul>
      )}
    </SectionCard>
  );
}

// Pestaña de la base de conocimiento. Sin props.
export default function TabConocimiento() {
  const [articulos, setArticulos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [idioma, setIdioma] = useState("es");
  const [busqueda, setBusqueda] = useState("");
  const [editando, setEditando] = useState(null); // null | {} (nuevo) | artículo
  const [recarga, setRecarga] = useState(0);

  // Trae los artículos del idioma elegido (y cada vez que se pide recargar).
  useEffect(() => {
    let vivo = true;
    listarArticulos(idioma)
      .then((d) => { if (vivo) { setArticulos(d); setError(""); } })
      .catch((e) => vivo && setError(e.message))
      .finally(() => vivo && setCargando(false));
    return () => { vivo = false; };
  }, [idioma, recarga]);

  // Vuelve a pedir los artículos (tras crear, editar o activar). Sin parámetros.
  const cargar = () => setRecarga((n) => n + 1);
  // Cambia el idioma y muestra la carga. Recibe el idioma.
  const cambiarIdioma = (valor) => { setCargando(true); setIdioma(valor); };

  const filtrados = useMemo(() => {
    const q = busqueda.trim().toLowerCase();
    return q ? articulos.filter((a) => [a.titulo, a.contenido, a.clave, a.categoria].some((v) => v.toLowerCase().includes(q))) : articulos;
  }, [articulos, busqueda]);

  // Activa o desactiva un artículo. Recibe el artículo.
  const alternar = (a) => cambiarEstadoArticulo(a.id, !a.activo).then(cargar).catch((e) => setError(e.message));

  const columnas = [
    { key: "titulo", header: "Pregunta", render: (a) => (
      <div>
        <p className="font-medium text-slate-800">{a.titulo}</p>
        <p className="line-clamp-1 text-xs text-slate-500">{a.contenido}</p>
      </div>
    ) },
    { key: "categoria", header: "Categoría", render: (a) => <span className="text-slate-600">{a.categoria}</span> },
    { key: "version", header: "Versión", render: (a) => <span className="text-xs text-slate-500 nums">v{a.version} · {fmt(a.editado_en)}</span> },
    { key: "activo", header: "Estado", render: (a) => (
      <button type="button" onClick={(e) => { e.stopPropagation(); alternar(a); }} title={a.activo ? "Desactivar" : "Activar"}>
        <Badge tono={a.activo ? "success" : "neutral"}>{a.activo ? "Activo" : "Inactivo"}</Badge>
      </button>
    ) },
  ];

  return (
    <div className="space-y-5">
      <ProbarBusqueda />
      <SectionCard title="Artículos" subtitle={`${filtrados.length} de ${articulos.length} en ${idioma === "es" ? "español" : "inglés"}`}
        action={
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <Input as="select" value={idioma} onChange={(e) => cambiarIdioma(e.target.value)} aria-label="Idioma">
              <option value="es">Español</option>
              <option value="en">Inglés</option>
            </Input>
            <div className="relative">
              <Search size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <Input className="pl-9" value={busqueda} onChange={(e) => setBusqueda(e.target.value)} placeholder="Buscar" aria-label="Buscar artículos" />
            </div>
            <Button icon={Plus} onClick={() => setEditando({ idioma })}>Nuevo artículo</Button>
          </div>
        }>
        {error && <p role="alert" className="mb-3 rounded-xl border border-danger/30 bg-danger-soft px-3 py-2 text-sm text-danger-strong">{error}</p>}
        <DataTable columns={columnas} rows={filtrados} rowKey={(a) => a.id} loading={cargando} onRowClick={(a) => setEditando(a)}
                   empty={{ icon: BookOpen, title: "Sin artículos", description: "No hay artículos que coincidan con la búsqueda." }} />
      </SectionCard>

      <Modal open={!!editando} onClose={() => setEditando(null)} variant="right">
        {editando && (
          <EditorArticulo key={editando.id || "nuevo"} articulo={editando.id ? editando : { ...VACIO, ...editando }}
                          onCerrar={() => setEditando(null)} onGuardado={() => { setEditando(null); cargar(); }} />
        )}
      </Modal>
    </div>
  );
}
