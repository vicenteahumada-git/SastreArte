import { type FormEvent, useEffect, useState } from 'react'
import { api } from '../../servicios_api/api'
import {
  COMPLEJIDADES,
  ESTADOS_PEDIDO,
  PRIORIDADES,
  type Pedido,
  type RolOperativo,
  type Trabajador,
} from '../../modelos/tipos'
import { Campo, etiqueta, fecha, moneda, porcentaje } from '../../componentes/Comunes'
import { Icono } from '../../componentes/Icono'
import { Modal } from '../../componentes/Modal'

type Pestana = 'encargo' | 'precio' | 'asignacion'

export function DetallePedido({
  pedidoInicial,
  rol,
  cerrar,
  actualizado,
  notificar,
  imprimirBoleta,
}: {
  pedidoInicial: Pedido
  rol: RolOperativo
  cerrar: () => void
  actualizado: (pedido: Pedido) => void
  notificar: (texto: string) => void
  imprimirBoleta: (pedido: Pedido) => void
}) {
  const [pedido, setPedido] = useState(pedidoInicial)
  const [pestana, setPestana] = useState<Pestana>('encargo')
  const [trabajadores, setTrabajadores] = useState<Trabajador[]>([])
  const [error, setError] = useState('')

  const [reasignando, setReasignando] = useState(false)

  useEffect(() => { void api.trabajadores('ACTIVO').then(setTrabajadores) }, [])

  const reemplazar = (nuevo: Pedido, mensaje: string) => {
    setPedido(nuevo); actualizado(nuevo); notificar(mensaje); setError('')
  }

  const guardarEncargo = async (evento: FormEvent<HTMLFormElement>) => {
    evento.preventDefault()
    const form = new FormData(evento.currentTarget)
    try {
      let nuevo = await api.modificarPedido(pedido.id_pedido, {
        descripcion: String(form.get('descripcion')),
        fecha_entrega: String(form.get('fecha_entrega')),
        complejidad: String(form.get('complejidad')),
        tiempo_estimado_horas: Number(form.get('tiempo_estimado_horas')),
      })
      nuevo = await api.actualizarEstado(pedido.id_pedido, String(form.get('estado')))
      if (rol === 'DUENO') nuevo = await api.actualizarPrioridad(pedido.id_pedido, String(form.get('prioridad')))
      reemplazar(nuevo, 'Datos del pedido actualizados.')
    } catch (e) { setError((e as Error).message) }
  }

  const guardarPrecio = async (evento: FormEvent<HTMLFormElement>) => {
    evento.preventDefault()
    const form = new FormData(evento.currentTarget)
    try {
      const nuevo = await api.actualizarPrecio(pedido.id_pedido, {
        valor_base: Number(form.get('valor_base')),
        descuento: Number(form.get('descuento')),
        recargo: Number(form.get('recargo')),
      })
      reemplazar(nuevo, 'Condiciones económicas actualizadas.')
    } catch (e) { setError((e as Error).message) }
  }

  const asignar = async (evento: FormEvent<HTMLFormElement>) => {
    evento.preventDefault()
    const form = new FormData(evento.currentTarget)
    const eraReasignacion = Boolean(pedido.id_trabajador)
    try {
      await api.asignar(pedido.id_pedido, Number(form.get('id_trabajador')))
      const nuevo = await api.pedido(pedido.id_pedido)
      setReasignando(false)
      reemplazar(nuevo, eraReasignacion ? 'Responsable actualizado.' : 'Pedido asignado al trabajador.')
    } catch (e) { setError((e as Error).message) }
  }

  const quitarAsignacion = async () => {
    try {
      await api.desasignar(pedido.id_pedido)
      const nuevo = await api.pedido(pedido.id_pedido)
      setReasignando(false)
      reemplazar(nuevo, 'Se quitó el responsable del pedido.')
    } catch (e) { setError((e as Error).message) }
  }

  return (
    <Modal titulo={`Guía #${pedido.id_pedido}`} subtitulo={`${pedido.cliente_nombre} · entrega ${fecha(pedido.fecha_entrega, true)}`} cerrar={cerrar} ancho="amplio">
      <div className="resumen-guia">
        <div><span>Estado</span><strong className={`insignia estado-${pedido.estado.toLowerCase()}`}>{etiqueta(pedido.estado)}</strong></div>
        <div><span>Total</span><strong>{moneda(pedido.total)}</strong></div>
        <div><span>Saldo</span><strong className={pedido.saldo_restante > 0 ? 'texto-alerta' : 'texto-ok'}>{moneda(pedido.saldo_restante)}</strong></div>
        <div><span>Responsable</span><strong>{pedido.trabajador_nombre || 'Sin asignar'}</strong></div>
      </div>
      <div className="acciones-guia">
        <button type="button" className="boton boton--suave" onClick={() => imprimirBoleta(pedido)}>
          <Icono nombre="impresora" /> Imprimir boleta
        </button>
      </div>
      <div className="pestanas">
        <button className={pestana === 'encargo' ? 'activo' : ''} onClick={() => setPestana('encargo')}>Encargo</button>
        {rol === 'DUENO' && <button className={pestana === 'precio' ? 'activo' : ''} onClick={() => setPestana('precio')}>Precio</button>}
        <button className={pestana === 'asignacion' ? 'activo' : ''} onClick={() => setPestana('asignacion')}>Asignación</button>
      </div>
      {error && <p className="aviso aviso--error">{error}</p>}

      {pestana === 'encargo' && (
        <form className="formulario" onSubmit={guardarEncargo}>
          <Campo etiqueta="Descripción" ancho="campo--completo"><textarea name="descripcion" rows={4} required defaultValue={pedido.descripcion} /></Campo>
          <Campo etiqueta="Fecha de entrega"><input name="fecha_entrega" type="date" required defaultValue={pedido.fecha_entrega} /></Campo>
          <Campo etiqueta="Estado"><select name="estado" defaultValue={pedido.estado}>{ESTADOS_PEDIDO.map((valor) => <option key={valor} value={valor}>{etiqueta(valor)}</option>)}</select></Campo>
          <Campo etiqueta="Complejidad"><select name="complejidad" defaultValue={pedido.complejidad ?? 'MEDIA'}>{COMPLEJIDADES.map((valor) => <option key={valor} value={valor}>{etiqueta(valor)}</option>)}</select></Campo>
          <Campo etiqueta="Horas estimadas"><input name="tiempo_estimado_horas" type="number" min="0" step="0.5" defaultValue={pedido.tiempo_estimado_horas ?? 0} /></Campo>
          {rol === 'DUENO' && <Campo etiqueta="Prioridad"><select name="prioridad" defaultValue={pedido.prioridad ?? 'MEDIA'}>{PRIORIDADES.map((valor) => <option key={valor} value={valor}>{etiqueta(valor)}</option>)}</select></Campo>}
          <div className="acciones-formulario campo--completo"><button className="boton boton--primario">Guardar cambios</button></div>
        </form>
      )}

      {pestana === 'precio' && rol === 'DUENO' && (
        <div className="precio-pedido">
          <form className="formulario" onSubmit={guardarPrecio}>
            <Campo etiqueta="Valor base"><input name="valor_base" type="number" min="0" step="1" defaultValue={pedido.valor_base} /></Campo>
            <Campo etiqueta="Descuento ($)"><input name="descuento" type="number" min="0" step="1" defaultValue={pedido.descuento} /></Campo>
            <Campo etiqueta="Recargo ($)"><input name="recargo" type="number" min="0" step="1" defaultValue={pedido.recargo} /></Campo>
            <div className="acciones-formulario campo--completo"><button className="boton boton--primario">Recalcular pedido</button></div>
          </form>
          <aside className="boleta-precio">
            <span className="sobretitulo">Cálculo automático</span>
            <p><span>Valor neto</span><b>{moneda(pedido.valor_neto)}</b></p>
            <p><span>IVA ({porcentaje(pedido.tasa_iva)})</span><b>{moneda(pedido.iva)}</b></p>
            <p className="boleta-precio__total"><span>Total</span><b>{moneda(pedido.total)}</b></p>
            <p><span>Pagado</span><b>{moneda(pedido.total_pagado)}</b></p>
            <p><span>Saldo restante</span><b>{moneda(pedido.saldo_restante)}</b></p>
          </aside>
        </div>
      )}

      {pestana === 'asignacion' && (
        <section className="asignacion-pedido">
          {pedido.id_trabajador && !reasignando ? (
            <div className="asignado-actual">
              <span className="avatar-grande">{pedido.trabajador_nombre?.charAt(0)}</span>
              <div>
                <span>Pedido asignado a</span>
                <h3>{pedido.trabajador_nombre}</h3>
                <p>Un pedido mantiene un solo responsable a la vez, pero podés cambiarlo.</p>
                <div className="acciones-asignacion">
                  <button type="button" className="boton boton--suave" onClick={() => setReasignando(true)}>Cambiar responsable</button>
                  <button type="button" className="boton-texto" onClick={() => void quitarAsignacion()}>Quitar asignación</button>
                </div>
              </div>
            </div>
          ) : (
            <form className="formulario" onSubmit={asignar}>
              <Campo etiqueta={pedido.id_trabajador ? 'Nuevo responsable' : 'Trabajador activo'} ancho="campo--completo">
                <select name="id_trabajador" required defaultValue={pedido.id_trabajador ?? ''}>
                  <option value="" disabled>Selecciona una persona</option>
                  {trabajadores.map((t) => <option key={t.id_usuario} value={t.id_usuario}>{t.nombre} {t.apellido}</option>)}
                </select>
              </Campo>
              <div className="acciones-formulario campo--completo">
                {reasignando && <button type="button" className="boton boton--suave" onClick={() => setReasignando(false)}>Cancelar</button>}
                <button className="boton boton--primario">{pedido.id_trabajador ? 'Guardar responsable' : 'Asignar pedido'}</button>
              </div>
            </form>
          )}
        </section>
      )}
    </Modal>
  )
}

