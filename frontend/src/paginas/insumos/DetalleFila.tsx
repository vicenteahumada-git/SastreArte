import { type FormEvent, useState } from 'react'
import type { DetalleInsumo } from '../../modelos/tipos'
import { api } from '../../servicios_api/api'
import { etiqueta, unidad } from '../../componentes/Comunes'

export function DetalleFila({
  detalle,
  actualizado,
  eliminado,
  notificar,
}: {
  detalle: DetalleInsumo
  actualizado: (detalle: DetalleInsumo) => void
  eliminado: (id: number) => void
  notificar: (texto: string) => void
}) {
  const [editando, setEditando] = useState(false)
  const [error, setError] = useState('')

  const guardar = async (evento: FormEvent<HTMLFormElement>) => {
    evento.preventDefault()
    const form = new FormData(evento.currentTarget)
    try {
      const nuevo = await api.modificarInsumoPedido(detalle.id_pedido, detalle.id_insumo, {
        cantidad: Number(form.get('cantidad')),
        estado_insumo: String(form.get('estado_insumo')),
      })
      actualizado(nuevo); setEditando(false); setError(''); notificar('Insumo del pedido actualizado.')
    } catch (e) { setError((e as Error).message) }
  }

  const quitar = async () => {
    if (!window.confirm(`¿Quitar ${detalle.nombre} de este pedido?`)) return
    try { await api.eliminarInsumoPedido(detalle.id_pedido, detalle.id_insumo); eliminado(detalle.id_insumo); notificar('Insumo eliminado del pedido.') }
    catch (e) { setError((e as Error).message) }
  }

  if (editando) return (
    <form className="fila-insumo fila-insumo--edicion" onSubmit={guardar}>
      <div><strong>{detalle.nombre}</strong><small>{detalle.stock_actual} {unidad(detalle.unidad_medida)} en bodega</small></div>
      <input name="cantidad" type="number" min="0.01" step="0.01" defaultValue={detalle.cantidad} aria-label="Cantidad" />
      <select name="estado_insumo" defaultValue={detalle.estado_insumo}><option>PENDIENTE_COMPRA</option><option>COMPRADO</option></select>
      <div><button className="boton-texto">Guardar</button><button type="button" className="boton-texto" onClick={() => setEditando(false)}>Cancelar</button></div>
      {error && <small className="texto-alerta">{error}</small>}
    </form>
  )

  // Si lo que pide el pedido supera lo que hay, conviene que salte a la
  // vista: es la diferencia entre poder empezar el encargo o no.
  const alcanza = Number(detalle.stock_actual) >= Number(detalle.cantidad)

  return (
    <article className="fila-insumo">
      <div>
        <strong>{detalle.nombre}</strong>
        <small className={alcanza ? undefined : 'texto-alerta'}>
          {detalle.stock_actual} {unidad(detalle.unidad_medida)} en bodega
          {!alcanza && ' · no alcanza'}
        </small>
      </div>
      <b>{detalle.cantidad}</b>
      <span className={`insignia ${detalle.estado_insumo === 'COMPRADO' ? 'insignia--verde' : 'insignia--ambar'}`}>{etiqueta(detalle.estado_insumo)}</span>
      <div><button className="boton-texto" onClick={() => setEditando(true)}>Modificar</button><button className="boton-texto boton-texto--peligro" onClick={quitar}>Eliminar</button></div>
      {error && <small className="texto-alerta">{error}</small>}
    </article>
  )
}

