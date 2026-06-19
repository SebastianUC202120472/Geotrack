// Previews de la etiqueta de estado automática: traduce el código de estado a
// su color (y punto) sin tener que recordar el mapeo. Dos filas: estados de
// pedido y estados de ruta / vehículo.
import { EstadoBadge } from "frontend-geotrack";

const fila = { display: "flex", gap: 10, flexWrap: "wrap" as const, alignItems: "center" };

export const Pedidos = () => (
  <div style={fila}>
    <EstadoBadge estado="PENDIENTE" />
    <EstadoBadge estado="ASIGNADO" />
    <EstadoBadge estado="EN_RUTA" />
    <EstadoBadge estado="ENTREGADO" />
    <EstadoBadge estado="FALLIDO" />
  </div>
);

export const RutasYVehiculos = () => (
  <div style={fila}>
    <EstadoBadge estado="CREADA" />
    <EstadoBadge estado="EN_PROGRESO" />
    <EstadoBadge estado="FINALIZADA" />
    <EstadoBadge estado="DISPONIBLE" />
    <EstadoBadge estado="GEOCODIFICACION_FALLIDA" />
  </div>
);
