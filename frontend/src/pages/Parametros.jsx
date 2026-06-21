import { useEffect, useState } from "react";
import { SlidersHorizontal, Plus, Trash2, AlertCircle, Ban, Fuel, Save } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import SectionCard from "../components/ui/SectionCard";
import Input from "../components/ui/Input";
import Button from "../components/ui/Button";
import { listarMotivos, crearMotivo, eliminarMotivo, obtenerCombustible, actualizarCombustible } from "../services/api";

// Parámetros del sistema (CUS-06). Por ahora: motivos de rechazo, que la app del
// conductor usa al reportar una entrega fallida (antes estaban fijos en el código).
export default function Parametros() {
  const [motivos, setMotivos] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [texto, setTexto] = useState("");
  const [aviso, setAviso] = useState(null);
  const [guardando, setGuardando] = useState(false);

  // Estado de los parámetros de combustible (CUS-34): consumo L/100km y precio S//L.
  const [combustible, setCombustible] = useState({ consumo_l_100km: "", precio_soles_litro: "" });
  const [guardandoComb, setGuardandoComb] = useState(false);

  // Carga los parámetros de combustible al montar (setState en callback de promesa).
  useEffect(() => {
    let activo = true;
    obtenerCombustible()
      .then((c) => activo && setCombustible({ consumo_l_100km: c.consumo_l_100km, precio_soles_litro: c.precio_soles_litro }))
      .catch(() => {});
    return () => { activo = false; };
  }, []);

  // Guarda los parámetros de combustible en el backend.
  const guardarCombustible = (e) => {
    e.preventDefault();
    setGuardandoComb(true);
    actualizarCombustible(Number(combustible.consumo_l_100km), Number(combustible.precio_soles_litro))
      .then(() => alert("Parámetros de combustible guardados"))
      .catch((err) => alert(err.message))
      .finally(() => setGuardandoComb(false));
  };

  // Sin setCargando(true) síncrono (inicia en true; refresca en callbacks de promesa)
  // para no disparar el error de lint "setState síncrono en effect".
  const cargar = async () => {
    try { setMotivos(await listarMotivos()); }
    catch (err) { console.error("No se pudo cargar motivos:", err.message); }
    finally { setCargando(false); }
  };

  // Carga inicial con setState en callbacks de promesa (evita el lint de effect).
  useEffect(() => {
    let activo = true;
    listarMotivos()
      .then((d) => activo && setMotivos(d))
      .catch(() => {})
      .finally(() => activo && setCargando(false));
    return () => { activo = false; };
  }, []);

  const agregar = async (e) => {
    e.preventDefault();
    setAviso(null);
    if (texto.trim().length < 3) { setAviso({ texto: "El motivo debe tener al menos 3 caracteres." }); return; }
    setGuardando(true);
    try {
      await crearMotivo(texto.trim());
      setTexto("");
      cargar();
    } catch (err) {
      setAviso({ texto: err.message });
    } finally {
      setGuardando(false);
    }
  };

  const quitar = async (id) => {
    setAviso(null);
    try { await eliminarMotivo(id); cargar(); }
    catch (err) { setAviso({ texto: err.message }); }
  };

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-in">
      <PageHeader titulo="Parámetros" subtitulo="Catálogos del sistema. Los motivos de rechazo se usan en la app al reportar una entrega fallida." />

      <div className="grid gap-6 lg:grid-cols-3 animate-fade-up">
        <SectionCard title="Agregar motivo de rechazo" className="lg:col-span-1">
          <form onSubmit={agregar} noValidate className="space-y-4">
            <Input label="Motivo" value={texto} onChange={(e) => { setTexto(e.target.value); setAviso(null); }}
              placeholder="Ej. Cliente no responde" hint="Aparecerá en la app del conductor" />
            <Button type="submit" icon={Plus} block disabled={guardando}>{guardando ? "Agregando…" : "Agregar motivo"}</Button>
            {aviso && (
              <div className="flex items-center gap-2 rounded-xl bg-danger-soft px-3.5 py-3 text-sm text-danger-strong">
                <AlertCircle size={18} /> <span>{aviso.texto}</span>
              </div>
            )}
          </form>
        </SectionCard>

        <SectionCard title="Motivos de rechazo" subtitle="Los que ve el conductor al reportar una falla." className="lg:col-span-2">
          {cargando ? (
            <p className="text-sm text-slate-400">Cargando…</p>
          ) : motivos.length === 0 ? (
            <div className="flex flex-col items-center gap-2 py-8 text-slate-400">
              <Ban size={28} /> <p className="text-sm">No hay motivos. Agrega el primero.</p>
            </div>
          ) : (
            <ul className="divide-y divide-slate-100">
              {motivos.map((m) => (
                <li key={m.id} className="flex items-center justify-between py-3">
                  <span className="flex items-center gap-2 text-sm text-slate-700">
                    <SlidersHorizontal size={15} className="text-slate-400" /> {m.texto}
                  </span>
                  <Button variant="ghost" size="sm" icon={Trash2} onClick={() => quitar(m.id)}>Quitar</Button>
                </li>
              ))}
            </ul>
          )}
        </SectionCard>
      </div>

      {/* Sección de combustible (CUS-34): consumo y precio para calcular el ahorro */}
      <div className="grid gap-6 animate-fade-up">
        <SectionCard
          title="Combustible (CUS-34)"
          subtitle="Parámetros para calcular el ahorro de combustible en los KPIs del dashboard."
          className="lg:max-w-md"
        >
          <form onSubmit={guardarCombustible} noValidate className="space-y-4">
            <Input
              label="Consumo (L/100 km)"
              type="number"
              min="0"
              step="0.1"
              value={combustible.consumo_l_100km}
              onChange={(e) => setCombustible((prev) => ({ ...prev, consumo_l_100km: e.target.value }))}
              placeholder="Ej. 12.5"
              hint="Litros consumidos por cada 100 km recorridos"
            />
            <Input
              label="Precio del combustible (S/ / L)"
              type="number"
              min="0"
              step="0.01"
              value={combustible.precio_soles_litro}
              onChange={(e) => setCombustible((prev) => ({ ...prev, precio_soles_litro: e.target.value }))}
              placeholder="Ej. 16.50"
              hint="Precio en soles por litro de combustible"
            />
            <Button type="submit" icon={Save} block disabled={guardandoComb}>
              {guardandoComb ? "Guardando…" : "Guardar parámetros"}
            </Button>
          </form>
        </SectionCard>
      </div>
    </div>
  );
}
