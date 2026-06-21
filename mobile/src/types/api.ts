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
  fecha_salida?: string | null; // CUS-23: salida del almacén (null si aún no inició)
  vehiculo_placa?: string | null;
  total_paradas: number;
  pendientes: number;
  entregadas: number;
  fallidas: number;
  pausada?: boolean;          // CUS-30: la ruta está pausada por un auxilio mecánico
  incidencia_id?: number | null;
  tipo?: string; // "ENTREGA" | "RECOJO" — la app elige el flujo de entregas o recepción
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
  url_evidencia?: string | null; // foto POD ya subida (CUS-26), servida en /media
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

// Resultado de validar un paquete por QR contra la ruta activa (CUS-22).
export interface ValidacionQR {
  pertenece: boolean;
  mensaje: string;
  parada?: ParadaManifiesto | null;
}

export interface CierreRuta {
  ruta_id: number;
  estado: string;
  fecha_fin?: string | null;
  hora_inicio?: string | null;      // CUS-28: salida (o creación si no hubo salida)
  hora_fin?: string | null;         // CUS-28: cierre de la ruta
  duracion_minutos?: number | null; // CUS-28: horas trabajadas, en minutos
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

// Perfil del conductor (GET /conductor/perfil).
export interface PerfilConductor {
  usuario_id: number;
  codigo?: string | null;
  correo: string;
  nombre?: string | null;
  telefono?: string | null;
  dni?: string | null;
  vehiculo?: { id: number; codigo?: string | null; placa: string } | null;
  foto_url?: string | null;
}

// Reporte de incidencia de un pedido.
export interface Reporte {
  id: number;
  pedido_id: number;
  pedido_codigo?: string | null;
  direccion_destino?: string | null;
  motivo: string;
  descripcion?: string | null;
  estado: string; // ABIERTO | RESUELTO
  respuesta?: string | null;
  accion?: string | null;
  creado_en?: string | null;
  respondido_en?: string | null;
}

// Incidencia de auxilio mecánico (CUS-30).
export interface Incidencia {
  id: number;
  codigo?: string | null;
  ruta_id: number;
  ruta_nombre?: string | null;
  conductor_id: number;
  conductor_nombre?: string | null;
  vehiculo_placa?: string | null;
  tipo: string;
  descripcion?: string | null;
  url_evidencia?: string | null;
  latitud?: number | null;
  longitud?: number | null;
  estado: string; // ABIERTA | RESUELTA
  creado_en?: string | null;
  resuelto_en?: string | null;
  nota_resolucion?: string | null;
}

// Un punto de origen de la ruta de recojo (GET /conductor/recojo/manifiesto).
export interface ParadaRecojo {
  secuencia: number;
  recojo_id: number;
  codigo?: string | null;
  cliente_origen: string;
  direccion_origen: string;
  distrito?: string | null;
  latitud?: number | null;
  longitud?: number | null;
  volumen_estimado_m3?: number | null;
  estado: string; // SOLICITADO | ASIGNADO | EN_RUTA | RECOGIDO
  cantidad_declarada?: number | null;
  url_guia?: string | null;
}

export interface ManifiestoRecojo {
  ruta_id: number;
  codigo?: string | null;
  nombre: string;
  estado: string;
  total_paradas: number;
  paradas: ParadaRecojo[];
}

// Resultado de registrar la recepción condicionada (CUS-12).
export interface Recepcion {
  recojo_id: number;
  codigo?: string | null;
  estado: string;
  cantidad_declarada?: number | null;
  url_guia?: string | null;
  fecha_recojo?: string | null;
  mensaje: string;
}
