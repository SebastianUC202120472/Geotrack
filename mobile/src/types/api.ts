// Tipos del dominio que reflejan EXACTAMENTE las respuestas del backend
// (app/schemas del FastAPI). Sirven para tipar el cliente HTTP y la UI.

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export type EstadoEntrega = "PENDIENTE" | "ENTREGADO" | "FALLIDO";

// Resumen de la ruta activa del conductor (GET /conductor/ruta-activa).
export interface RutaActiva {
  ruta_id: number;
  codigo?: string | null;
  nombre: string;
  estado: string; // CREADA | EN_PROGRESO | FINALIZADA
  fecha_creacion: string;
  vehiculo_placa?: string | null;
  total_paradas: number;
  pendientes: number;
  entregadas: number;
  fallidas: number;
}

// Una parada del manifiesto (GET /conductor/ruta-activa/manifiesto).
export interface ParadaManifiesto {
  secuencia: number;
  detalle_id: number;
  pedido_id: number;
  codigo?: string | null;
  cliente_origen: string;
  nombre_destinatario?: string | null;
  telefono_destinatario?: string | null;
  direccion_destino: string;
  distrito?: string | null;
  latitud?: number | null;
  longitud?: number | null;
  peso_kg?: number | null;
  estado_entrega: EstadoEntrega;
}

export interface Manifiesto {
  ruta_id: number;
  codigo?: string | null;
  nombre: string;
  estado: string;
  total_paradas: number;
  paradas: ParadaManifiesto[];
}

// Punto de navegación para el mapa (GET /conductor/ruta-activa/navegacion).
export interface ParadaNavegacion {
  secuencia: number;
  pedido_id: number;
  codigo?: string | null;
  latitud: number;
  longitud: number;
}

export interface Navegacion {
  ruta_id: number;
  total_paradas: number;
  paradas: ParadaNavegacion[];
}

// Resultado de gestionar una parada (estado o evidencia).
export interface GestionParada {
  pedido_id: number;
  codigo?: string | null;
  estado_entrega: string;
  motivo_fallo?: string | null;
  url_evidencia?: string | null;
  fecha_gestion?: string | null;
  mensaje: string;
}

export interface OptimizacionResultado {
  mensaje: string;
  total_paradas: number;
}

export interface CierreRuta {
  ruta_id: number;
  estado: string;
  total_paradas: number;
  entregadas: number;
  fallidas: number;
  pendientes: number;
  mensaje: string;
}

// Coordenadas geográficas simples (las que entrega expo-location).
export interface Coordenadas {
  latitud: number;
  longitud: number;
}
