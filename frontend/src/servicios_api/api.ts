import type {
  Cliente,
  DetalleInsumo,
  MovimientoInsumo,
  FiltrosPedido,
  Insumo,
  ListaCompra,
  Pago,
  Pedido,
  PendienteCompra,
  Resumen,
  SesionUsuario,
  Trabajador,
} from '../modelos/tipos'

// Ruta relativa: el servidor de Vite hace de proxy hacia el backend, así que
// el navegador siempre pide al mismo origen desde el que cargó la página.
// Apuntar a http://localhost:8000 rompería al abrir la app desde otro equipo
// o a través de un túnel, porque ese localhost sería el del visitante.
const API = import.meta.env.VITE_API_URL ?? '/api'

async function solicitud<T>(ruta: string, opciones?: RequestInit): Promise<T> {
  const respuesta = await fetch(`${API}${ruta}`, {
    ...opciones,
    headers: {
      'Content-Type': 'application/json',
      'X-Rol-Operativo': localStorage.getItem('sastrearte_rol') ?? 'DUENO',
      // Evita la página intermedia que ngrok interpone en su plan gratuito.
      'ngrok-skip-browser-warning': 'true',
      ...opciones?.headers,
    },
  })
  const cuerpo = await respuesta.json().catch(() => ({}))
  if (!respuesta.ok) {
    throw new Error(cuerpo.error ?? 'No fue posible completar la operación.')
  }
  return cuerpo.datos as T
}

const json = (metodo: string, datos?: unknown): RequestInit => ({
  method: metodo,
  body: datos === undefined ? undefined : JSON.stringify(datos),
})

