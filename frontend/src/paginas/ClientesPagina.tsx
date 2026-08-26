import { type FormEvent, useEffect, useState } from 'react'
import { api } from '../servicios_api/api'
import type { Cliente, RolOperativo } from '../modelos/tipos'
import { Campo, Cargando, EstadoVacio } from '../componentes/Comunes'
import { Icono } from '../componentes/Icono'
import { Modal } from '../componentes/Modal'

export function ClientesPagina({
  rol,
  notificar,
}: {
  rol: RolOperativo
  notificar: (texto: string) => void
}) {
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [buscar, setBuscar] = useState('')
  const [cargando, setCargando] = useState(true)
  // null = cerrado, 'nuevo' = alta, un cliente = edición.
  const [formulario, setFormulario] = useState<Cliente | 'nuevo' | null>(null)
  const [guardando, setGuardando] = useState(false)
  const [borrando, setBorrando] = useState(0)
  const [error, setError] = useState('')

  const cargar = async (termino = '') => {
    setCargando(true)
    try { setClientes(await api.clientes(termino)); setError('') }
    catch (e) { setError((e as Error).message) }
    finally { setCargando(false) }
  }

  useEffect(() => { void cargar() }, [])

  const buscarClientes = (evento: FormEvent) => {
    evento.preventDefault()
    void cargar(buscar)
  }

  const editando = formulario !== null && formulario !== 'nuevo' ? formulario : null

  const guardar = async (evento: FormEvent<HTMLFormElement>) => {
    evento.preventDefault()
    const datos = new FormData(evento.currentTarget)
    const cliente = {
      nombre: String(datos.get('nombre')),
      telefono: String(datos.get('telefono')),
    }
    setGuardando(true)
    setError('')
    try {
      if (editando) {
        await api.modificarCliente(editando.id_cliente, cliente)
        notificar('Cliente actualizado.')
      } else {
        await api.crearCliente(cliente)
        notificar('Cliente registrado en la libreta.')
      }
      setFormulario(null)
      await cargar(buscar)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setGuardando(false)
    }
  }

  const eliminar = async (cliente: Cliente) => {
    if (!window.confirm(`¿Eliminar a ${cliente.nombre} de la libreta?\n\nEsta acción no se puede deshacer.`)) return
    setBorrando(cliente.id_cliente)
    setError('')
    try {
      await api.eliminarCliente(cliente.id_cliente)
      notificar(`${cliente.nombre} salió de la libreta.`)
      await cargar(buscar)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBorrando(0)
    }
  }

  const puedeEliminar = rol === 'DUENO'

  return (
    <div className="pagina">
      <section className="barra-herramientas">
        <form className="buscador" onSubmit={buscarClientes}>
          <Icono nombre="buscar" />
          <input value={buscar} onChange={(e) => setBuscar(e.target.value)} placeholder="Buscar por nombre o teléfono" aria-label="Buscar clientes" />
          <button>Buscar</button>
        </form>
        <button className="boton boton--primario" onClick={() => setFormulario('nuevo')}><Icono nombre="mas" /> Registrar cliente</button>
      </section>

      {error && <p className="aviso aviso--error">{error}</p>}
      {cargando ? <Cargando /> : clientes.length === 0 ? (
        <EstadoVacio titulo="No encontramos clientes" texto="Prueba otra búsqueda o registra una nueva persona." accion={<button className="boton boton--primario" onClick={() => setFormulario('nuevo')}>Registrar cliente</button>} />
      ) : (
        <section className="panel papel-costura tabla-contenedor">
          <header className="panel__cabecera"><div><span className="sobretitulo">Libreta de medidas</span><h2>{clientes.length} clientes</h2></div></header>
          <table className="tabla">
            <thead><tr><th>Cliente</th><th>Teléfono</th><th /></tr></thead>
            <tbody>{clientes.map((cliente) => (
              <tr key={cliente.id_cliente}>
                <td><span className="avatar-letra">{cliente.nombre.charAt(0)}</span><strong>{cliente.nombre}</strong></td>
                <td><a href={`tel:${cliente.telefono}`}>{cliente.telefono}</a></td>
                <td>
                  <div className="acciones-fila">
                    <button className="boton-icono" onClick={() => setFormulario(cliente)} aria-label={`Modificar a ${cliente.nombre}`} title="Modificar">
                      <Icono nombre="editar" />
                    </button>
                    {puedeEliminar && (
                      <button
                        className="boton-icono boton-icono--peligro"
                        onClick={() => void eliminar(cliente)}
                        disabled={borrando === cliente.id_cliente}
                        aria-label={`Eliminar a ${cliente.nombre}`}
                        title="Eliminar"
                      >
                        <Icono nombre="eliminar" />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}</tbody>
          </table>
        </section>
      )}

      {formulario && (
        <Modal
          titulo={editando ? 'Modificar cliente' : 'Registrar cliente'}
          subtitulo="Datos de contacto para asociar sus pedidos."
          cerrar={() => setFormulario(null)}
        >
          <form className="formulario" onSubmit={guardar}>
            <Campo etiqueta="Nombre completo" ancho="campo--completo">
              <input name="nombre" required maxLength={150} autoFocus defaultValue={editando?.nombre ?? ''} placeholder="Ej. Amalia Fuentes" />
            </Campo>
            <Campo etiqueta="Teléfono" ayuda="Puede incluir +56, espacios y guiones." ancho="campo--completo">
              <input name="telefono" required maxLength={30} defaultValue={editando?.telefono ?? ''} placeholder="+56 9 1234 5678" />
            </Campo>
            <div className="acciones-formulario">
              <button type="button" className="boton boton--suave" onClick={() => setFormulario(null)}>Cancelar</button>
              <button className="boton boton--primario" disabled={guardando}>
                {guardando ? 'Guardando…' : editando ? 'Guardar cambios' : 'Guardar cliente'}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}
