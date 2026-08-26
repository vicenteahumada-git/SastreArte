import { useEffect, useState } from 'react'
import { api } from '../servicios_api/api'
import type { ListaCompra, PendienteCompra } from '../modelos/tipos'
import { Cargando, EstadoVacio, fecha, unidad } from '../componentes/Comunes'
import { Icono } from '../componentes/Icono'

const INSIGNIA: Record<ListaCompra['estado'], string> = {
  ABIERTA: 'insignia insignia--ambar',
  RECIBIDA: 'insignia insignia--verde',
  ANULADA: 'insignia insignia--gris',
}

export function ComprasPagina({ notificar }: { notificar: (texto: string) => void }) {
  const [pendientes, setPendientes] = useState<PendienteCompra[]>([])
  const [listas, setListas] = useState<ListaCompra[]>([])
  const [seleccionada, setSeleccionada] = useState<ListaCompra | null>(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')

  const cargar = async (idSeleccion?: number) => {
    setCargando(true)
    try {
      const [materiales, historico] = await Promise.all([api.pendientesCompra(), api.listasCompra()])
      setPendientes(materiales); setListas(historico); setError('')
      if (idSeleccion) setSeleccionada(await api.listaCompra(idSeleccion))
    } catch (e) { setError((e as Error).message) }
    finally { setCargando(false) }
  }
  useEffect(() => { void cargar() }, [])

  const generar = async () => {
    try {
      const lista = await api.generarListaCompra()
      notificar(`Lista de compra #${lista.id_lista_compra} generada.`)
      await cargar(lista.id_lista_compra)
    } catch (e) { setError((e as Error).message) }
  }
  const consultar = async (id: number) => {
    try { setSeleccionada(await api.listaCompra(id)) }
    catch (e) { setError((e as Error).message) }
  }
  // Recibir la compra es lo que hace entrar el material a bodega: de acá sale
  // el movimiento que sube el stock, y por eso se pide confirmación.
  const recibir = async (lista: ListaCompra) => {
    if (!window.confirm(`Se dará por recibida la lista #${lista.id_lista_compra} y los materiales entrarán a bodega.\n\n¿Llegó todo lo pedido?`)) return
    try {
      await api.recibirListaCompra(lista.id_lista_compra)
      notificar('Compra recibida: el stock quedó actualizado.')
      await cargar(lista.id_lista_compra)
    } catch (e) { setError((e as Error).message) }
  }
  const anular = async (lista: ListaCompra) => {
    if (!window.confirm(`Se anulará la lista #${lista.id_lista_compra}. Los materiales volverán a figurar como faltantes.`)) return
    try {
      await api.anularListaCompra(lista.id_lista_compra)
      notificar('Lista anulada.')
      await cargar(lista.id_lista_compra)
    } catch (e) { setError((e as Error).message) }
  }

  if (cargando) return <Cargando />
  return (
    <div className="pagina pagina-compras">
      {error && <p className="aviso aviso--error">{error}</p>}
      <div className="rejilla-compras">
        <section className="panel pendientes-compra">
          <header className="panel__cabecera"><div><span className="sobretitulo">Materiales faltantes</span><h2>Pendientes de compra</h2></div><button className="boton boton--primario" disabled={pendientes.length === 0} onClick={generar}><Icono nombre="compras" /> Generar lista</button></header>
          {pendientes.length === 0 ? <EstadoVacio titulo="No falta ningún material" texto="Lo que piden los pedidos activos está en bodega o ya fue solicitado en una lista abierta." /> : (
            <div className="lista-pendientes">{pendientes.map((item) => <article key={item.id_insumo}><span className="casilla-compra" /><div><strong>{item.nombre}</strong><small>Guías {item.pedidos} · piden {item.requerido}, hay {item.stock_actual}{Number(item.en_camino) > 0 && `, ${item.en_camino} en camino`}</small></div><b>{item.cantidad_a_comprar} {unidad(item.unidad_medida)}</b></article>)}</div>
          )}
        </section>
        <aside className="historial-listas">
          <span className="sobretitulo">Archivador</span><h2>Listas generadas</h2>
          {listas.length === 0 ? <p className="texto-tenue">Todavía no se ha generado ninguna lista.</p> : listas.map((lista) => <button key={lista.id_lista_compra} className={seleccionada?.id_lista_compra === lista.id_lista_compra ? 'activo' : ''} onClick={() => void consultar(lista.id_lista_compra)}><span>Lista #{lista.id_lista_compra}</span><small>{fecha(lista.fecha_generacion, true)} · {lista.cantidad_items} materiales · {lista.estado.toLowerCase()}</small><Icono nombre="flecha" tamano={17} /></button>)}
        </aside>
      </div>
      {seleccionada && (
        <section className="hoja-compra papel-costura">
          <header><div><img src="/logo-sastrearte.png" alt="SastreArte" /><span>Lista de compra #{seleccionada.id_lista_compra}</span><span className={INSIGNIA[seleccionada.estado]}>{seleccionada.estado.toLowerCase()}</span></div><time>Generada el {fecha(seleccionada.fecha_generacion, true)}{seleccionada.fecha_recepcion && ` · recibida el ${fecha(seleccionada.fecha_recepcion, true)}`}</time></header>
          <div className="hoja-compra__columnas"><span>Material</span><span>Solicitado</span><span>Recibido</span></div>
          {seleccionada.detalles?.map((detalle) => <article key={detalle.id_insumo}><span className="casilla-compra" /><strong>{detalle.nombre}</strong><b>{detalle.cantidad_solicitada} {unidad(detalle.unidad_medida)}</b><span>{detalle.cantidad_recibida === null ? '—' : `${detalle.cantidad_recibida} ${unidad(detalle.unidad_medida)}`}</span></article>)}
          <footer>
            {seleccionada.estado === 'ABIERTA' ? (
              <div className="acciones-formulario">
                <button className="boton boton--suave" onClick={() => void anular(seleccionada)}>Anular</button>
                <button className="boton boton--primario" onClick={() => void recibir(seleccionada)}>Marcar recibida</button>
              </div>
            ) : <span>Los materiales de esta lista ya no figuran como faltantes.</span>}
          </footer>
        </section>
      )}
    </div>
  )
}
