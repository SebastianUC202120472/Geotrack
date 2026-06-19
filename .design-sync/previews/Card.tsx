// Previews de la tarjeta-superficie: con cabecera, con acción a la derecha y
// sin cabecera (contenido libre).
import { Card, Button, EstadoBadge } from "frontend-geotrack";

const caja = { maxWidth: 380 };
const cuerpo = { margin: 0, color: "#475569", fontSize: 14, lineHeight: 1.5 };

export const ConCabecera = () => (
  <div style={caja}>
    <Card title="Resumen del día" subtitle="18 de junio, 2026">
      <p style={cuerpo}>128 pedidos entregados de 156 programados. 7 incidencias reportadas.</p>
    </Card>
  </div>
);

export const ConAccion = () => (
  <div style={caja}>
    <Card
      title="Ruta Miraflores"
      subtitle="8 paradas · Juan Pérez"
      action={<Button size="sm" variant="secondary">Ver ruta</Button>}
    >
      <div style={{ display: "flex", gap: 8 }}>
        <EstadoBadge estado="EN_RUTA" />
      </div>
    </Card>
  </div>
);

export const SinCabecera = () => (
  <div style={caja}>
    <Card hover>
      <p style={cuerpo}>Tarjeta sin cabecera, con elevación al pasar el cursor. Útil para listas de elementos clicables.</p>
    </Card>
  </div>
);
