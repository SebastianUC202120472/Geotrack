// Previews de la cabecera de página: solo título, con subtítulo, y con
// acciones a la derecha. Es un componente con mucho texto — buena prueba de
// la tipografía (Inter) del sistema.
import { PageHeader, Button } from "frontend-geotrack";
import { Plus, Download } from "lucide-react";

const caja = { maxWidth: 720 };

export const Simple = () => (
  <div style={caja}>
    <PageHeader titulo="Pedidos" />
  </div>
);

export const ConSubtitulo = () => (
  <div style={caja}>
    <PageHeader
      titulo="Seguimiento de conductores"
      subtitulo="Posición en vivo y paradas de cada ruta activa"
    />
  </div>
);

export const ConAcciones = () => (
  <div style={caja}>
    <PageHeader titulo="Conductores" subtitulo="12 activos · 3 sin vehículo asignado">
      <Button variant="secondary" size="sm" icon={Download}>Exportar</Button>
      <Button variant="primary" size="sm" icon={Plus}>Nuevo conductor</Button>
    </PageHeader>
  </div>
);
