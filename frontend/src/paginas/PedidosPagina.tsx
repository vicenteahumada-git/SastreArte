import { type FormEvent, useCallback, useEffect, useState } from 'react'
import { api } from '../servicios_api/api'
import {
  ESTADOS_PEDIDO,
  type OrdenPedido,
  type Pedido,
  type RolOperativo,
} from '../modelos/tipos'
import { Cargando, EstadoVacio, etiqueta, fecha, moneda } from '../componentes/Comunes'
import { Icono } from '../componentes/Icono'
import { DetallePedido } from './pedidos/DetallePedido'
import { NuevoPedido } from './pedidos/NuevoPedido'

const COLUMNAS: { clave: OrdenPedido; rotulo: string; clase?: string }[] = [
  { clave: 'id_pedido', rotulo: 'Guía' },
  { clave: 'cliente', rotulo: 'Cliente y encargo' },
  { clave: 'fecha_entrega', rotulo: 'Entrega', clase: 'col-entrega' },
  { clave: 'prioridad', rotulo: 'Urgencia' },
  { clave: 'estado', rotulo: 'Estado' },
]

export function PedidosPagina({
  rol,
  notificar,
  imprimirBoleta,
  abrirNuevo = false,
  nuevoAbierto,
}: {
  rol: RolOperativo
  notificar: (texto: string) => void
  imprimirBoleta: (pedido: Pedido) => void
  abrirNuevo?: boolean
  nuevoAbierto?: () => void
}) {
  const [pedidos, setPedidos] = useState<Pedido[]>([])
  const [buscar, setBuscar] = useState('')
  const [termino, setTermino] = useState('')
  const [estado, setEstado] = useState('')
  const [desde, setDesde] = useState('')
  const [hasta, setHasta] = useState('')
  const [orden, setOrden] = useState<OrdenPedido>('fecha_entrega')
  const [descendente, setDescendente] = useState(false)
  const [cargando, setCargando] = useState(true)
  const [nuevo, setNuevo] = useState(false)
  const [seleccionado, setSeleccionado] = useState<Pedido | null>(null)
  const [marcados, setMarcados] = useState<number[]>([])
  const [borrando, setBorrando] = useState(false)
  const [error, setError] = useState('')

  const cargar = useCallback(async () => {
    setCargando(true)
    try {
      setPedidos(await api.pedidos({
        buscar: termino,
        estado,
        desde,
        hasta,
        orden,
        direccion: descendente ? 'desc' : 'asc',
      }))
      setError('')
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setCargando(false)
    }
  }, [termino, estado, desde, hasta, orden, descendente])

  useEffect(() => { void cargar() }, [cargar])

  // Apertura desde la mesa general.
  useEffect(() => {
    if (abrirNuevo) {
      setNuevo(true)
      nuevoAbierto?.()
    }
  }, [abrirNuevo, nuevoAbierto])

  const buscarPedidos = (evento: FormEvent) => { evento.preventDefault(); setTermino(buscar) }

  const hayFiltros = Boolean(termino || estado || desde || hasta)
  const limpiarFiltros = () => {
    setBuscar(''); setTermino(''); setEstado(''); setDesde(''); setHasta('')
  }

  const ordenarPor = (clave: OrdenPedido) => {
    if (clave === orden) setDescendente((valor) => !valor)
    else { setOrden(clave); setDescendente(false) }
  }

  const reemplazar = (pedido: Pedido) =>
    setPedidos((actual) => actual.map((item) => (item.id_pedido === pedido.id_pedido ? pedido : item)))

  const alternar = (id: number) =>
    setMarcados((actual) => (actual.includes(id) ? actual.filter((x) => x !== id) : [...actual, id]))

  const todosMarcados = pedidos.length > 0 && marcados.length === pedidos.length
  const alternarTodos = () =>
    setMarcados(todosMarcados ? [] : pedidos.map((pedido) => pedido.id_pedido))

  const eliminarMarcados = async () => {
    const objetivo = pedidos.filter((pedido) => marcados.includes(pedido.id_pedido))
    const conPagos = objetivo.filter((pedido) => pedido.total_pagado > 0).length
    const detallePagos = conPagos
      ? `\n\nAtención: ${conPagos} ${conPagos === 1 ? 'tiene pagos registrados que también se borrarán' : 'tienen pagos registrados que también se borrarán'}.`
      : ''
    const resumen = objetivo.map((pedido) => `#${pedido.id_pedido} · ${pedido.cliente_nombre}`).join('\n')

    if (!window.confirm(`Se eliminarán ${objetivo.length} ${objetivo.length === 1 ? 'pedido' : 'pedidos'}:\n\n${resumen}${detallePagos}\n\nEsta acción no se puede deshacer.`)) return

    setBorrando(true)
    try {
      const resultado = await api.eliminarPedidos(marcados)
      setMarcados([])
      await cargar()
      notificar(
        `${resultado.cantidad} ${resultado.cantidad === 1 ? 'pedido eliminado' : 'pedidos eliminados'}` +
          (resultado.pagos_eliminados ? ` y ${resultado.pagos_eliminados} pagos asociados.` : '.'),
      )
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBorrando(false)
    }
  }

  const flecha = (clave: OrdenPedido) =>
    clave === orden ? <i className="indicador-orden">{descendente ? '▾' : '▴'}</i> : null

  const puedeEliminar = rol === 'DUENO'

  return (
    <div className="pagina">
      <section className="barra-herramientas">
        <form className="buscador" onSubmit={buscarPedidos}>
          <Icono nombre="buscar" />
          <input value={buscar} onChange={(e) => setBuscar(e.target.value)} placeholder="Buscar guía, cliente o descripción" />
          <button>Buscar</button>
        </form>
        <button className="boton boton--primario" onClick={() => setNuevo(true)}><Icono nombre="mas" /> Registrar pedido</button>
      </section>

      <section className="filtros-pedidos" aria-label="Filtros">
        <label>
          <span>Estado</span>
          <select value={estado} onChange={(e) => setEstado(e.target.value)}>
            <option value="">Todos</option>
            {ESTADOS_PEDIDO.map((valor) => (
              <option key={valor} value={valor}>{etiqueta(valor)}</option>
            ))}
          </select>
        </label>
        <label>
          <span>Entrega desde</span>
          <input type="date" value={desde} max={hasta || undefined} onChange={(e) => setDesde(e.target.value)} />
        </label>
        <label>
          <span>Entrega hasta</span>
          <input type="date" value={hasta} min={desde || undefined} onChange={(e) => setHasta(e.target.value)} />
        </label>
        {hayFiltros && (
          <button className="boton-texto" onClick={limpiarFiltros}>Limpiar filtros</button>
        )}
      </section>

      {error && <p className="aviso aviso--error">{error}</p>}

      {puedeEliminar && marcados.length > 0 && (
        <div className="barra-seleccion" role="status">
          <span><strong>{marcados.length}</strong> {marcados.length === 1 ? 'pedido seleccionado' : 'pedidos seleccionados'}</span>
          <div>
            <button className="boton boton--suave" onClick={() => setMarcados([])}>Quitar selección</button>
            <button className="boton boton--peligro" onClick={() => void eliminarMarcados()} disabled={borrando}>
              {borrando ? 'Eliminando…' : `Eliminar ${marcados.length === 1 ? 'pedido' : 'pedidos'}`}
            </button>
          </div>
        </div>
      )}

      {cargando ? <Cargando /> : pedidos.length === 0 ? (
        <EstadoVacio
          titulo={hayFiltros ? 'Ningún pedido coincide con los filtros' : 'No hay pedidos en esta mesa'}
          texto={hayFiltros ? 'Prueba ampliando el rango de fechas o quitando el estado.' : 'Registra el primer encargo.'}
          accion={hayFiltros
            ? <button className="boton boton--suave" onClick={limpiarFiltros}>Limpiar filtros</button>
            : <button className="boton boton--primario" onClick={() => setNuevo(true)}>Registrar pedido</button>}
        />
      ) : (
        <section className="panel tabla-contenedor tabla-pedidos">
          <header className="panel__cabecera">
            <div><span className="sobretitulo">Guías del taller</span><h2>{pedidos.length} pedidos registrados</h2></div>
            <small>Ordenados por {etiqueta(orden).toLowerCase()} {descendente ? '(descendente)' : '(ascendente)'}</small>
          </header>
          <table className="tabla">
            <thead>
              <tr>
                {puedeEliminar && (
                  <th className="col-marcar">
                    <input type="checkbox" checked={todosMarcados} onChange={alternarTodos} aria-label="Seleccionar todos los pedidos" />
                  </th>
                )}
                {COLUMNAS.map(({ clave, rotulo, clase }) => (
                  <th key={clave} className={clase}>
                    <button type="button" className="encabezado-orden" onClick={() => ordenarPor(clave)} aria-label={`Ordenar por ${rotulo}`}>
                      {rotulo} {flecha(clave)}
                    </button>
                  </th>
                ))}
                <th className="col-responsable">Responsable</th>
                {rol === 'DUENO' && <th>Total</th>}
                <th />
              </tr>
            </thead>
            <tbody>{pedidos.map((pedido) => (
              <tr key={pedido.id_pedido} className={`fila-prioridad prioridad-${(pedido.prioridad ?? 'media').toLowerCase()}${marcados.includes(pedido.id_pedido) ? ' fila-marcada' : ''}`}>
                {puedeEliminar && (
                  <td className="col-marcar">
                    <input type="checkbox" checked={marcados.includes(pedido.id_pedido)} onChange={() => alternar(pedido.id_pedido)} aria-label={`Seleccionar pedido ${pedido.id_pedido}`} />
                  </td>
                )}
                <td><strong>#{pedido.id_pedido}</strong></td>
                <td><strong>{pedido.cliente_nombre}</strong><p>{pedido.descripcion}</p></td>
                <td className="col-entrega"><time>{fecha(pedido.fecha_entrega, true)}</time></td>
                <td>
                  <span className={`insignia urgencia-${(pedido.prioridad ?? 'media').toLowerCase()}`}>
                    {etiqueta(pedido.prioridad)}
                  </span>
                </td>
                <td><span className={`insignia estado-${pedido.estado.toLowerCase()}`}>{etiqueta(pedido.estado)}</span></td>
                <td className="col-responsable">{pedido.trabajador_nombre || <span className="texto-tenue">Sin asignar</span>}</td>
                {rol === 'DUENO' && <td><strong>{moneda(pedido.total)}</strong><small className={pedido.saldo_restante ? 'texto-alerta' : 'texto-ok'}>{pedido.saldo_restante ? `${moneda(pedido.saldo_restante)} pendiente` : 'Pagado'}</small></td>}
                <td><button className="boton-icono" onClick={() => setSeleccionado(pedido)} aria-label={`Abrir pedido ${pedido.id_pedido}`}><Icono nombre="flecha" /></button></td>
              </tr>
            ))}</tbody>
          </table>
        </section>
      )}

      {nuevo && <NuevoPedido rol={rol} cerrar={() => setNuevo(false)} notificar={notificar} creado={(pedido) => { setNuevo(false); void cargar(); imprimirBoleta(pedido) }} />}
      {seleccionado && <DetallePedido rol={rol} imprimirBoleta={imprimirBoleta} pedidoInicial={seleccionado} cerrar={() => setSeleccionado(null)} notificar={notificar} actualizado={(pedido) => { reemplazar(pedido); setSeleccionado(pedido) }} />}
    </div>
  )
}
