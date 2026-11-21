import { useEffect, useState } from "react";
import {
  AlertTriangle, BellRing, CalendarRange, ClipboardList, FileText, Fuel,
  Gauge, Pencil, Plus, Settings, ShieldCheck, Trash2, Truck, Wrench,
} from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import KpiCard from "../components/ui/KpiCard";
import DataTable from "../components/ui/DataTable";
import SectionCard from "../components/ui/SectionCard";
import Input from "../components/ui/Input";
import Button from "../components/ui/Button";
import Modal from "../components/ui/Modal";
import Badge from "../components/ui/Badge";
import { useAuth } from "../hooks/useAuth";
import {
  actualizarCargaCombustible, actualizarConfiguracionMantenimiento,
  actualizarDocumentoMantenimiento, actualizarPreventivoMantenimiento,
  crearCargaCombustible, crearDocumentoMantenimiento, crearMantenimientoFlota,
  crearPreventivoMantenimiento, eliminarCargaCombustible,
  eliminarDocumentoMantenimiento, eliminarPreventivoMantenimiento,
  listarAlertasMantenimiento, listarAuditoriaMantenimiento,
  listarCargasCombustible, listarDocumentosMantenimiento,
  listarFlotaMantenimiento, listarLicenciasMantenimiento,
  listarMantenimientosFlota, listarPreventivosMantenimiento,
  listarRankingAverias, obtenerConfiguracionMantenimiento,
  obtenerCostosFlotaMantenimiento, obtenerFichaVehiculoMantenimiento,
  obtenerResumenMantenimiento,
} from "../services/api";

// Pestañas del modulo. Cada entrada lleva su icono de lucide.
const PESTANAS = [
  ["resumen", "Resumen", Gauge],
  ["documentos", "Documentos", FileText],
  ["mantenimientos", "Mantenimientos", Wrench],
  ["preventivos", "Preventivos", CalendarRange],
  ["combustible", "Combustible", Fuel],
  ["alertas", "Alertas", BellRing],
  ["flota", "Flota", Truck],
  ["licencias", "Licencias", ShieldCheck],
  ["configuracion", "Configuración", Settings],
];

const OPCIONES = {
  tipoDocumento: ["SOAT", "REVISION_TECNICA", "TARJETA_CIRCULACION", "SEGURO", "PERMISO_OPERACION"],
  tipoMantenimiento: ["PREVENTIVO", "CORRECTIVO"],
  categoria: ["ACEITE", "LLANTAS", "FRENOS", "REVISION_GENERAL", "OTRO"],
  prioridad: ["BAJA", "MEDIA", "ALTA"],
  estadoMantenimiento: ["PROGRAMADO", "EN_PROCESO", "COMPLETADO", "CANCELADO"],
  tipoCombustible: ["DIESEL", "GASOLINA_95", "GASOLINA_90", "GLP"],
};

