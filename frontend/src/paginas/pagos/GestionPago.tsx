import { type FormEvent, useEffect, useState } from 'react'
import { api } from '../../servicios_api/api'
import type { Pago, Pedido } from '../../modelos/tipos'
import { Campo, Cargando, etiqueta, fecha, moneda, porcentaje } from '../../componentes/Comunes'
import { Modal } from '../../componentes/Modal'

export function GestionPago({
  pedidoInicial,
  cerrar,
  actualizado,
  notificar,
}: {
  pedidoInicial: Pedido
  cerrar: () => void
  actualizado: (pedido: Pedido) => void
  notificar: (texto: string) => void
}) {
  const [pedido, setPedido] = useState(pedidoInicial)
  const [pagos, setPagos] = useState<Pago[]>([])
  const [cargando, setCargando] = useState(true)
  const [guardando, setGuardando] = useState(false)
  const [error, setError] = useState('')

  const cargar = async () => {
    setCargando(true)
    try {
      const datos = await api.pagos(pedidoInicial.id_pedido)
      setPedido(datos.pedido)
      setPagos(datos.pagos)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setCargando(false)
    }
  }
  useEffect(() => { void cargar() }, [])

  const saldado = pedido.saldo_restante <= 0

  const registrar = async (evento: FormEvent<HTMLFormElement>) => {
    evento.preventDefault()
    // currentTarget queda en null cuando el handler cede el control en el
    // primer await, así que hay que capturar el formulario antes.
    const formulario = evento.currentTarget
    const form = new FormData(formulario)
    const monto = Number(form.get('monto'))

    if (monto > pedido.saldo_restante) {
      setError(`El abono supera el saldo restante (${moneda(pedido.saldo_restante)}).`)
      return
    }

    setGuardando(true)
    setError('')
    try {
      const datos = await api.crearPago(pedido.id_pedido, {
        monto,
        metodo_pago: String(form.get('metodo_pago')),
      })
      // Se refresca con la respuesta y se relee el historial completo.
      setPedido(datos.pedido)
      setPagos((actual) => [datos.pago, ...actual])
      actualizado(datos.pedido)
      formulario.reset()
      notificar('Pago registrado y saldo actualizado.')
      await cargar()
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setGuardando(false)
    }
  }

  return (
    <Modal
      titulo={`Pagos · guía #${pedido.id_pedido}`}
      subtitulo={`${pedido.cliente_nombre} · total ${moneda(pedido.total)}`}
      cerrar={cerrar}
      ancho="amplio"
    >
      {error && <p className="aviso aviso--error">{error}</p>}
      <div className="gestion-pagos">
        <section className="boleta-grande">
          <span className="sobretitulo">Estado de cuenta</span>
          <h3>{pedido.cliente_nombre}</h3>
          <div className="boleta-grande__lineas">
            <p><span>Valor neto</span><b>{moneda(pedido.valor_neto)}</b></p>
            <p><span>IVA ({porcentaje(pedido.tasa_iva)})</span><b>{moneda(pedido.iva)}</b></p>
            <p><span>Total del pedido</span><b>{moneda(pedido.total)}</b></p>
            <p><span>Total pagado</span><b>{moneda(pedido.total_pagado)}</b></p>
          </div>
          <div className="boleta-grande__saldo">
            <span>Saldo restante</span>
            <strong>{moneda(pedido.saldo_restante)}</strong>
          </div>

          {saldado ? (
            <p className="aviso aviso--exito">
              Este pedido está pagado por completo. No quedan abonos por registrar.
            </p>
          ) : (
            <form className="formulario formulario-abono" onSubmit={registrar}>
              <Campo
                etiqueta="Monto del abono"
                ayuda={`Máximo ${moneda(pedido.saldo_restante)}`}
              >
                <input
                  name="monto"
                  type="number"
                  min="1"
                  max={pedido.saldo_restante}
                  step="1"
                  required
                  placeholder="20000"
                />
              </Campo>
              <Campo etiqueta="Método">
                <select name="metodo_pago" defaultValue="EFECTIVO">
                  <option>EFECTIVO</option>
                  <option>TRANSFERENCIA</option>
                  <option>TARJETA</option>
                </select>
              </Campo>
              <button className="boton boton--primario campo--completo" disabled={guardando}>
                {guardando ? 'Registrando…' : 'Registrar pago'}
              </button>
            </form>
          )}
        </section>

        <section className="historial-pagos">
          <header><span className="sobretitulo">Comprobantes</span><h3>Historial de pagos</h3></header>
          {cargando ? <Cargando /> : pagos.length === 0 ? (
            <p className="texto-tenue">Este pedido todavía no tiene abonos.</p>
          ) : (
            <ol>{pagos.map((pago) => (
              <li key={pago.id_pago}>
                <span className="punto-pago" />
                <div className="pago-detalle">
                  <strong>{moneda(pago.monto)}</strong>
                  <div className="pago-meta">
                    <span className={`insignia metodo-${pago.metodo_pago.toLowerCase()}`}>
                      {etiqueta(pago.metodo_pago)}
                    </span>
                    <time>{fecha(pago.fecha, true)}</time>
                  </div>
                </div>
              </li>
            ))}</ol>
          )}
        </section>
      </div>
    </Modal>
  )
}
