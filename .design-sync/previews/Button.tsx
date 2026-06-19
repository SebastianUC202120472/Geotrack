// Previews del botón estándar del panel: variantes de color, tamaños, icono
// y estados. Contenido realista del dominio (pedidos / rutas).
import { Button } from "frontend-geotrack";
import { Plus, Download, Trash2 } from "lucide-react";

const fila = { display: "flex", gap: 12, flexWrap: "wrap" as const, alignItems: "center" };

export const Variantes = () => (
  <div style={fila}>
    <Button variant="primary">Asignar ruta</Button>
    <Button variant="secondary">Editar</Button>
    <Button variant="ghost">Cancelar</Button>
    <Button variant="danger">Eliminar</Button>
  </div>
);

export const Tamanos = () => (
  <div style={fila}>
    <Button size="sm">Pequeño</Button>
    <Button size="md">Mediano</Button>
    <Button size="lg">Grande</Button>
  </div>
);

export const ConIcono = () => (
  <div style={fila}>
    <Button variant="primary" icon={Plus}>Nuevo pedido</Button>
    <Button variant="secondary" icon={Download}>Exportar</Button>
    <Button variant="danger" icon={Trash2}>Eliminar</Button>
  </div>
);

export const Estados = () => (
  <div style={fila}>
    <Button variant="primary">Activo</Button>
    <Button variant="primary" disabled>Deshabilitado</Button>
  </div>
);