// Campos de los formularios de alta. El tipo "numero" se convierte al enviar.
const FORMULARIOS = {
  documentos: [
    { clave: "placa", etiqueta: "Placa", requerido: true, placeholder: "ABC-789" },
    { clave: "tipo_documento", etiqueta: "Tipo", tipo: "select", opciones: OPCIONES.tipoDocumento, requerido: true },
    { clave: "numero", etiqueta: "Número", requerido: true },
    { clave: "entidad_emisora", etiqueta: "Entidad emisora" },
    { clave: "fecha_emision", etiqueta: "Fecha de emisión", tipo: "date", requerido: true },
    { clave: "fecha_vencimiento", etiqueta: "Fecha de vencimiento", tipo: "date", requerido: true },
    { clave: "observaciones", etiqueta: "Observaciones" },
  ],
  mantenimientos: [
    { clave: "placa", etiqueta: "Placa", requerido: true, placeholder: "ABC-789" },
    { clave: "tipo", etiqueta: "Tipo", tipo: "select", opciones: OPCIONES.tipoMantenimiento, requerido: true },
    { clave: "categoria", etiqueta: "Categoría", tipo: "select", opciones: OPCIONES.categoria, requerido: true },
    { clave: "descripcion", etiqueta: "Descripción", requerido: true },
    { clave: "prioridad", etiqueta: "Prioridad", tipo: "select", opciones: OPCIONES.prioridad, requerido: true },
    { clave: "fecha_programada", etiqueta: "Fecha programada", tipo: "date" },
    { clave: "kilometraje", etiqueta: "Kilometraje", tipo: "numero" },
    { clave: "costo", etiqueta: "Costo (S/)", tipo: "numero" },
    { clave: "taller", etiqueta: "Taller" },
  ],
  preventivos: [
    { clave: "placa", etiqueta: "Placa", requerido: true, placeholder: "ABC-789" },
    { clave: "categoria", etiqueta: "Categoría", tipo: "select", opciones: OPCIONES.categoria, requerido: true },
    { clave: "descripcion", etiqueta: "Descripción", requerido: true },
    { clave: "intervalo_km", etiqueta: "Intervalo en km", tipo: "numero", requerido: true },
    { clave: "intervalo_dias", etiqueta: "Intervalo en días", tipo: "numero" },
    { clave: "km_base", etiqueta: "Kilometraje base", tipo: "numero" },
    { clave: "fecha_base", etiqueta: "Fecha base", tipo: "date" },
  ],
  combustible: [
    { clave: "placa", etiqueta: "Placa", requerido: true, placeholder: "ABC-789" },
    { clave: "fecha", etiqueta: "Fecha", tipo: "date", requerido: true },
    { clave: "tipo_combustible", etiqueta: "Tipo", tipo: "select", opciones: OPCIONES.tipoCombustible, requerido: true },
    { clave: "galones", etiqueta: "Galones", tipo: "numero", requerido: true },
    { clave: "monto", etiqueta: "Monto (S/)", tipo: "numero", requerido: true },
    { clave: "odometro", etiqueta: "Odómetro", tipo: "numero" },
    { clave: "proveedor", etiqueta: "Proveedor" },
  ],
};

// Valores iniciales de un formulario. Recibe la lista de campos.
const valoresIniciales = (campos) =>
  Object.fromEntries(campos.map((campo) => [campo.clave, campo.tipo === "date" ? new Date().toISOString().slice(0, 10) : ""]));

// Convierte los valores de texto a numeros donde corresponde. Recibe campos y valores.
const normalizar = (campos, valores) => {
  const resultado = { ...valores };
  for (const campo of campos) {
    if (campo.tipo === "numero" && resultado[campo.clave] !== "") {
      resultado[campo.clave] = Number(resultado[campo.clave]);
    }
    if (resultado[campo.clave] === "") delete resultado[campo.clave];
  }
  return resultado;
};

// Etiqueta de color para estados calculados. Recibe el estado.
function Estado({ valor }) {
  const texto = String(valor || "—").replaceAll("_", " ");
  const tono = ["VENCIDO", "ALTA", "NO_APTO"].includes(valor) ? "danger"
    : ["POR_VENCER", "MEDIA", "EN_PROCESO"].includes(valor) ? "warning"
      : ["VIGENTE", "BAJA", "AL_DIA", "COMPLETADO"].includes(valor) ? "success" : "neutral";
  return <Badge tono={tono}>{texto}</Badge>;
}