export const api = {
  iniciarSesion: (datos: { nombre_usuario: string; contrasena: string }) =>
    solicitud<SesionUsuario>('/sesion', json('POST', datos)),

  resumen: () => solicitud<Resumen>('/resumen'),

  clientes: (buscar = '') =>
    solicitud<Cliente[]>(`/clientes${buscar ? `?buscar=${encodeURIComponent(buscar)}` : ''}`),
  crearCliente: (datos: Pick<Cliente, 'nombre' | 'telefono'>) =>
    solicitud<Cliente>('/clientes', json('POST', datos)),
  modificarCliente: (id: number, datos: Pick<Cliente, 'nombre' | 'telefono'>) =>
    solicitud<Cliente>(`/clientes/${id}`, json('PUT', datos)),
  eliminarCliente: (id: number) =>
    solicitud<{ eliminado: boolean; id_cliente: number }>(
      `/clientes/${id}`,
      json('DELETE'),
    ),

  pedidos: (filtros: FiltrosPedido = {}) => {
    const parametros = new URLSearchParams()
    for (const [clave, valor] of Object.entries(filtros)) {
      if (valor) parametros.set(clave, String(valor))
    }
    const cadena = parametros.toString()
    return solicitud<Pedido[]>(`/pedidos${cadena ? `?${cadena}` : ''}`)
  },
  pedido: (id: number) => solicitud<Pedido>(`/pedidos/${id}`),
  crearPedido: (datos: Record<string, unknown>) =>
    solicitud<Pedido>('/pedidos', json('POST', datos)),
  modificarPedido: (id: number, datos: Record<string, unknown>) =>
    solicitud<Pedido>(`/pedidos/${id}`, json('PUT', datos)),
  actualizarEstado: (id: number, estado: string) =>
    solicitud<Pedido>(`/pedidos/${id}/estado`, json('PATCH', { estado })),
  actualizarPrioridad: (id: number, prioridad: string) =>
    solicitud<Pedido>(`/pedidos/${id}/prioridad`, json('PATCH', { prioridad })),
  actualizarPrecio: (id: number, datos: Record<string, unknown>) =>
    solicitud<Pedido>(`/pedidos/${id}/precio`, json('PATCH', datos)),
  /** Asigna o reasigna: si ya tenía responsable, lo reemplaza. */
  asignar: (id: number, id_trabajador: number) =>
    solicitud(`/pedidos/${id}/asignacion`, json('POST', { id_trabajador })),
  desasignar: (id: number) => solicitud(`/pedidos/${id}/asignacion`, json('DELETE')),
  eliminarPedidos: (ids: number[]) =>
    solicitud<{ eliminados: number[]; cantidad: number; pagos_eliminados: number }>(
      '/pedidos/eliminar',
      json('POST', { ids }),
    ),

  pagos: (idPedido: number) =>
    solicitud<{ pedido: Pedido; pagos: Pago[] }>(`/pedidos/${idPedido}/pagos`),
  crearPago: (idPedido: number, datos: { monto: number; metodo_pago: string }) =>
    solicitud<{ pedido: Pedido; pago: Pago }>(
      `/pedidos/${idPedido}/pagos`,
      json('POST', datos),
    ),

  trabajadores: (estado = '') =>
    solicitud<Trabajador[]>(`/trabajadores${estado ? `?estado=${estado}` : ''}`),
  crearTrabajador: (datos: Record<string, unknown>) =>
    solicitud<Trabajador>('/trabajadores', json('POST', datos)),
  modificarTrabajador: (id: number, datos: Record<string, unknown>) =>
    solicitud<Trabajador>(`/trabajadores/${id}`, json('PUT', datos)),
  darBajaTrabajador: (id: number) =>
    solicitud<Trabajador>(`/trabajadores/${id}/baja`, json('PATCH')),

  insumos: () => solicitud<Insumo[]>('/insumos'),
  crearInsumo: (datos: Record<string, unknown>) =>
    solicitud<Insumo>('/insumos', json('POST', datos)),
  modificarInsumo: (id: number, datos: Record<string, unknown>) =>
    solicitud<Insumo>(`/insumos/${id}`, json('PUT', datos)),
  eliminarInsumo: (id: number) => solicitud(`/insumos/${id}`, json('DELETE')),
  insumosPedido: (idPedido: number) =>
    solicitud<DetalleInsumo[]>(`/pedidos/${idPedido}/insumos`),
  agregarInsumoPedido: (idPedido: number, datos: Record<string, unknown>) =>
    solicitud<DetalleInsumo>(`/pedidos/${idPedido}/insumos`, json('POST', datos)),
  modificarInsumoPedido: (
    idPedido: number,
    idInsumo: number,
    datos: Record<string, unknown>,
  ) =>
    solicitud<DetalleInsumo>(
      `/pedidos/${idPedido}/insumos/${idInsumo}`,
      json('PUT', datos),
    ),
  eliminarInsumoPedido: (idPedido: number, idInsumo: number) =>
    solicitud(`/pedidos/${idPedido}/insumos/${idInsumo}`, json('DELETE')),

  pendientesCompra: () => solicitud<PendienteCompra[]>('/listas-compra/pendientes'),
  listasCompra: () => solicitud<ListaCompra[]>('/listas-compra'),
  listaCompra: (id: number) => solicitud<ListaCompra>(`/listas-compra/${id}`),
  generarListaCompra: () => solicitud<ListaCompra>('/listas-compra', json('POST')),
  recibirListaCompra: (id: number, recibidas: Record<number, number> = {}) =>
    solicitud<ListaCompra>(`/listas-compra/${id}/recepcion`, json('PATCH', { recibidas })),
  anularListaCompra: (id: number) =>
    solicitud<ListaCompra>(`/listas-compra/${id}/anulacion`, json('PATCH')),
  ajustarStock: (id: number, datos: Record<string, unknown>) =>
    solicitud<Insumo>(`/insumos/${id}/ajuste`, json('PATCH', datos)),
  movimientosInsumo: (id: number) =>
    solicitud<MovimientoInsumo[]>(`/insumos/${id}/movimientos`),
}
