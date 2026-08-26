import { type FormEvent, useEffect, useState } from 'react'
import { api } from '../servicios_api/api'
import type { Trabajador } from '../modelos/tipos'
import { Campo, Cargando, EstadoVacio } from '../componentes/Comunes'
import { Icono } from '../componentes/Icono'
import { Modal } from '../componentes/Modal'

export function TrabajadoresPagina({ notificar }: { notificar: (texto: string) => void }) {
  const [trabajadores, setTrabajadores] = useState<Trabajador[]>([])
  const [cargando, setCargando] = useState(true)
  const [editando, setEditando] = useState<Trabajador | 'nuevo' | null>(null)
  const [error, setError] = useState('')

  const cargar = async () => {
    setCargando(true)
    try { setTrabajadores(await api.trabajadores()); setError('') }
    catch (e) { setError((e as Error).message) }
    finally { setCargando(false) }
  }
  useEffect(() => { void cargar() }, [])

  const guardar = async (evento: FormEvent<HTMLFormElement>) => {
    evento.preventDefault()
    const form = new FormData(evento.currentTarget)
    const datos = { nombre: String(form.get('nombre')), apellido: String(form.get('apellido')), telefono: String(form.get('telefono')) }
    try {
      if (editando === 'nuevo') await api.crearTrabajador(datos)
      else if (editando) await api.modificarTrabajador(editando.id_usuario, datos)
      setEditando(null); notificar(editando === 'nuevo' ? 'Trabajador incorporado al taller.' : 'Ficha del trabajador actualizada.'); await cargar()
    } catch (e) { setError((e as Error).message) }
  }

  const darBaja = async (trabajador: Trabajador) => {
    if (!window.confirm(`¿Dar de baja a ${trabajador.nombre}? Sus pedidos anteriores se conservarán.`)) return
    try { await api.darBajaTrabajador(trabajador.id_usuario); notificar('Trabajador marcado como inactivo.'); await cargar() }
    catch (e) { setError((e as Error).message) }
  }

  return (
    <div className="pagina">
      <section className="barra-herramientas barra-herramientas--derecha">
        <button className="boton boton--primario" onClick={() => setEditando('nuevo')}><Icono nombre="mas" /> Alta de trabajador</button>
      </section>
      {error && <p className="aviso aviso--error">{error}</p>}
      {cargando ? <Cargando /> : trabajadores.length === 0 ? (
        <EstadoVacio titulo="Aún no hay trabajadores" texto="Registra a la primera persona del equipo." />
      ) : (
        <section className="rejilla-trabajadores">
          {trabajadores.map((trabajador) => (
            <article className={`ficha-trabajador ${trabajador.estado_usuario === 'INACTIVO' ? 'ficha-trabajador--inactiva' : ''}`} key={trabajador.id_usuario}>
              <div className="ficha-trabajador__cabecera"><span className="avatar-grande">{trabajador.nombre.charAt(0)}{trabajador.apellido?.charAt(0)}</span><span className={`insignia ${trabajador.estado_usuario === 'ACTIVO' ? 'insignia--verde' : 'insignia--gris'}`}>{trabajador.estado_usuario.toLowerCase()}</span></div>
              <h2>{trabajador.nombre} {trabajador.apellido}</h2>
              <p>{trabajador.telefono || 'Sin teléfono registrado'}</p>
              <div className="ficha-trabajador__acciones"><button className="boton-texto" onClick={() => setEditando(trabajador)}><Icono nombre="editar" tamano={17} /> Editar</button>{trabajador.estado_usuario === 'ACTIVO' && <button className="boton-texto boton-texto--peligro" onClick={() => darBaja(trabajador)}>Dar de baja</button>}</div>
            </article>
          ))}
        </section>
      )}
      {editando && (
        <Modal titulo={editando === 'nuevo' ? 'Alta de trabajador' : 'Modificar trabajador'} subtitulo="La baja conserva todas sus asignaciones históricas." cerrar={() => setEditando(null)}>
          <form className="formulario" onSubmit={guardar}>
            <Campo etiqueta="Nombre"><input name="nombre" required defaultValue={editando === 'nuevo' ? '' : editando.nombre} autoFocus /></Campo>
            <Campo etiqueta="Apellido"><input name="apellido" defaultValue={editando === 'nuevo' ? '' : editando.apellido ?? ''} /></Campo>
            <Campo etiqueta="Teléfono" ancho="campo--completo"><input name="telefono" defaultValue={editando === 'nuevo' ? '' : editando.telefono ?? ''} placeholder="+56 9 1234 5678" /></Campo>
            <div className="acciones-formulario"><button type="button" className="boton boton--suave" onClick={() => setEditando(null)}>Cancelar</button><button className="boton boton--primario">Guardar ficha</button></div>
          </form>
        </Modal>
      )}
    </div>
  )
}
