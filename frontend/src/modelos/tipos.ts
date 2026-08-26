export type RolOperativo = 'DUENO' | 'TRABAJADOR'

export interface SesionUsuario {
  id_usuario: number
  nombre: string
  apellido: string | null
  tipo_usuario: 'DUENO' | 'TRABAJADOR'
}

// Dominios cerrados del pedido. El backend los valida en servicios/pedidos.py,
// la base los replica con CHECK y GET /api/pedidos/opciones los expone.
export const ESTADOS_PEDIDO = [
  'PENDIENTE',
  'EN_PROCESO',
  'LISTO_PARA_ENTREGA',
  'ENTREGADO',
  'CANCELADO',
] as const
export const PRIORIDADES = ['BAJA', 'MEDIA', 'ALTA', 'URGENTE'] as const
export const COMPLEJIDADES = ['BAJA', 'MEDIA', 'ALTA'] as const

export type EstadoPedido = (typeof ESTADOS_PEDIDO)[number]
export type Prioridad = (typeof PRIORIDADES)[number]
export type Complejidad = (typeof COMPLEJIDADES)[number]

/** Columnas por las que la API permite ordenar el listado de pedidos. */
export const ORDENES_PEDIDO = [
  'id_pedido',
  'fecha_entrega',
  'fecha_registro',
  'cliente',
  'estado',
  'prioridad',
] as const
export type OrdenPedido = (typeof ORDENES_PEDIDO)[number]

/**
 * Unidades en que el taller mide sus materiales. "UNIDADES" cubre lo que se
 * cuenta de a uno: botones, cierres, conos de hilo.
 */
export const UNIDADES_MEDIDA = ['MM', 'CM', 'METROS', 'UNIDADES'] as const
export type UnidadMedida = (typeof UNIDADES_MEDIDA)[number]

/** Filtros aceptados por GET /api/pedidos. */
export interface FiltrosPedido {
  buscar?: string
  estado?: string
  orden?: OrdenPedido
  direccion?: 'asc' | 'desc'
  /** Rango de fecha de entrega, en formato AAAA-MM-DD. */
  desde?: string
  hasta?: string
}
export type Seccion =
  | 'resumen'
  | 'pedidos'
  | 'clientes'
  | 'pagos'
  | 'insumos'
  | 'compras'
  | 'trabajadores'

export interface Cliente {
  id_cliente: number
  nombre: string
  telefono: string
}

export interface Trabajador {
  id_usuario: number
  nombre: string
  apellido: string | null
  telefono: string | null
  estado_usuario: 'ACTIVO' | 'INACTIVO'
  tipo_usuario: 'TRABAJADOR'
}

export interface Pedido {
  /** Identificador y número de guía a la vez: nunca se reutiliza. */
  id_pedido: number
  id_cliente: number
  fecha_registro: string
  fecha_entrega: string
  descripcion: string
  estado: EstadoPedido
  prioridad: Prioridad | null
  complejidad: Complejidad | null
  tiempo_estimado_horas: number | null
  valor_base: number
  descuento: number
  recargo: number
  valor_neto: number
  /** Tasa que regía al registrar el pedido; queda congelada en la base. */
  tasa_iva: number
  /** Derivados de la tasa por el backend; no se guardan. */
  iva: number
  total: number
  total_pagado: number
  saldo_restante: number
  cliente_nombre: string
  cliente_telefono: string
  id_trabajador: number | null
  trabajador_nombre: string | null
}

export interface Pago {
  id_pago: number
  id_pedido: number
  monto: number
  fecha: string
  metodo_pago: 'EFECTIVO' | 'TRANSFERENCIA' | 'TARJETA'
}

export interface Insumo {
  id_insumo: number
  nombre: string
  stock_actual: number
  unidad_medida: UnidadMedida
}

export interface DetalleInsumo extends Insumo {
  id_pedido: number
  cantidad: number
  /** REQUERIDO: anotado. CONSUMIDO: ya salió de bodega y dejó su movimiento. */
  estado_insumo: 'REQUERIDO' | 'CONSUMIDO'
}

export interface MovimientoInsumo {
  id_movimiento: number
  cantidad: number
  motivo: 'INVENTARIO_INICIAL' | 'COMPRA' | 'CONSUMO' | 'AJUSTE' | 'DEVOLUCION'
  id_pedido: number | null
  id_lista_compra: number | null
  observacion: string | null
  fecha: string
}

export interface PendienteCompra {
  id_insumo: number
  nombre: string
  unidad_medida: UnidadMedida
  stock_actual: number
  /** Lo que piden los pedidos activos. */
  requerido: number
  /** Lo ya solicitado en listas abiertas. */
  en_camino: number
  /** requerido − stock − en_camino: lo que hay que salir a comprar. */
  cantidad_a_comprar: number
  cantidad_pedidos: number
  pedidos: string | null
}

export interface ListaCompra {
  id_lista_compra: number
  fecha_generacion: string
  fecha_recepcion: string | null
  estado: 'ABIERTA' | 'RECIBIDA' | 'ANULADA'
  cantidad_items?: number
  total_solicitado?: number
  detalles?: Array<{
    id_insumo: number
    nombre: string
    unidad_medida: UnidadMedida
    cantidad_solicitada: number
    cantidad_recibida: number | null
  }>
}

export interface Resumen {
  metricas: {
    pedidos_totales: number
    pedidos_activos: number
    entregas_semana: number
    clientes: number
    trabajadores_activos: number
    saldo_pendiente: number
    insumos_pendientes: number
  }
  estados: Array<{ estado: string; cantidad: number }>
  proximos: Pedido[]
}

