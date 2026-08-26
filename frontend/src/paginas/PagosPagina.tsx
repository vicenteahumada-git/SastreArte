import { type FormEvent, useEffect, useState } from 'react'
import { api } from '../servicios_api/api'
import type { Pedido } from '../modelos/tipos'
import { Cargando, EstadoVacio, fecha, moneda } from '../componentes/Comunes'
import { Icono } from '../componentes/Icono'
import { GestionPago } from './pagos/GestionPago'

export function PagosPagina({ notificar }: { notificar: (texto: string) => void }) {
  const [pedidos, setPedidos] = useState<Pedido[]>([])
  const [seleccionado, setSeleccionado] = useState<Pedido | null>(null)
  const [buscar, setBuscar] = useState('')
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')

  const cargar = async (termino = '') => {
    setCargando(true)
    try { setPedidos(await api.pedidos({ buscar: termino })) }
    catch (e) { setError((e as Error).message) }
    finally { setCargando(false) }
  }
  useEffect(() => { void cargar() }, [])
  const buscarPagos = (evento: FormEvent) => { evento.preventDefault(); void cargar(buscar) }
  const reemplazar = (pedido: Pedido) => setPedidos((actual) => actual.map((item) => item.id_pedido === pedido.id_pedido ? pedido : item))

  return (
    <div className="pagina">
      <section className="barra-herramientas"><form className="buscador" onSubmit={buscarPagos}><Icono nombre="buscar" /><input value={buscar} onChange={(e) => setBuscar(e.target.value)} placeholder="Buscar guía o cliente" /><button>Buscar</button></form></section>
      {error && <p className="aviso aviso--error">{error}</p>}
      {cargando ? <Cargando /> : pedidos.length === 0 ? <EstadoVacio titulo="No hay cuentas por mostrar" texto="Registra un pedido para comenzar." /> : (
        <section className="rejilla-cuentas">
          {pedidos.map((pedido) => {
            const porcentaje = pedido.total ? Math.min(100, Math.round((pedido.total_pagado / pedido.total) * 100)) : 100
            return <article className="cuenta-pedido" key={pedido.id_pedido}>
              <header><span>Guía #{pedido.id_pedido}</span><time>{fecha(pedido.fecha_entrega)}</time></header>
              <h2>{pedido.cliente_nombre}</h2><p>{pedido.descripcion}</p>
              <div className="progreso-pago"><span><i style={{ width: `${porcentaje}%` }} /></span><small>{porcentaje}% pagado</small></div>
              <div className="cuenta-pedido__montos"><div><span>Total</span><strong>{moneda(pedido.total)}</strong></div><div><span>Saldo</span><strong className={pedido.saldo_restante ? 'texto-alerta' : 'texto-ok'}>{moneda(pedido.saldo_restante)}</strong></div></div>
              <button className="boton boton--tinta" onClick={() => setSeleccionado(pedido)}>{pedido.saldo_restante > 0 ? 'Gestionar abonos' : 'Ver pagos'} <Icono nombre="flecha" /></button>
            </article>
          })}
        </section>
      )}
      {seleccionado && <GestionPago pedidoInicial={seleccionado} cerrar={() => setSeleccionado(null)} actualizado={(pedido) => { reemplazar(pedido); setSeleccionado(pedido) }} notificar={notificar} />}
    </div>
  )
}
