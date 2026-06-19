// Previews de la tarjeta de KPI: con barra de progreso, con texto de apoyo y
// la gama de tonos semánticos. Los valores se pasan como string para que la
// tarjeta muestre el número final de forma determinista en la captura (con
// number, el contador animado puede capturarse a mitad de la animación).
import { StatCard } from "frontend-geotrack";
import { CheckCircle2, Truck, Package, AlertTriangle, MapPin } from "lucide-react";

const grid2 = { display: "grid", gridTemplateColumns: "repeat(2, minmax(220px, 1fr))", gap: 16 };
const grid3 = { display: "grid", gridTemplateColumns: "repeat(3, minmax(180px, 1fr))", gap: 16 };

export const ConProgreso = () => (
  <div style={grid2}>
    <StatCard label="Pedidos entregados" value="128" icon={CheckCircle2} tone="success" progress={82} progressLabel="82% del total del día" />
    <StatCard label="En ruta" value="34" icon={Truck} tone="info" progress={45} progressLabel="45% en tránsito" />
  </div>
);

export const ConTexto = () => (
  <div style={grid2}>
    <StatCard label="Pedidos del mes" value="1 540" icon={Package} tone="brand" hint="Acumulado de junio" />
    <StatCard label="Incidencias" value="7" icon={AlertTriangle} tone="danger" hint="Requieren atención" />
  </div>
);

export const Tonos = () => (
  <div style={grid3}>
    <StatCard label="Marca" value="92" icon={MapPin} tone="brand" progress={92} />
    <StatCard label="Información" value="45" icon={Truck} tone="info" progress={45} />
    <StatCard label="Éxito" value="128" icon={CheckCircle2} tone="success" progress={82} />
    <StatCard label="Aviso" value="12" icon={AlertTriangle} tone="warning" progress={30} />
    <StatCard label="Peligro" value="7" icon={AlertTriangle} tone="danger" progress={15} />
  </div>
);
