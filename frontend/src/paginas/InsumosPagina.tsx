import { type FormEvent, useEffect, useMemo, useState } from 'react'
import { api } from '../servicios_api/api'
import {
  UNIDADES_MEDIDA,
  type DetalleInsumo,
  type Insumo,
  type Pedido,
} from '../modelos/tipos'
import { Campo, Cargando, EstadoVacio, etiqueta, unidad } from '../componentes/Comunes'
import { Icono } from '../componentes/Icono'
import { Modal } from '../componentes/Modal'
import { DetalleFila } from './insumos/DetalleFila'

type Vista = 'catalogo' | 'pedido'

export function InsumosPagina({ notificar }: { notificar: (texto: string) => void }) {
  const [vista, setVista] = useState<Vista>('catalogo')
  const [insumos, setInsumos] = useState<Insumo[]>([])
  const [pedidos, setPedidos] = useState<Pedido[]>([])
  const [pedidoId, setPedidoId] = useState<number | null>(null)
  const [detalles, setDetalles] = useState<DetalleInsumo[]>([])
  const [editando, setEditando] = useState<Insumo | 'nuevo' | null>(null)
  const [agregando, setAgregando] = useState(false)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState('')

  const cargarBase = async () => {
    setCargando(true)
    try {
      const [materiales, encargos] = await Promise.all([api.insumos(), api.pedidos()])
      setInsumos(materiales); setPedidos(encargos)
      if (!pedidoId && encargos.length) setPedidoId(encargos[0].id_pedido)
    } catch (e) { setError((e as Error).message) }
    finally { setCargando(false) }
  }
  useEffect(() => { void cargarBase() }, [])
  useEffect(() => { if (pedidoId) void api.insumosPedido(pedidoId).then(setDetalles).catch((e: Error) => setError(e.message)) }, [pedidoId])

  const disponibles = useMemo(() => insumos.filter((insumo) => !detalles.some((detalle) => detalle.id_insumo === insumo.id_insumo)), [insumos, detalles])
  const pedidoActual = pedidos.find((pedido) => pedido.id_pedido === pedidoId)

  const guardarCatalogo = async (evento: FormEvent<HTMLFormElement>) => {
    evento.preventDefault()
    const form = new FormData(evento.currentTarget)
    const datos = { nombre: String(form.get('nombre')), stock_actual: Number(form.get('stock_actual')), unidad_medida: String(form.get('unidad_medida')) }
    try {
      if (editando === 'nuevo') await api.crearInsumo(datos)
      else if (editando) await api.modificarInsumo(editando.id_insumo, datos)
      setEditando(null); notificar(editando === 'nuevo' ? 'Insumo agregado al catálogo.' : 'Insumo actualizado.'); await cargarBase()
    } catch (e) { setError((e as Error).message) }
  }

  const eliminarCatalogo = async (insumo: Insumo) => {
    if (!window.confirm(`¿Eliminar ${insumo.nombre} del catálogo?`)) return
    try { await api.eliminarInsumo(insumo.id_insumo); notificar('Insumo eliminado del catálogo.'); await cargarBase() }
    catch (e) { setError((e as Error).message) }
  }

  const agregarDetalle = async (evento: FormEvent<HTMLFormElement>) => {
    evento.preventDefault()
    if (!pedidoId) return
    const form = new FormData(evento.currentTarget)
    try {
      const detalle = await api.agregarInsumoPedido(pedidoId, { id_insumo: Number(form.get('id_insumo')), cantidad: Number(form.get('cantidad')), estado_insumo: String(form.get('estado_insumo')) })
      setDetalles((actual) => [...actual, detalle]); setAgregando(false); notificar('Insumo asociado al pedido.')
    } catch (e) { setError((e as Error).message) }
  }

  return (
    <div className="pagina">
      <div className="pestanas pestanas--pagina"><button className={vista === 'catalogo' ? 'activo' : ''} onClick={() => setVista('catalogo')}>Materiales existentes</button><button className={vista === 'pedido' ? 'activo' : ''} onClick={() => setVista('pedido')}>Insumos por pedido</button></div>
      {error && <p className="aviso aviso--error">{error}</p>}
      {cargando ? <Cargando /> : vista === 'catalogo' ? (
        <>
          <section className="barra-herramientas barra-herramientas--derecha"><button className="boton boton--primario" onClick={() => setEditando('nuevo')}><Icono nombre="mas" /> Agregar insumo</button></section>
          {insumos.length === 0 ? <EstadoVacio titulo="El estante está vacío" texto="Agrega los materiales habituales del taller." /> : (
            <section className="estante-insumos">{insumos.map((insumo) => <article className="tarjeta-insumo" key={insumo.id_insumo}><span className="muestra-material" /><div><span className="sobretitulo">Material I-{String(insumo.id_insumo).padStart(3, '0')}</span><h2>{insumo.nombre}</h2><p><strong>{insumo.stock_actual}</strong> {insumo.unidad_medida} disponibles</p></div><footer><button className="boton-texto" onClick={() => setEditando(insumo)}>Modificar</button><button className="boton-texto boton-texto--peligro" onClick={() => eliminarCatalogo(insumo)}>Eliminar</button></footer></article>)}</section>
          )}
        </>
      ) : (
        <section className="panel panel-insumos-pedido">
          <header className="panel__cabecera panel__cabecera--seleccion"><div><span className="sobretitulo">Mesa de materiales</span><h2>{pedidoActual ? `Guía #${pedidoActual.id_pedido}` : 'Selecciona un pedido'}</h2></div><select value={pedidoId ?? ''} onChange={(e) => setPedidoId(Number(e.target.value))}>{pedidos.map((pedido) => <option key={pedido.id_pedido} value={pedido.id_pedido}>#{pedido.id_pedido} · {pedido.cliente_nombre}</option>)}</select><button className="boton boton--primario" disabled={!pedidoId || disponibles.length === 0} onClick={() => setAgregando(true)}><Icono nombre="mas" /> Asociar insumo</button></header>
          <div className="cabecera-filas-insumo"><span>Material</span><span>Cantidad</span><span>Estado</span><span>Acciones</span></div>
          {detalles.length === 0 ? <EstadoVacio titulo="Sin materiales asociados" texto="Agrega los insumos requeridos para este encargo." /> : detalles.map((detalle) => <DetalleFila key={detalle.id_insumo} detalle={detalle} notificar={notificar} actualizado={(nuevo) => setDetalles((actual) => actual.map((item) => item.id_insumo === nuevo.id_insumo ? nuevo : item))} eliminado={(id) => setDetalles((actual) => actual.filter((item) => item.id_insumo !== id))} />)}
        </section>
      )}

      {editando && <Modal titulo={editando === 'nuevo' ? 'Agregar insumo' : 'Modificar insumo'} subtitulo="Stock simple, sin movimientos históricos." cerrar={() => setEditando(null)}><form className="formulario" onSubmit={guardarCatalogo}><Campo etiqueta="Nombre" ancho="campo--completo"><input name="nombre" required defaultValue={editando === 'nuevo' ? '' : editando.nombre} /></Campo><Campo etiqueta="Stock actual"><input name="stock_actual" type="number" min="0" step="0.01" required defaultValue={editando === 'nuevo' ? 0 : editando.stock_actual} /></Campo><Campo etiqueta="Unidad de medida"><select name="unidad_medida" required defaultValue={editando === 'nuevo' ? 'UNIDADES' : editando.unidad_medida}>{UNIDADES_MEDIDA.map((valor) => <option key={valor} value={valor}>{unidad(valor)}</option>)}</select></Campo><div className="acciones-formulario campo--completo"><button type="button" className="boton boton--suave" onClick={() => setEditando(null)}>Cancelar</button><button className="boton boton--primario">Guardar insumo</button></div></form></Modal>}
      {agregando && pedidoId && <Modal titulo="Asociar insumo al pedido" subtitulo={`Guía #${pedidoActual?.id_pedido} · ${pedidoActual?.cliente_nombre}`} cerrar={() => setAgregando(false)}><form className="formulario" onSubmit={agregarDetalle}><Campo etiqueta="Material" ancho="campo--completo"><select name="id_insumo" required>{disponibles.map((insumo) => <option key={insumo.id_insumo} value={insumo.id_insumo}>{insumo.nombre} · {insumo.stock_actual} {unidad(insumo.unidad_medida)}</option>)}</select></Campo><Campo etiqueta="Cantidad"><input name="cantidad" type="number" min="0.01" step="0.01" required defaultValue="1" /></Campo><Campo etiqueta="Estado"><select name="estado_insumo" defaultValue="PENDIENTE_COMPRA"><option value="PENDIENTE_COMPRA">{etiqueta('PENDIENTE_COMPRA')}</option><option value="COMPRADO">comprado</option></select></Campo><div className="acciones-formulario campo--completo"><button type="button" className="boton boton--suave" onClick={() => setAgregando(false)}>Cancelar</button><button className="boton boton--primario">Asociar material</button></div></form></Modal>}
    </div>
  )
}
