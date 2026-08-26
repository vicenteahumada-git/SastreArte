import { type FormEvent, useEffect, useState } from 'react'
import { api } from '../../servicios_api/api'
import {
  COMPLEJIDADES,
  PRIORIDADES,
  type Cliente,
  type Pedido,
  type RolOperativo,
} from '../../modelos/tipos'
import { Campo, etiqueta } from '../../componentes/Comunes'
import { Icono } from '../../componentes/Icono'
import { Modal } from '../../componentes/Modal'

export function NuevoPedido({
  rol,
  cerrar,
  creado,
  notificar,
}: {
  rol: RolOperativo
  cerrar: () => void
  creado: (pedido: Pedido) => void
  notificar: (texto: string) => void
}) {
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [seleccionado, setSeleccionado] = useState<Cliente | null>(null)
  const [busqueda, setBusqueda] = useState('')
  const [nuevoCliente, setNuevoCliente] = useState(false)
  const [error, setError] = useState('')
  const [guardando, setGuardando] = useState(false)

  useEffect(() => {
    void api.clientes().then(setClientes).catch((e: Error) => setError(e.message))
  }, [])

  const filtrar = async (termino: string) => {
    setBusqueda(termino)
    try { setClientes(await api.clientes(termino)) }
    catch (e) { setError((e as Error).message) }
  }

  const registrarCliente = async (evento: FormEvent<HTMLFormElement>) => {
    evento.preventDefault()
    const datos = new FormData(evento.currentTarget)
    try {
      const cliente = await api.crearCliente({ nombre: String(datos.get('nombre_cliente')), telefono: String(datos.get('telefono_cliente')) })
      setSeleccionado(cliente); setClientes((actual) => [cliente, ...actual]); setNuevoCliente(false)
      notificar('Cliente registrado y asociado al nuevo pedido.')
    } catch (e) { setError((e as Error).message) }
  }

  const guardarPedido = async (evento: FormEvent<HTMLFormElement>) => {
    evento.preventDefault()
    if (!seleccionado) { setError('Selecciona o registra un cliente antes de confirmar.'); return }
    const form = new FormData(evento.currentTarget)
    setGuardando(true)
    try {
      // El número de guía es el id_pedido, que asigna PostgreSQL al insertar.
      const pedido = await api.crearPedido({
        id_cliente: seleccionado.id_cliente,
        fecha_entrega: String(form.get('fecha_entrega')),
        descripcion: String(form.get('descripcion')),
        estado: 'PENDIENTE',
        prioridad: String(form.get('prioridad')),
        complejidad: String(form.get('complejidad')),
        tiempo_estimado_horas: Number(form.get('tiempo_estimado_horas')),
        valor_base: Number(form.get('valor_base')),
        descuento: rol === 'DUENO' ? Number(form.get('descuento')) : 0,
        recargo: rol === 'DUENO' ? Number(form.get('recargo')) : 0,
      })
      notificar(`Pedido #${pedido.id_pedido} registrado.`)
      creado(pedido)
    } catch (e) { setError((e as Error).message) }
    finally { setGuardando(false) }
  }

  return (
    <Modal titulo="Registrar pedido" subtitulo="Primero asocia a la persona; el n.º de guía se asigna al confirmar." cerrar={cerrar} ancho="amplio">
      {error && <p className="aviso aviso--error">{error}</p>}
      <div className="registro-pedido">
        <section className="selector-cliente">
          <div className="paso-formulario"><b>1</b><div><span>Asociar cliente</span><small>Busca por nombre o teléfono</small></div></div>
          <div className="buscador buscador--compacto"><Icono nombre="buscar" /><input value={busqueda} onChange={(e) => void filtrar(e.target.value)} placeholder="Ej. Amalia o 5010" /></div>
          <div className="selector-cliente__lista">
            {clientes.slice(0, 6).map((cliente) => (
              <button key={cliente.id_cliente} className={seleccionado?.id_cliente === cliente.id_cliente ? 'seleccionado' : ''} onClick={() => setSeleccionado(cliente)}>
                <span className="avatar-letra">{cliente.nombre.charAt(0)}</span><span><strong>{cliente.nombre}</strong><small>{cliente.telefono}</small></span>{seleccionado?.id_cliente === cliente.id_cliente && <i>Asociado</i>}
              </button>
            ))}
          </div>
          <button className="boton-texto" onClick={() => setNuevoCliente((valor) => !valor)}><Icono nombre="mas" tamano={17} /> Registrar cliente nuevo</button>
          {nuevoCliente && (
            <form className="mini-formulario" onSubmit={registrarCliente}>
              <input name="nombre_cliente" required placeholder="Nombre completo" />
              <input name="telefono_cliente" required placeholder="Teléfono" />
              <button className="boton boton--tinta">Guardar y asociar</button>
            </form>
          )}
        </section>

        <form className="formulario formulario-pedido" onSubmit={guardarPedido}>
          <div className="paso-formulario campo--completo"><b>2</b><div><span>Datos del encargo</span><small>La lista de precios se consulta fuera del sistema</small></div></div>
          <Campo etiqueta="Fecha de entrega"><input name="fecha_entrega" type="date" required min={new Date().toISOString().slice(0, 10)} /></Campo>
          <Campo etiqueta="Descripción de prendas y trabajos" ancho="campo--completo"><textarea name="descripcion" required rows={4} placeholder="Ej. Ajustar mangas de chaqueta y realizar basta en pantalón…" /></Campo>
          <Campo etiqueta="Prioridad"><select name="prioridad" defaultValue="MEDIA">{PRIORIDADES.map((valor) => <option key={valor} value={valor}>{etiqueta(valor)}</option>)}</select></Campo>
          <Campo etiqueta="Complejidad"><select name="complejidad" defaultValue="MEDIA">{COMPLEJIDADES.map((valor) => <option key={valor} value={valor}>{etiqueta(valor)}</option>)}</select></Campo>
          <Campo etiqueta="Horas estimadas"><input name="tiempo_estimado_horas" type="number" min="0" step="0.5" defaultValue="2" required /></Campo>
          <Campo etiqueta="Valor base" ayuda="Monto en pesos, sin separadores."><input name="valor_base" type="number" min="0" step="1" required placeholder="30000" /></Campo>
          {rol === 'DUENO' && <><Campo etiqueta="Descuento"><input name="descuento" type="number" min="0" step="1" defaultValue="0" /></Campo><Campo etiqueta="Recargo"><input name="recargo" type="number" min="0" step="1" defaultValue="0" /></Campo></>}
          <div className="acciones-formulario campo--completo"><button type="button" className="boton boton--suave" onClick={cerrar}>Cancelar</button><button className="boton boton--primario" disabled={guardando || !seleccionado}>{guardando ? 'Registrando…' : 'Confirmar pedido'}</button></div>
        </form>
      </div>
    </Modal>
  )
}

