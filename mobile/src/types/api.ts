// Tipos que reflejan las respuestas del backend (FastAPI schemas).

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export type EstadoEntrega = "PENDIENTE" | "ENTREGADO" | "FALLIDO";

// Resumen de la ruta activa del conductor.
export interface RutaActiva {
  ruta_id: number;
  codigo?: string | null;
  nombre: string;
  estado: string; // CREADA | EN_PROGRESO | FINALIZADA
  fecha_creacion: string;
  fecha_salida?: string | null;
  vehiculo_placa?: string | null;
  total_paradas: number;
  pendientes: number;
  entregadas: number;
  fallidas: number;
  pausada?: boolean;          // true si hay auxilio mecánico activo
  incidencia_id?: number | null;
  ayuda_enviada_en?: string | null;
  ayuda_detalle?: string | null;
  tipo?: string; // "ENTREGA" | "RECOJO"
}

// Una parada del manifiesto de entrega.
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
  url_evidencia?: string | null; // foto POD ya subida
}

export interface Manifiesto {
  ruta_id: number;
  codigo?: string | null;
  nombre: string;
  estado: string;
  total_paradas: number;
  paradas: ParadaManifiesto[];
}

// Punto de navegación para el mapa.
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

// Resultado de gestionar una parada.
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
  fecha_fin?: string | null;
  hora_inicio?: string | null;
  hora_fin?: string | null;
  duracion_minutos?: number | null;
  total_paradas: number;
  entregadas: number;
  fallidas: number;
  pendientes: number;
  mensaje: string;
}

// Coordenadas geográficas simples.
export interface Coordenadas {
  latitud: number;
  longitud: number;
}

// Perfil del conductor.
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

// Reporte de falla de un pedido.
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

// Incidencia de auxilio mecánico.
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
  puede_solucionar_solo?: boolean;
  ayuda_enviada_en?: string | null;
  ayuda_detalle?: string | null;
}

// Un punto de origen de la ruta de recojo.
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

// Resultado de registrar la recepción de un recojo.
export interface Recepcion {
  recojo_id: number;
  codigo?: string | null;
  estado: string;
  cantidad_declarada?: number | null;
  url_guia?: string | null;
  fotos?: string[] | null;
  fecha_recojo?: string | null;
  mensaje: string;
}
