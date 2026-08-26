import { useEffect, useState } from 'react'
import { api } from '../servicios_api/api'
import type { ListaCompra, PendienteCompra } from '../modelos/tipos'
import { Cargando, EstadoVacio, etiqueta, fecha, unidad } from '../componentes/Comunes'
import { Icono } from '../componentes/Icono'

export function ComprasPagina({ notificar }: { notificar: (texto: string) => void }) {
  const [pendientes, setPendientes] = useState<PendienteCompra[]>([])
  const [listas, setListas] = useState<ListaCompra[]>([])
  const [seleccionada, setSeleccionada] = useState<ListaCompra | null>(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')

  const cargar = async () => {
    setCargando(true)
    try {
      const [materiales, historico] = await Promise.all([api.pendientesCompra(), api.listasCompra()])
      setPendientes(materiales); setListas(historico); setError('')
    } catch (e) { setError((e as Error).message) }
    finally { setCargando(false) }
  }
  useEffect(() => { void cargar() }, [])

  const generar = async () => {
    try {
      const lista = await api.generarListaCompra()
      setSeleccionada(lista); notificar(`Lista de compra #${lista.id_lista_compra} generada.`); await cargar()
    } catch (e) { setError((e as Error).message) }
  }
  const consultar = async (id: number) => {
    try { setSeleccionada(await api.listaCompra(id)) }
    catch (e) { setError((e as Error).message) }
  }
  const sePuedeGenerar = pendientes.some((item) => item.disponible_para_nueva_lista)

  if (cargando) return <Cargando />
  return (
    <div className="pagina pagina-compras">
      {error && <p className="aviso aviso--error">{error}</p>}
      <div className="rejilla-compras">
        <section className="panel pendientes-compra">
          <header className="panel__cabecera"><div><span className="sobretitulo">Materiales faltantes</span><h2>Pendientes de compra</h2></div><button className="boton boton--primario" disabled={!sePuedeGenerar} onClick={generar}><Icono nombre="compras" /> Generar lista</button></header>
          {pendientes.length === 0 ? <EstadoVacio titulo="No faltan materiales" texto="Todos los insumos asociados están marcados como comprados." /> : (
            <div className="lista-pendientes">{pendientes.map((item) => <article key={item.id_insumo}><span className="casilla-compra" /><div><strong>{item.nombre}</strong><small>Guías {item.pedidos}{item.stock_actual > 0 && ` · ${item.stock_actual} ${unidad(item.unidad_medida)} en bodega`}</small></div><b>{item.cantidad_a_comprar} {unidad(item.unidad_medida)}</b>{item.cantidad_a_comprar === 0 && <span className="insignia insignia--gris">hay en bodega</span>}{!item.disponible_para_nueva_lista && <span className="insignia insignia--gris">ya listada</span>}</article>)}</div>
          )}
        </section>
        <aside className="historial-listas">
          <span className="sobretitulo">Archivador</span><h2>Listas generadas</h2>
          {listas.length === 0 ? <p className="texto-tenue">Todavía no se ha generado ninguna lista.</p> : listas.map((lista) => <button key={lista.id_lista_compra} className={seleccionada?.id_lista_compra === lista.id_lista_compra ? 'activo' : ''} onClick={() => void consultar(lista.id_lista_compra)}><span>Lista #{lista.id_lista_compra}</span><small>{fecha(lista.fecha_generacion, true)} · {lista.cantidad_items} materiales</small><Icono nombre="flecha" tamano={17} /></button>)}
        </aside>
      </div>
      {seleccionada && (
        <section className="hoja-compra papel-costura">
          <header><div><img src="/logo-sastrearte.png" alt="SastreArte" /><span>Lista de compra #{seleccionada.id_lista_compra}</span></div><time>Generada el {fecha(seleccionada.fecha_generacion, true)}</time></header>
          <div className="hoja-compra__columnas"><span>Material</span><span>Pedido</span><span>Cantidad</span><span>Estado</span></div>
          {seleccionada.detalles?.map((detalle) => <article key={`${detalle.id_pedido}-${detalle.id_insumo}`}><span className="casilla-compra" /><strong>{detalle.nombre}</strong><span>Guía #{detalle.id_pedido}</span><b>{detalle.cantidad} {unidad(detalle.unidad_medida)}</b><span className="insignia insignia--ambar">{etiqueta(detalle.estado_insumo)}</span></article>)}
          <footer><span>Lista simple · sin movimientos históricos de inventario</span></footer>
        </section>
      )}
    </div>
  )
}
