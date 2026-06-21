// Previews de la etiqueta de estado: gama de tonos semánticos y un ejemplo
// con punto de color a la izquierda.
import { Badge } from "frontend-geotrack";

const fila = { display: "flex", gap: 10, flexWrap: "wrap" as const, alignItems: "center" };

export const Tonos = () => (
  <div style={fila}>
    <Badge tono="neutral">Neutral</Badge>
    <Badge tono="info">Información</Badge>
    <Badge tono="brand">Marca</Badge>
    <Badge tono="success">Entregado</Badge>
    <Badge tono="warning">Pendiente</Badge>
    <Badge tono="danger">Fallido</Badge>
  </div>
);

export const ConPunto = () => (
  <div style={fila}>
    <Badge tono="success">
      <span style={{ width: 6, height: 6, borderRadius: 999, background: "#16a34a" }} />
      En línea
    </Badge>
    <Badge tono="warning">
      <span style={{ width: 6, height: 6, borderRadius: 999, background: "#f59e0b" }} />
      Esperando
    </Badge>
    <Badge tono="danger">
      <span style={{ width: 6, height: 6, borderRadius: 999, background: "#dc2626" }} />
      Sin señal
    </Badge>
  </div>
);