// Formulario generico de alta/edicion. Recibe campos, valores, onChange y onSubmit.
function Formulario({ campos, valores, onChange, onSubmit, etiquetaBoton = "Guardar" }) {
  return (
    <form
      className="space-y-4"
      onSubmit={(evento) => { evento.preventDefault(); onSubmit(normalizar(campos, valores)); }}
    >
      {campos.map((campo) => (
        <Input
          key={campo.clave}
          label={campo.etiqueta}
          as={campo.tipo === "select" ? "select" : "input"}
          type={campo.tipo === "numero" ? "number" : campo.tipo === "date" ? "date" : "text"}
          placeholder={campo.placeholder}
          required={campo.requerido}
          value={valores[campo.clave] ?? ""}
          onChange={(evento) => onChange({ ...valores, [campo.clave]: evento.target.value })}
        >
          {campo.opciones?.map((opcion) => (
            <option key={opcion} value={opcion}>{opcion.replaceAll("_", " ")}</option>
          ))}
        </Input>
      ))}
      <div className="flex justify-end gap-2 pt-2">
        <Button type="submit">{etiquetaBoton}</Button>
      </div>
    </form>
  );
}

export default function ModuloMantenimientoPage() {
  const { rol } = useAuth();
  const esAdmin = rol === "admin";
  const [pestana, setPestana] = useState("resumen");
  const [cargando, setCargando] = useState(true);
  const [aviso, setAviso] = useState(null);
  const [datos, setDatos] = useState({
    resumen: null, flota: [], documentos: [], mantenimientos: [], preventivos: [],
    cargas: [], alertas: [], licencias: [], costos: null, averias: [],
    configuracion: null, auditoria: [], ficha: null,
  });
  const [filtros, setFiltros] = useState({ placa: "", estado: "" });
  const [modal, setModal] = useState(null);
  const [valores, setValores] = useState({});
  const [editando, setEditando] = useState(null);

  const notificar = (ok, texto) => setAviso({ ok, texto });
  const manejarError = (error) => notificar(false, error?.message || "No se pudo completar la operación.");

  // Carga todas las consultas del modulo. Una caida parcial no bloquea la pantalla.
  async function recargar() {
    setCargando(true);
    const tareas = [
      ["resumen", obtenerResumenMantenimiento],
      ["flota", listarFlotaMantenimiento],
      ["documentos", () => listarDocumentosMantenimiento({ limite: 200 })],
      ["mantenimientos", () => listarMantenimientosFlota({ limite: 200 })],
      ["preventivos", () => listarPreventivosMantenimiento({ limite: 200 })],
      ["cargas", () => listarCargasCombustible({ limite: 200 })],
      ["alertas", listarAlertasMantenimiento],
      ["costos", obtenerCostosFlotaMantenimiento],
      ["averias", listarRankingAverias],
      ["configuracion", obtenerConfiguracionMantenimiento],
    ];
    if (esAdmin) {
      tareas.push(["licencias", listarLicenciasMantenimiento]);
      tareas.push(["auditoria", () => listarAuditoriaMantenimiento(50)]);
    }
    const resultados = await Promise.allSettled(tareas.map(([, fn]) => fn()));
    const siguiente = {};
    resultados.forEach((resultado, indice) => {
      const clave = tareas[indice][0];
      siguiente[clave] = resultado.status === "fulfilled" ? resultado.value : null;
    });
    if (resultados.every((resultado) => resultado.status === "rejected" && resultado.reason?.status === 404)) {
      notificar(false, "El módulo de mantenimiento está apagado en el servidor (MODULO_MANTENIMIENTO_ENABLED).");
    }
    setDatos((anterior) => ({ ...anterior, ...siguiente }));
    setCargando(false);
  }

  useEffect(() => { recargar(); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, [esAdmin]);

  // Abre el modal de alta con valores iniciales.
  const abrirAlta = (nombre) => {
    setEditando(null);
    setValores(valoresIniciales(FORMULARIOS[nombre]));
    setModal(nombre);
  };

  // Abre el modal de edicion con los valores de la fila.
  const abrirEdicion = (nombre, fila) => {
    setEditando(fila);
    setValores(Object.fromEntries(FORMULARIOS[nombre].map((campo) => [campo.clave, fila[campo.clave] ?? ""])));
    setModal(nombre);
  };

  // Guarda un formulario segun el modulo y cierra el modal.
  const guardar = async (nombre, valoresNormalizados) => {
    try {
      if (nombre === "documentos") {
        if (editando) await actualizarDocumentoMantenimiento(editando.id, valoresNormalizados);
        else await crearDocumentoMantenimiento(valoresNormalizados);
      } else if (nombre === "mantenimientos") {
        await crearMantenimientoFlota(valoresNormalizados);
      } else if (nombre === "preventivos") {
        if (editando) await actualizarPreventivoMantenimiento(editando.id, valoresNormalizados);
        else await crearPreventivoMantenimiento(valoresNormalizados);
      } else if (nombre === "combustible") {
        if (editando) await actualizarCargaCombustible(editando.id, valoresNormalizados);
        else await crearCargaCombustible(valoresNormalizados);
      }
      notificar(true, "Cambio guardado correctamente.");
      setModal(null);
      await recargar();
    } catch (error) { manejarError(error); }
  };

  // Da de baja una fila previa confirmacion del navegador.
  const borrar = async (nombre, id) => {
    if (!window.confirm("¿Deseas dar de baja este registro?")) return;
    try {
      const acciones = {
        documentos: eliminarDocumentoMantenimiento,
        preventivos: eliminarPreventivoMantenimiento,
        combustible: eliminarCargaCombustible,
      };
      await acciones[nombre](id);
      notificar(true, "Registro dado de baja.");
      await recargar();
    } catch (error) { manejarError(error); }
  };

  // Abre la ficha completa de una placa. Recibe la fila de flota.
  const verFicha = async (fila) => {
    try {
      setDatos((anterior) => ({ ...anterior, ficha: null }));
      const ficha = await obtenerFichaVehiculoMantenimiento(fila.placa);
      setDatos((anterior) => ({ ...anterior, ficha }));
      setModal("ficha");
    } catch (error) { manejarError(error); }
  };

  const porPlaca = (lista) => (lista || []).filter((fila) => !filtros.placa || fila.placa === filtros.placa);
  const porEstado = (lista) => porPlaca(lista).filter((fila) => !filtros.estado || fila.estado === filtros.estado);
  const resumen = datos.resumen || {};
  const costos = datos.costos || {};

  const filtroControles = (
    <div className="flex flex-wrap gap-3">
      <Input
        label="Filtrar por placa"
        placeholder="Todas"
        value={filtros.placa}
        onChange={(evento) => setFiltros({ ...filtros, placa: evento.target.value.toUpperCase() })}
      />
      <Input
        label="Filtrar por estado"
        as="select"
        value={filtros.estado}
        onChange={(evento) => setFiltros({ ...filtros, estado: evento.target.value })}
      >
        <option value="">Todos</option>
        {["VIGENTE", "POR_VENCER", "VENCIDO", "AL_DIA", "PROGRAMADO", "COMPLETADO"].map((estado) => (
          <option key={estado} value={estado}>{estado.replaceAll("_", " ")}</option>
        ))}
      </Input>
    </div>
  );

  return (
    <div className="space-y-6 p-6 lg:p-8">
      <PageHeader
        titulo="Mantenimiento de la flota"
        subtitulo="Documentos, mantenimientos preventivos, averías, combustible y costos por unidad"
      >
        <Button variant="secondary" icon={ClipboardList} onClick={recargar}>Actualizar</Button>
        {esAdmin && <Button icon={Plus} onClick={() => abrirAlta("documentos")}>Nuevo documento</Button>}
      </PageHeader>

      {aviso && (
        <div role="status" className={`rounded-xl border px-4 py-3 text-sm ${aviso.ok
          ? "border-success/30 bg-success-soft text-success-strong"
          : "border-danger/30 bg-danger-soft text-danger-strong"}`}>
          {aviso.texto}
        </div>
      )}

      <nav className="flex flex-wrap gap-2" aria-label="Secciones del módulo">
        {PESTANAS.filter(([id]) => id !== "licencias" || esAdmin).map(([id, nombre, Icono]) => (
          <button
            key={id}
            type="button"
            onClick={() => setPestana(id)}
            aria-current={pestana === id ? "page" : undefined}
            className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium ${pestana === id
              ? "bg-brand-600 text-white" : "border border-slate-200 bg-white text-slate-700"}`}
          >
            <Icono size={16} />{nombre}
          </button>
        ))}
      </nav>

      {pestana === "resumen" && (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <KpiCard label="Vehículos" value={resumen.total_vehiculos ?? 0} icon={Truck} tone="brand" />
            <KpiCard label="Documentos vigentes" value={resumen.documentos_vigentes ?? 0} icon={FileText} tone="success" />
            <KpiCard label="Documentos vencidos" value={resumen.documentos_vencidos ?? 0} icon={AlertTriangle} tone="danger" />
            <KpiCard label="Alertas activas" value={resumen.alertas_total ?? 0} icon={BellRing} tone="warning" />
            <KpiCard label="Costo del mes (S/)" value={Number(resumen.costo_mes ?? 0).toLocaleString("es-PE")} icon={Fuel} tone="info" />
            <KpiCard label="Rendimiento (km/gal)" value={Number(costos.rendimiento_km_gal ?? 0).toFixed(2)} icon={Gauge} tone="brand" />
            <KpiCard label="Preventivos vencidos" value={Number(costos.preventivos_vencidos ?? (datos.preventivos || []).filter((p) => p.estado === "VENCIDO").length)} icon={CalendarRange} tone="danger" />
            <KpiCard label="Con más averías" value={datos.averias?.[0]?.total ?? 0} icon={Wrench} tone="warning" />
          </div>
          <div className="grid gap-6 lg:grid-cols-2">
            <SectionCard title="Costos de la flota" subtitle="Mantenimiento + combustible">
              <dl className="grid grid-cols-2 gap-4 text-sm">
                <div><dt className="text-slate-500">Costo total</dt><dd className="font-semibold nums">S/ {Number(costos.costo_total ?? 0).toFixed(2)}</dd></div>
                <div><dt className="text-slate-500">Costo por km</dt><dd className="font-semibold nums">S/ {costos.costo_por_kilometro ?? "—"}</dd></div>
                <div><dt className="text-slate-500">Galones</dt><dd className="font-semibold nums">{Number(costos.galones_totales ?? 0).toFixed(2)}</dd></div>
                <div><dt className="text-slate-500">Cargas registradas</dt><dd className="font-semibold nums">{costos.cargas_totales ?? 0}</dd></div>
              </dl>
            </SectionCard>
            <SectionCard title="Unidades con más averías" subtitle="Sugerencia de revisión preventiva">
              <DataTable
                rows={datos.averias || []}
                rowKey={(fila) => fila.placa}
                columns={[
                  { key: "placa", header: "Placa" },
                  { key: "total", header: "Incidencias" },
                  { key: "sugerencia", header: "Sugerencia", render: (fila) => <Estado valor={fila.sugerencia} /> },
                ]}
                empty={{ icon: Wrench, title: "Sin averías registradas", description: "No hay incidencias vinculadas a la flota." }}
                loading={cargando}
              />
            </SectionCard>
          </div>
        </div>
      )}

      {pestana === "documentos" && (
        <SectionCard
          title="Documentos de la flota"
          subtitle="El historial se conserva; los contadores usan la renovación más reciente"
          action={esAdmin && <Button size="sm" icon={Plus} onClick={() => abrirAlta("documentos")}>Nuevo</Button>}
        >
          {filtroControles}
          <div className="mt-4">
            <DataTable
              rows={porEstado(datos.documentos)}
              rowKey={(fila) => fila.id}
              loading={cargando}
              columns={[
                { key: "placa", header: "Placa" },
                { key: "tipo_documento", header: "Tipo", render: (fila) => fila.tipo_documento.replaceAll("_", " ") },
                { key: "numero", header: "Número" },
                { key: "fecha_vencimiento", header: "Vencimiento" },
                { key: "dias_para_vencer", header: "Días", className: "nums" },
                { key: "estado", header: "Estado", render: (fila) => <Estado valor={fila.estado} /> },
                ...(esAdmin ? [{ key: "acciones", header: "Acciones", render: (fila) => (
                  <div className="flex gap-2">
                    <button type="button" aria-label="Editar" onClick={() => abrirEdicion("documentos", fila)}><Pencil size={16} /></button>
                    <button type="button" aria-label="Eliminar" onClick={() => borrar("documentos", fila.id)}><Trash2 size={16} /></button>
                  </div>
                ) }] : []),
              ]}
              empty={{ icon: FileText, title: "Sin documentos", description: "Registra el primer documento de la flota." }}
            />
          </div>
        </SectionCard>
      )}

      {pestana === "mantenimientos" && (
        <SectionCard
          title="Mantenimientos"
          subtitle="Órdenes programadas, en proceso y completadas"
          action={esAdmin && <Button size="sm" icon={Plus} onClick={() => abrirAlta("mantenimientos")}>Nuevo</Button>}
        >
          {filtroControles}
          <div className="mt-4">
            <DataTable
              rows={porEstado(datos.mantenimientos)}
              rowKey={(fila) => fila.id}
              loading={cargando}
              columns={[
                { key: "codigo", header: "Código" },
                { key: "placa", header: "Placa" },
                { key: "tipo", header: "Tipo" },
                { key: "descripcion", header: "Descripción" },
                { key: "fecha_programada", header: "Programada" },
                { key: "costo", header: "Costo", render: (fila) => `S/ ${Number(fila.costo ?? 0).toFixed(2)}` },
                { key: "estado", header: "Estado", render: (fila) => <Estado valor={fila.estado} /> },
              ]}
              empty={{ icon: Wrench, title: "Sin mantenimientos", description: "Programa el primer mantenimiento." }}
            />
          </div>
        </SectionCard>
      )}

      {pestana === "preventivos" && (
        <SectionCard
          title="Mantenimiento preventivo"
          subtitle="Calculado con los kilómetros reales de las rutas y el odómetro"
          action={esAdmin && <Button size="sm" icon={Plus} onClick={() => abrirAlta("preventivos")}>Nuevo plan</Button>}
        >
          {filtroControles}
          <div className="mt-4">
            <DataTable
              rows={porEstado(datos.preventivos)}
              rowKey={(fila) => fila.id}
              loading={cargando}
              columns={[
                { key: "codigo", header: "Código" },
                { key: "placa", header: "Placa" },
                { key: "categoria", header: "Categoría" },
                { key: "km_actual", header: "Km actual", className: "nums" },
                { key: "km_restantes", header: "Km restantes", className: "nums" },
                { key: "fecha_limite", header: "Fecha límite" },
                { key: "estado", header: "Estado", render: (fila) => <Estado valor={fila.estado} /> },
                ...(esAdmin ? [{ key: "acciones", header: "Acciones", render: (fila) => (
                  <div className="flex gap-2">
                    <button type="button" aria-label="Editar" onClick={() => abrirEdicion("preventivos", fila)}><Pencil size={16} /></button>
                    <button type="button" aria-label="Eliminar" onClick={() => borrar("preventivos", fila.id)}><Trash2 size={16} /></button>
                  </div>
                ) }] : []),
              ]}
              empty={{ icon: CalendarRange, title: "Sin planes preventivos", description: "Crea un plan por vehículo y categoría." }}
            />
          </div>
        </SectionCard>
      )}

      {pestana === "combustible" && (
        <SectionCard
          title="Combustible y costos"
          subtitle="Rendimiento real por unidad y detección de consumos anómalos"
          action={esAdmin && <Button size="sm" icon={Plus} onClick={() => abrirAlta("combustible")}>Nueva carga</Button>}
        >
          {filtroControles}
          <div className="mt-4">
            <DataTable
              rows={porPlaca(datos.cargas)}
              rowKey={(fila) => fila.id}
              loading={cargando}
              columns={[
                { key: "codigo", header: "Código" },
                { key: "placa", header: "Placa" },
                { key: "fecha", header: "Fecha" },
                { key: "tipo_combustible", header: "Tipo" },
                { key: "galones", header: "Galones", className: "nums" },
                { key: "monto", header: "Monto", render: (fila) => `S/ ${Number(fila.monto ?? 0).toFixed(2)}` },
                { key: "rendimiento_km_gal", header: "Km/gal", className: "nums" },
                { key: "consumo_anomalo", header: "Alerta", render: (fila) => fila.consumo_anomalo ? <Badge tono="danger">Anómalo</Badge> : <Badge tono="success">Normal</Badge> },
                ...(esAdmin ? [{ key: "acciones", header: "Acciones", render: (fila) => (
                  <div className="flex gap-2">
                    <button type="button" aria-label="Editar" onClick={() => abrirEdicion("combustible", fila)}><Pencil size={16} /></button>
                    <button type="button" aria-label="Eliminar" onClick={() => borrar("combustible", fila.id)}><Trash2 size={16} /></button>
                  </div>
                ) }] : []),
              ]}
              empty={{ icon: Fuel, title: "Sin cargas", description: "Registra la primera carga de combustible." }}
            />
          </div>
        </SectionCard>
      )}

      {pestana === "alertas" && (
        <SectionCard title="Alertas del día" subtitle="Documentos, licencias, mantenimientos, preventivos y consumos">
          <DataTable
            rows={datos.alertas || []}
            rowKey={(fila) => fila.id}
            loading={cargando}
            columns={[
              { key: "tipo", header: "Tipo" },
              { key: "severidad", header: "Severidad", render: (fila) => <Estado valor={fila.severidad} /> },
              { key: "placa", header: "Placa", render: (fila) => fila.placa || "—" },
              { key: "titulo", header: "Aviso" },
              { key: "mensaje", header: "Detalle" },
              { key: "dias", header: "Días", className: "nums" },
            ]}
            empty={{ icon: BellRing, title: "Sin alertas", description: "Todo está al día." }}
          />
        </SectionCard>
      )}

      {pestana === "flota" && (
        <SectionCard title="Estado de la flota" subtitle="Haz clic en una placa para ver su ficha completa">
          <DataTable
            rows={datos.flota || []}
            rowKey={(fila) => fila.placa}
            onRowClick={verFicha}
            loading={cargando}
            columns={[
              { key: "placa", header: "Placa" },
              { key: "marca", header: "Marca" },
              { key: "estado_vehiculo", header: "Estado" },
              { key: "documentos_total", header: "Docs." },
              { key: "documentos_vencidos", header: "Vencidos" },
              { key: "proximo_vencimiento", header: "Próx. vencimiento" },
              { key: "estado_general", header: "Estado general", render: (fila) => <Estado valor={fila.estado_general} /> },
              { key: "apto_para_salir", header: "Apto", render: (fila) => <Badge tono={fila.apto_para_salir ? "success" : "danger"}>{fila.apto_para_salir ? "Sí" : "No"}</Badge> },
              { key: "motivos", header: "Motivos", render: (fila) => (fila.motivos_no_apto || []).join(", ") || "—" },
            ]}
            empty={{ icon: Truck, title: "Sin vehículos", description: "No hay unidades activas en la flota." }}
          />
        </SectionCard>
      )}

      {pestana === "licencias" && esAdmin && (
        <SectionCard title="Licencias de conductores" subtitle="Información personal visible solo para administradores">
          <DataTable
            rows={datos.licencias || []}
            rowKey={(fila) => fila.conductor_id}
            loading={cargando}
            columns={[
              { key: "nombre", header: "Conductor" },
              { key: "licencia_numero", header: "Número" },
              { key: "licencia_vencimiento", header: "Vencimiento" },
              { key: "dias_para_vencer", header: "Días", className: "nums" },
              { key: "estado", header: "Estado", render: (fila) => <Estado valor={fila.estado} /> },
              { key: "nivel_alerta", header: "Alerta", render: (fila) => <Estado valor={fila.nivel_alerta} /> },
            ]}
            empty={{ icon: ShieldCheck, title: "Sin licencias", description: "No hay licencias registradas en el núcleo." }}
          />
        </SectionCard>
      )}

      {pestana === "configuracion" && (
        <SectionCard title="Configuración" subtitle={esAdmin ? "Los cambios quedan registrados en auditoría" : "Solo lectura para almacén"}>
          {datos.configuracion && (
            <dl className="grid gap-4 sm:grid-cols-3">
              {Object.entries(datos.configuracion).filter(([clave]) => !clave.startsWith("actualizado")).map(([clave, valor]) => (
                <div key={clave} className="rounded-xl border border-slate-100 p-3">
                  <dt className="text-xs text-slate-500">{clave.replaceAll("_", " ")}</dt>
                  <dd className="font-semibold text-slate-800">{String(valor)}</dd>
                </div>
              ))}
            </dl>
          )}
          {esAdmin && datos.auditoria?.length > 0 && (
            <div className="mt-6">
              <h3 className="mb-2 text-sm font-semibold">Últimos movimientos</h3>
              <DataTable
                rows={datos.auditoria}
                rowKey={(fila) => fila.id}
                columns={[
                  { key: "accion", header: "Acción" },
                  { key: "entidad", header: "Entidad" },
                  { key: "usuario", header: "Usuario" },
                  { key: "creado_en", header: "Fecha" },
                ]}
              />
            </div>
          )}
        </SectionCard>
      )}

      <Modal open={Boolean(modal)} onClose={() => setModal(null)}>
        {modal === "ficha" && datos.ficha && (
          <div className="space-y-4">
            <h2 className="text-lg font-bold">Ficha de {datos.ficha.placa}</h2>
            <p className="text-sm text-slate-500">
              {datos.ficha.marca} · Odómetro {datos.ficha.odometro_actual ?? "—"} km · Estado {datos.ficha.estado_general}
            </p>
            <div className="flex flex-wrap gap-2">
              <Badge tono={datos.ficha.apto_para_salir ? "success" : "danger"}>
                {datos.ficha.apto_para_salir ? "Apto para salir" : "No apto para salir"}
              </Badge>
              {(datos.ficha.motivos_no_apto || []).map((motivo) => <Badge key={motivo} tono="danger">{motivo}</Badge>)}
            </div>
            <p className="text-sm">
              Documentos actuales: <strong>{datos.ficha.documentos_total}</strong> ·
              Vencidos: <strong>{datos.ficha.documentos_vencidos}</strong> ·
              Costo total: <strong>S/ {Number(datos.ficha.costos?.costo_total ?? 0).toFixed(2)}</strong>
            </p>
            {datos.ficha.preventivos?.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold">Preventivos</h3>
                {datos.ficha.preventivos.map((plan) => (
                  <p key={plan.id} className="text-sm text-slate-600">
                    {plan.categoria}: {plan.km_restantes} km restantes · <Estado valor={plan.estado} />
                  </p>
                ))}
              </div>
            )}
            <Button variant="secondary" block onClick={() => setModal(null)}>Cerrar</Button>
          </div>
        )}
        {FORMULARIOS[modal] && (
          <div className="space-y-4">
            <h2 className="text-lg font-bold">{editando ? "Editar" : "Nuevo"} registro</h2>
            <Formulario
              campos={FORMULARIOS[modal]}
              valores={valores}
              onChange={setValores}
              onSubmit={(normalizados) => guardar(modal, normalizados)}
              etiquetaBoton={editando ? "Guardar cambios" : "Crear"}
            />
            <Button variant="ghost" block onClick={() => setModal(null)}>Cancelar</Button>
          </div>
        )}
      </Modal>
    </div>
  );
}
