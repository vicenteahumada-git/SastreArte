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
      <div><strong>{detalle.nombre}</strong><small>{unidad(detalle.unidad_medida)}</small></div>
      <input name="cantidad" type="number" min="0.01" step="0.01" defaultValue={detalle.cantidad} aria-label="Cantidad" />
      <select name="estado_insumo" defaultValue={detalle.estado_insumo}><option value="REQUERIDO">requerido</option><option value="CONSUMIDO">consumido</option></select>
      <div><button className="boton-texto">Guardar</button><button type="button" className="boton-texto" onClick={() => setEditando(false)}>Cancelar</button></div>
      {error && <small className="texto-alerta">{error}</small>}
    </form>
  )

  return (
    <article className="fila-insumo">
      <div><strong>{detalle.nombre}</strong><small>{unidad(detalle.unidad_medida)}</small></div>
      <b>{detalle.cantidad}</b>
      <span className={`insignia ${detalle.estado_insumo === 'CONSUMIDO' ? 'insignia--verde' : 'insignia--ambar'}`} title={detalle.estado_insumo === 'CONSUMIDO' ? 'Ya salió de bodega' : `Anotado; hay ${detalle.stock_actual} en bodega`}>{etiqueta(detalle.estado_insumo)}</span>
      <div><button className="boton-texto" onClick={() => setEditando(true)}>Modificar</button><button className="boton-texto boton-texto--peligro" onClick={quitar}>Eliminar</button></div>
      {error && <small className="texto-alerta">{error}</small>}
    </article>
  )
}

