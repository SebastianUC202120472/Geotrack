import { useEffect, useState } from "react";
import { RefreshCw, MapPin } from "lucide-react";
import PageHeader from "../components/ui/PageHeader";
import Card from "../components/ui/Card";
import Button from "../components/ui/Button";
import MapaFlota from "../components/MapaFlota";
import { obtenerUbicacionesFlota } from "../services/api";

const REFRESCO_MS = 15000; // el mapa se actualiza solo cada 15 s (polling)

// Seguimiento de conductores en el mapa: posición en vivo de cada conductor con
// ruta activa y sus pedidos pendientes (Leaflet + OpenStreetMap).
export default function SeguimientoConductores() {
  const [ubicaciones, setUbicaciones] = useState([]);
  const [cargando, setCargando] = useState(true);

  // Carga manual (botón "Actualizar"), con indicador de carga.
  const actualizar = () => {
    setCargando(true);
    obtenerUbicacionesFlota()
      .then(setUbicaciones)
      .catch((err) => console.error("No se pudo cargar el mapa:", err.message))
      .finally(() => setCargando(false));
  };

  // Carga inicial + refresco automático cada 15 s (sin parpadeo). Los setState van
  // dentro de los callbacks de la promesa, no en el cuerpo del efecto.
  useEffect(() => {
    let activo = true;
    const traer = () =>
      obtenerUbicacionesFlota()
        .then((u) => activo && setUbicaciones(u))
        .catch(() => {})
        .finally(() => activo && setCargando(false));
    traer();
    const id = setInterval(traer, REFRESCO_MS);
    return () => {
      activo = false;
      clearInterval(id);
    };
  }, []);

  return (
    <div className="space-y-6 p-6 lg:p-8 animate-fade-in">
      <PageHeader titulo="Seguimiento de Conductores" subtitulo="Ubicación en vivo de cada conductor y sus pedidos pendientes.">
        <Button variant="secondary" icon={RefreshCw} onClick={actualizar}>Actualizar</Button>
      </PageHeader>

      {cargando ? (
        <Card><p className="py-10 text-center text-sm text-slate-500">Cargando mapa…</p></Card>
      ) : ubicaciones.length === 0 ? (
        <Card>
          <div className="py-12 text-center text-sm text-slate-400">
            <MapPin className="mx-auto mb-3 opacity-40" size={36} />
            <p>No hay conductores con ruta activa enviando su ubicación.</p>
          </div>
        </Card>
      ) : (
        <MapaFlota conductores={ubicaciones} />
      )}
    </div>
  );
}
